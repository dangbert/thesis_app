#!/usr/bin/env python3
"""
Downloads the alpaca cleaned dataset and reports some stats about it.
https://huggingface.co/datasets/yahma/alpaca-cleaned?row=16
https://github.com/gururise/AlpacaDataCleaned
"""

import argparse
import os
import json
import sys
from datasets import load_dataset, Dataset, DatasetDict
import numpy as np
import deepl
from typing import Union

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
EXPERIMENTS_DIR = os.path.realpath(os.path.join(SCRIPT_DIR, "../.."))
sys.path.append(EXPERIMENTS_DIR)
import data.alpaca_cleaned_nl.translate_utils as tutils  # noqa: E402
import config  # noqa: E402
from config import TaskTimer  # noqa: E402


DATASET_ID = "yahma/alpaca-cleaned"
COL_NAMES = ["output", "input", "instruction"]  # columns to translate

TRANSLATED_PATH = os.path.join(
    SCRIPT_DIR, "translated_dataset.jsonl"
)  # where to write/read translated dataset
TRANSLATED_DATASET_ID = "dangbert/alpaca-cleaned-nl"  # where to upload on hugging face

logger = config.get_logger(__name__, level="INFO")


def main():
    # parser which shows default values in help
    parser = argparse.ArgumentParser(
        description="Download the alpaca cleaned dataset and report some stats about it.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--dump-docx",
        type=str,
        nargs=3,
        metavar=("filename", "start_index", "count"),
        help="Dump source dataset entries to a docx file with the specified filename, starting from the specified index and count",
    )

    args = parser.parse_args()

    if args.dump_docx:
        filename, start_index, count = args.dump_docx
        start_index, count = int(start_index), int(count)
        assert not os.path.exists(filename), f"refusing to overwrite '{filename}'"
        sdataset, orig_indices = get_shuffled_dataset()
        sdataset = sdataset.add_column("orig_index", orig_indices)

        # TOOD: use start_index and count
        tutils.serialize_dataset(sdataset, filename, assert_sanity=False)
        return

    if args.translate:
        sdataset, orig_indices = get_shuffled_dataset()
        sdataset = sdataset.add_column("orig_index", orig_indices)

        _ = estimate_budget()
        translate_dataset(sdataset, TRANSLATED_PATH, max_samples=args.max_samples)
        if not args.upload:
            return

    if args.upload:
        tdataset, tdataset_dict = load_local_dataset(TRANSLATED_PATH)
        logger.info(
            f"uploading translated dataset to hugging face hub '{TRANSLATED_DATASET_ID}'"
        )
        # https://huggingface.co/docs/datasets/upload_dataset
        with TaskTimer("push to hub"):
            tdataset.push_to_hub(TRANSLATED_DATASET_ID)
        return

    # download dataset to hugging face disk cache
    dataset = get_dataset()
    describe_dataset(dataset)


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
                chars += len(item[col_name])
    print(f"\ntotal chars in dataset: {chars:,}")
    print(f"\naverage chars per sample: {(chars / total_samples):.1f}")


def get_dataset():
    """Returns the full original dataset."""
    with TaskTimer("load dataset"):
        return load_dataset(DATASET_ID)


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
    logger.info(
        f"reloaded cached dataset from '{disk_path}' (with {len(tdataset)} samples)"
    )
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
