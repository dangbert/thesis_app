"""PeerRead dataset utils."""

import os
import json
from datasets import Dataset, DatasetDict
import glob
from collections import defaultdict
from typing import Dict

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATASETS_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, os.pardir, "datasets"))
PR_DIR = os.path.join(DATASETS_DIR, "PeerRead")


def pdf_json_to_text(data: Dict) -> str:
    """Convert PeerRead json object to a single string."""
    combined = ""
    for section in data["metadata"]["sections"]:
        heading, text = section["heading"], section["text"]
        combined += f"\n{heading}\n{text}"

    return combined.strip()


def get_path_dataset(data_dir: str) -> DatasetDict:
    """Get dataset of just filenames (relative to PR_DIR).
    params:
        data_dir: directory relative to PR_DIR (e.g. "data/iclr_2017")
    """
    if not os.path.isabs(data_dir):
        data_dir = os.path.join(PR_DIR, data_dir)
    assert os.path.isdir(data_dir)

    data_dict = defaultdict(dict)
    for split in {"dev", "test", "train"}:
        pattern = os.path.join(data_dir, split, "parsed_pdfs/*.json")
        fnames = glob.glob(pattern)
        for fname in fnames:
            assert os.path.exists(fname)
            if "path" not in data_dict[split]:
                data_dict[split]["path"] = []
            data_dict[split]["path"].append(os.path.relpath(fname, PR_DIR))

    dataset_dict = DatasetDict(
        {split: Dataset.from_dict(data_dict[split]) for split in data_dict.keys()}
    )
    return dataset_dict


def add_contents_feature(sample: Dict):
    full_path = os.path.join(PR_DIR, sample["path"])
    assert os.path.isfile(full_path)
    with open(full_path, "r") as f:
        paper_json = json.load(f)
    sample["contents_str"] = pdf_json_to_text(paper_json)
    return sample
