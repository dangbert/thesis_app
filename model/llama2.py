#!/usr/bin/env python3
################################################################################
# https://huggingface.co/meta-llama/Llama-2-7b-chat-hf
#
# https://medium.com/@nimritakoul01/chat-with-llama-2-7b-from-huggingface-llama-2-7b-chat-hf-d0f5735abfcf
#
# TODO: play with connecting langchain https://medium.com/@ankit941208/generating-summaries-for-large-documents-with-llama2-using-hugging-face-and-langchain-f7de567339d2
################################################################################

import torch
import os
from transformers import (
    AutoTokenizer,
    AutoModelForCausalLM,
    BitsAndBytesConfig,
)
from huggingface_hub import login

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))


def main():
    # parser = argparse.ArgumentParser()
    # parser.add_argument(
    #     "out_folder",
    #     type=str,
    #     help="path of folder to output markdown and csv files (e.g. './output')",
    # )
    # args = parser.parse_args()

    device = get_device()
    print(f"using device: '{device}'")

    # ensure authenticated with hugging face hub (for downloading llama2 model)
    # login()

    # the model will be automatically downloaded and cached (e.g. in ~/.cache/huggingface/)
    #  for info about cache dir and running offline see:
    #  https://huggingface.co/docs/datasets/en/cache
    MODEL_ID = "meta-llama/Llama-2-7b-chat-hf"
    # pipe = pipeline("text-generation", model=MODEL_ID)
    tokenizer = AutoTokenizer.from_pretrained(MODEL_ID)
    tokenizer.use_default_system_prompt = False

    # load quantized model (load_in_8_bit is critical to fit in memory)
    quantization_config = BitsAndBytesConfig(llm_int8_threshold=4.0, load_in_8_bit=True)
    print("loading model", flush=True)
    model = AutoModelForCausalLM.from_pretrained(
        MODEL_ID,
        quantization_config=quantization_config,
        device_map="auto",
    )
    print("done loading model!")
    # model.to(device)

    while True:
        prompt = input("\nYou: ")
        input_ids = tokenizer.encode(prompt, return_tensors="pt")
        input_ids = input_ids  # .to(device)
        output = model.generate(
            input_ids, max_length=256, num_beams=4, no_repeat_ngram_size=2
        )
        response = tokenizer.decode(output[0], skip_special_tokens=True)
        print(f"\nLLama: {response}")


def get_device() -> str:
    """Returns the device for PyTorch to use."""
    device = "cpu"
    if torch.cuda.is_available():
        device = "cuda"
    # mac MPS support: https://pytorch.org/docs/stable/notes/mps.html
    elif torch.backends.mps.is_available():
        if not torch.backends.mps.is_built():
            print(
                "MPS not available because the current PyTorch install was not built with MPS enabled."
            )
        else:
            device = "mps"
    return device


if __name__ == "__main__":
    main()
