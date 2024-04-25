#!/usr/bin/env python3
"""
Downloads the alpaca cleaned dataset and reports some stats about it.
https://huggingface.co/datasets/yahma/alpaca-cleaned?row=16
https://github.com/gururise/AlpacaDataCleaned
"""

import os
import json
import sys
from datasets import load_dataset

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
EXPERIMENTS_DIR = os.path.realpath(os.path.join(SCRIPT_DIR, "../.."))
sys.path.append(EXPERIMENTS_DIR)
from config import TaskTimer  # noqa


DATASET_ID = "yahma/alpaca-cleaned"


def main():
    # download dataset to hugging face disk cache
    with TaskTimer("load dataset"):
        dataset = load_dataset(DATASET_ID)
    describe_dataset(dataset)


def describe_dataset(dataset):
    print("\ndataset splits: ", dataset.keys())
    print("dataset columns:", dataset.column_names)

    total_samples = 0
    for split in dataset:
        print(f"\nsplit: {split} has {len(dataset[split]):,} entires")
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


if __name__ == "__main__":
    main()
