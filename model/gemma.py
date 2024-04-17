#!/usr/bin/env python3

import os
import torch
from transformers import (
    AutoTokenizer,
    AutoModelForCausalLM,
    BitsAndBytesConfig,
)
from config import get_device, TaskTimer

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

MODEL_ID = "google/gemma-2b-it"


def main():
    device = get_device()
    print(f"using device {device}")

    model, tokenizer = get_model()

    input_text = "Write me a poem in Dutch."
    input_ids = tokenizer(input_text, return_tensors="pt").to(device)

    with TaskTimer("generation"):
        outputs = model.generate(**input_ids, max_new_tokens=400)
    print(tokenizer.decode(outputs[0]))


def get_model():
    # load quantized model (load_in_8_bit is critical to fit in memory)
    quantization_config = BitsAndBytesConfig(llm_int8_threshold=4.0, load_in_8_bit=True)
    with TaskTimer("model load"):
        tokenizer = AutoTokenizer.from_pretrained("google/gemma-2b-it")
        model = AutoModelForCausalLM.from_pretrained(
            MODEL_ID,
            quantization_config=quantization_config,
            torch_dtype=torch.bfloat16,
            device_map="auto",
        )
        return model, tokenizer


if __name__ == "__main__":
    main()
