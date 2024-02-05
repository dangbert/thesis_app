#!/usr/bin/env python3
# https://huggingface.co/meta-llama/Llama-2-7b-chat-hf

import os
import argparse
import sys
from transformers import pipeline, AutoTokenizer, AutoModelForCausalLM

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))


def main():
    # parser = argparse.ArgumentParser()
    # parser.add_argument(
    #     "out_folder",
    #     type=str,
    #     help="path of folder to output markdown and csv files (e.g. './output')",
    # )
    # ops = 0  # num operations performed
    # args = parser.parse_args()

    pipe = pipeline("text-generation", model="meta-llama/Llama-2-7b-chat-hf")
    tokenizer = AutoTokenizer.from_pretrained("meta-llama/Llama-2-7b-chat-hf")
    model = AutoModelForCausalLM.from_pretrained("meta-llama/Llama-2-7b-chat-hf")


if __name__ == "__main__":
    main()
