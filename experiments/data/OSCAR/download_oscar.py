#!/usr/bin/env python3
"""
This script demonstrates how to load the Dutch portion of the OSCAR dataset from HuggingFace.
This was exploratory and ultimately not used in the final project.
"""

import os
import argparse
import json
from datasets import load_dataset
import time
from time import perf_counter

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))


# https://huggingface.co/datasets/oscar-corpus/OSCAR-2301
# https://huggingface.co/docs/datasets/en/cache#cache-directory
def main():
    dataset = load_dataset(
        "oscar-corpus/OSCAR-2301", "nl", trust_remote_code=True, streaming=True
    )

    # just "train"
    print("dataset splits:")
    for split in dataset:
        print(split)

    for item in dataset["train"]:
        break

    with open("example.json", "w") as f:
        json.dump(item, f, indent=2)
    print("\nwrote example.json")

    # now let's get serious and download it
    start_time = perf_counter()
    print("loading dataset!", flush=True)
    dataset = load_dataset("oscar-corpus/OSCAR-2301", "nl", trust_remote_code=True)
    end_time = perf_counter()
    print(f"\ntook {(end_time-start_time)/60:.2f} minutes to load dataset!")


if __name__ == "__main__":
    main()
