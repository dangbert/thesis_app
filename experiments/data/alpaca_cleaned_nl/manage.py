#!/usr/bin/env python3
"""
Utilities for translating the alpaca-cleaned dataset, creating aplaca-cleaned-nl.
https://huggingface.co/datasets/yahma/alpaca-cleaned
https://github.com/gururise/AlpacaDataCleaned
https://huggingface.co/datasets/dangbert/alpaca-cleaned-nl
"""

import argparse
import os
import json
import sys
import glob
from datasets import load_dataset, concatenate_datasets, Dataset, DatasetDict
import numpy as np
import deepl
from typing import Union

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
EXPERIMENTS_DIR = os.path.realpath(os.path.join(SCRIPT_DIR, "../.."))
sys.path.append(EXPERIMENTS_DIR)
import data.alpaca_cleaned_nl.translate_utils as tutils  # noqa: E402
import config  # noqa: E402
from config import TaskTimer  # noqa: E402


ORIG_DATASET_ID = "yahma/alpaca-cleaned"
COL_NAMES = ["output", "input", "instruction"]  # columns to translate

TRANSLATED_PATH = os.path.join(
    SCRIPT_DIR, "translated_dataset.jsonl"
)  # where to write/read translated dataset
# make relative path
TRANSLATED_PATH = os.path.relpath(TRANSLATED_PATH, start=os.getcwd())

TRANSLATED_DATASET_ID = "dangbert/alpaca-cleaned-nl"  # where to upload on hugging face

logger = config.get_logger(__name__, level="INFO")


