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
    pipeline,
)
from langchain.llms import HuggingFacePipeline
from langchain.prompts import PromptTemplate

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))


def main():
    # the model will be automatically downloaded and cached (e.g. in ~/.cache/huggingface/)
    #  cache dir / running offline info: https://huggingface.co/docs/datasets/en/cache
    MODEL_ID = "meta-llama/Llama-2-7b-chat-hf"
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
