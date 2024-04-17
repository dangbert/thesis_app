#!/usr/bin/env python3

import os
import torch
from transformers import (
    AutoTokenizer,
    AutoModelForCausalLM,
    BitsAndBytesConfig,
    pipeline,
)

# from transformers.models.gemma
from config import get_device, TaskTimer

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

MODEL_ID = "google/gemma-2b-it"


def main():
    device = get_device()
    print(f"using device {device}")

    model, tokenizer = get_model()

    # simple generation
    input_text = "Write me a poem in Dutch."
    input_ids = tokenizer(input_text, return_tensors="pt").to(device)
    with TaskTimer("single generation"):
        outputs = model.generate(**input_ids, max_new_tokens=400)
        print(tokenizer.decode(outputs[0]), "\n")

    max_new_tokens = 400
    pipe = pipeline(
        "text-generation",
        model=model,
        tokenizer=tokenizer,
        max_new_tokens=max_new_tokens,
        # tokenizer_kwargs={"add_bos_token": True}
    )
    batch = [
        f"write me a poem in {lang}"
        for lang in ["Dutch", "French", "German", "Spanish"]
    ]

    batch.append(
        "tell me a short story about a kid at the beach for the first time in Europe"
    )
    # reference: https://github.com/huggingface/transformers/blob/main/src/transformers/models/gemma/tokenization_gemma.py
    batch = ["<bos>" + t for t in batch]

    BATCH_SIZE = len(batch)
    with TaskTimer(f"batch generation (n={len(batch)})"):
        responses = pipe(batch, return_full_text=False, batch_size=BATCH_SIZE)
        # outputs = model.generate(**input_ids, max_new_tokens=max_new_tokens)

    for i, res in enumerate(responses):
        res = res[0]["generated_text"]
        print(f"\n--- response {i}: ---")
        print(res, "\n")


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