def main():
    # parser which shows default values in help
    parser = argparse.ArgumentParser(
        description="Utils for downloading the original alpaca-cleaned dataset, translating sections of it, and re-uploading to huggingface.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--translate",
        "-t",
        action="store_true",
        help="Translate the dataset to Dutch, writing the result to '{TRANSLATED_PATH}'.  Resume from where it left off if the file already exists.",
    )
    parser.add_argument(
        "--max-samples",
        "-m",
        type=int,
        default=100,
        help="max number of samples to translate (only applicable alongside --translate)",
    )
    parser.add_argument(
        "--dump",
        type=str,
        nargs=3,
        metavar=("filename", "start_index", "stop_index"),
        help="Dump source dataset entries to a docx or text file with the specified filename, starting from the specified index and ending before the stop_index (exclusive).",
    )

    parser.add_argument(
        "--deserialize",
        type=str,
        nargs=1,
        metavar=("folder"),
        help="Folder of docx files to convert to jsonl files (e.g. downloaded from DeepL after translation).",
    )
    parser.add_argument(
        "--merge",
        nargs=2,
        type=str,
        metavar=("folder", "output_file"),
        help="Folder of jsonl files to merge into a single dataset (jsonl) file",
    )
    parser.add_argument(
        "--describe",
        metavar="filename",
        type=str,
        help="Describe a given .jsonl dataset (subset) by reporting some stats",
    )
    parser.add_argument(
        "--download",
        nargs=2,
        metavar=("dataset_id", "filename"),
        type=str,
        help=f"Download alpaca-cleaned or alpaca-cleaned-nl to desired path, and describe it. E.g. `--download {ORIG_DATASET_ID} alpaca-cleaned.nl` OR `--download {TRANSLATED_DATASET_ID} {TRANSLATED_PATH}`",
    )
    parser.add_argument(
        "--upload",
        "-u",
        type=str,
        help="Upload provided .jsonl file to hugging face hub, replacing the existing dataset '{TRANSLATED_DATASET_ID}'",
    )

    args = parser.parse_args()

    if args.dump:
        filename, start_index, stop_index = args.dump
        start_index, stop_index = int(start_index), int(stop_index)
        # assert not os.path.exists(filename), f"refusing to overwrite '{filename}'"
        if os.path.isdir(filename):
            filename = f"{filename}/orig_{start_index}_to_{stop_index}.docx"
        sdataset, orig_indices = get_shuffled_dataset()
        sdataset = sdataset.add_column("orig_index", orig_indices)

        sdataset = sdataset.select(range(start_index, stop_index))
        tutils.serialize_dataset(sdataset, filename, assert_sanity=False)
        return

    if args.deserialize:
        dir = args.deserialize[0]
        assert os.path.isdir(dir)
        fnames = glob.glob(f"{dir}/*.docx")
        logger.info(f"found {len(fnames)} docx files in '{dir}' to convert to jsonl")
        for fname in fnames:
            outname = fname.replace(".docx", ".jsonl")
            if os.path.exists(outname):
                logger.info(f"skipping already deserialized file: '{fname}'")
                continue
            logger.info(f"converting '{fname}' -> '{outname}'")
            cur_dataset = tutils.deserialize_dataset(fname)
            cur_dataset.to_json(outname)
        return

    if args.translate:
        sdataset, orig_indices = get_shuffled_dataset()
        sdataset = sdataset.add_column("orig_index", orig_indices)

        _ = estimate_budget()
        translate_dataset(sdataset, TRANSLATED_PATH, max_samples=args.max_samples)
        if not args.upload:
            return

    if args.upload:
        fname = args.upload
        assert os.path.isfile(fname)
        assert fname.lower().endswith(".jsonl") or fname.lower().endswith(".json")
        dataset, _ = load_local_dataset(fname)
        logger.info(
            f"uploading translated dataset to hugging face hub '{TRANSLATED_DATASET_ID}'"
        )
        # https://huggingface.co/docs/datasets/upload_dataset
        with TaskTimer("push to hub"):
            dataset.push_to_hub(TRANSLATED_DATASET_ID)
        return

    if args.merge:
        dir, output_file = args.merge
        assert not os.path.exists(output_file), f"refusing to overwrite '{output_file}'"
        fnames = glob.glob(f"{dir}/*.jsonl")
        logger.info(f"found {len(fnames)} jsonl files in '{dir}' to merge")
        if len(fnames) == 0:
            return

        seen_ids = set()

        def filter_rows(item):
            # prevent possible duplicates when concatenating datasets by removing rows where orig_index has already been seen
            nonlocal seen_ids
            return item["orig_index"] not in seen_ids  # True if row should be kept

        combined = None
        for fname in fnames:
            cur_dataset, _ = load_local_dataset(fname)
            if combined is None:
                combined = cur_dataset
                continue
            seen_ids = set(combined["orig_index"])
            prev_len = len(cur_dataset)
            cur_dataset = cur_dataset.filter(filter_rows)
            removed = prev_len - len(cur_dataset)
            if removed > 0:
                logger.info(f"skipping {removed} possible duplicates from '{fname}'")
            combined = concatenate_datasets([combined, cur_dataset])

        combined.to_json(output_file)
        logger.info(
            f"wrote merged dataset (from {len(fnames)} files) to '{output_file}' ({len(combined)} final rows)"
        )
        return

    if args.download:
        dataset_id, fname = args.download
        assert not os.path.exists(fname), f"refusing to overwrite '{fname}'"
        if dataset_id not in [ORIG_DATASET_ID, TRANSLATED_DATASET_ID]:
            logger.warning(f"unknown dataset_id: '{dataset_id}', continuing anyways...")
        assert fname.endswith(".json") or fname.endswith(".jsonl")
        dataset = get_dataset(dataset_id)
        Dataset.from_dict(dataset).to_json(fname)
        logger.info(f"downloaded dataset '{dataset_id}' to '{fname}'")
        print(
            f"\nto view info about this dataset, you can always run ./{os.path.basename(__file__)} --describe '{fname}'"
        )
        args.describe = fname

    if args.describe:
        fname = args.describe
        assert os.path.isfile(fname)
        assert fname.lower().endswith(".jsonl") or fname.lower().endswith(".json")
        print("\ndescribing dataset: ", fname)
        dataset, _ = load_local_dataset(fname)
        dataset = get_dataset(TRANSLATED_DATASET_ID)
        describe_dataset(dataset)
        return

    print("no action specified, printing help...\n")
    parser.print_help()
    exit(1)


def describe_dataset(dataset):
    print("\ndataset splits: ", dataset.keys())
    print("dataset columns:", dataset.column_names)

    total_samples = 0
    for split in dataset:
        print(f"\nsplit: {split} has {len(dataset[split]):,} entries")
        total_samples += len(dataset[split])

    for item in dataset["train"]:
        break

    print("\nexample item:\n", item)
    with open("example.json", "w") as f:
        json.dump(item, f, indent=2)
    print("\nwrote example.json")

    # count total chars in dataset
    chars = 0
    for split in dataset:
        col_names = dataset[split].column_names
        for item in dataset[split]:
            for col_name in col_names:
                if isinstance(item[col_name], str):
                    chars += len(item[col_name])
    print(f"\ntotal chars in dataset: {chars:,}")
    print(f"\naverage chars per sample: {(chars / total_samples):.1f}")


