#!/usr/bin/env python3
################################################################################
# https://huggingface.co/meta-llama/Llama-2-7b-chat-hf
#
# https://medium.com/@nimritakoul01/chat-with-llama-2-7b-from-huggingface-llama-2-7b-chat-hf-d0f5735abfcf
# https://medium.com/@ankit941208/generating-summaries-for-large-documents-with-llama2-using-hugging-face-and-langchain-f7de567339d2
################################################################################

import torch
import os
import time
import json
from transformers import (
    AutoTokenizer,
    AutoModelForCausalLM,
    BitsAndBytesConfig,
    pipeline,
)
from langchain_community.llms import HuggingFacePipeline
from langchain.prompts import PromptTemplate
from typing import Dict

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATASETS_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, os.pardir, "datasets"))
PEER_READ_DIR = os.path.join(DATASETS_DIR, "PeerRead")


MODEL_ID = "meta-llama/Llama-2-7b-chat-hf"

def main():
    #interactive()
    play_datasets()


def play_datasets():
    cur_dir = os.path.join(PEER_READ_DIR, "data/iclr_2017/train/parsed_pdfs/")

    fname = os.path.join(cur_dir, "304.pdf.json")
    assert os.path.exists(fname)
    print(f"reading {fname}", flush=True)
    with open(fname, "r") as f:
        data = json.load(f)
    print("done reading", flush=True)

    paper_text = pdf_json_to_text(data)
    print(paper_text)

    breakpoint()
    print()

    #model, tokenizer = get_model()



def pdf_json_to_text(data: Dict):
    """Convert PeerRead json object to a single string."""
    combined = ""
    for section in data["metadata"]["sections"]:
        heading, text = section["heading"], section["text"]
        combined += f"\n{heading}\n{text}"

    return combined.strip()


def interactive():
    """Play with LLama by chatting through stdin."""
    model, tokenizer = get_model()

    # https://python.langchain.com/docs/integrations/llms/huggingface_pipelines
    print("creating pipline...")
    pipe = pipeline(
        "text-generation", model=model, tokenizer=tokenizer, max_new_tokens=1000
    )
    hf = HuggingFacePipeline(pipeline=pipe)

    prompt_template = "[INST]{prompt}[/INST]"
    prompt = PromptTemplate.from_template(prompt_template)
    chain = prompt | hf

    while True:
        prompt = input("\nYou: ")
        response = chain.invoke({"prompt": prompt})
        # input_ids = tokenizer.encode(prompt, return_tensors="pt")
        # input_ids = input_ids
        # output = model.generate(
        #     input_ids, max_length=256, num_beams=4, no_repeat_ngram_size=2
        # )
        # response = tokenizer.decode(output[0], skip_special_tokens=True)
        print(f"\nLLama: {response}")


def get_model(verbose: bool = True):
    start_time = time.perf_counter()
    if verbose:
        print("loading model...", flush=True)

    # the model will be automatically downloaded and cached (e.g. in ~/.cache/huggingface/)
    #  cache dir / running offline info: https://huggingface.co/docs/datasets/en/cache
    tokenizer = AutoTokenizer.from_pretrained(MODEL_ID)
    tokenizer.use_default_system_prompt = False

    # load quantized model (load_in_8_bit is critical to fit in memory)
    quantization_config = BitsAndBytesConfig(llm_int8_threshold=4.0, load_in_8_bit=True)
    model = AutoModelForCausalLM.from_pretrained(
        MODEL_ID,
        quantization_config=quantization_config,
        device_map="auto",
    )
    end_time = time.perf_counter()
    if verbose:
        print(f"model loaded in {(end_time - start_time):.2f} secs!")
    return model, tokenizer


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