def get_dataset(dataset_id: str):
    """Returns the full original dataset."""
    with TaskTimer(f"load dataset: {dataset_id}"):
        return load_dataset(dataset_id)


def get_shuffled_dataset():
    """Shuffles the train split of the dataset and return it. Uses a constant seed so the returned dataset is always the same."""
    dataset = get_dataset()
    # calculate how many samples can be translated with a budget of 500_000 chars
    np.random.seed(42)
    indices = np.random.permutation(len(dataset["train"]))
    sdataset = dataset["train"].select(indices)
    return sdataset, indices


def estimate_budget(translate_budget: int = 500_000) -> int:
    """Estimate number of samples that can be translated with a given budget."""
    sdataset, orig_indices = get_shuffled_dataset()
    print(f"{orig_indices[:5]=}")
    print(sdataset.column_names)

    count = 0
    budget = translate_budget
    for item in sdataset:
        if budget <= 0:
            count -= 1 if budget < 0 else 0
            break
        for col_name in COL_NAMES:
            budget -= len(item[col_name])
        count += 1

    print(f"translate_budget={translate_budget:,} allows for {count:,} samples!\n")
    return count


class DUMMYResult:
    text: str = "Hallo, wereld!"
    detected_source_lang: str = "EN"


def load_local_dataset(disk_path: str):
    """Reload dataset from local cache of previous translations."""
    assert os.path.exists(disk_path)
    tdataset: DatasetDict = load_dataset("json", data_files=disk_path, split="train")
    tdataset_dict = {c: tdataset[c] for c in tdataset.column_names}
    logger.info(f"reloaded dataset from '{disk_path}' (with {len(tdataset)} samples)")
    return tdataset, tdataset_dict


def translate_dataset(dataset, disk_path: str, max_samples: int):
    """
    Translates the provided dataset, writing the results to disk.
    Rerunning this function will automatically resume from where it left off.

    max_samples: maximum number of samples to translate before quitting (one sample has len(COL_NAMES) columns
    """
    assert disk_path.endswith(".jsonl") or disk_path.endswith(".json")

    tdataset_dict: dict = {c: [] for c in COL_NAMES}  # translated dataset
    extra_cols = ["orig_index", "detected_source_lang"]
    for c in extra_cols:
        tdataset_dict[c] = []
    if os.path.exists(disk_path):
        tdataset, tdataset_dict = load_local_dataset(disk_path)
    assert tdataset_dict.keys() == set(COL_NAMES + extra_cols)

    def flush_translated_dataset(tdataset_dict):
        # note: .to_json(disk_path, indent=2) makes it more readable but leads to problems reloading later :(
        Dataset.from_dict(tdataset_dict).to_json(disk_path)

    translator = deepl.Translator(config.get_settings().deepl_api_key)

    # resume from where we left off (if any)
    start_index = len(tdataset_dict[COL_NAMES[0]])
    logger.info(f"starting translation from row {start_index} in dataset")
    for i in range(start_index, len(dataset)):
        if len(tdataset_dict[COL_NAMES[0]]) >= max_samples:
            logger.info(f"reached max_samples={max_samples}, stopping")
            break

        sample = dataset[i]
        # skip translating empty fields
        results = {c: sample[c] for c in COL_NAMES if sample[c].strip() == ""}
        batch = [sample[c] for c in COL_NAMES if c not in results]

        logger.debug(f"translating batch of {len(batch)} entries")
        try:
            res = translator.translate_text(batch, target_lang="NL")
            # res = [DUMMYResult() for _ in batch] # for testing
        except Exception as e:
            logger.error(f"failed to translate batch, stopping early: {e}")
            break

        # populate results dict with translations (considering some columns may have been skipped)
        res_idx = 0
        for c in COL_NAMES:
            if c not in results:
                results[c] = res[res_idx].text
                res_idx += 1
            tdataset_dict[c].append(results[c])
        tdataset_dict["orig_index"].append(sample["orig_index"])
        source_langs = sorted(list(set(r.detected_source_lang for r in res)))
        tdataset_dict["detected_source_lang"].append(",".join(source_langs))

        if i % 10 == 0:
            flush_translated_dataset(tdataset_dict)
            logger.debug(f"flushed dataset to '{disk_path}' (row {i})")

    flush_translated_dataset(tdataset_dict)
    logger.info("final flush complete!")


if __name__ == "__main__":
    main()
