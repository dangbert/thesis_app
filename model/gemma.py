#!/usr/bin/env python3
################################################################################
# https://huggingface.co/google/gemma-2b-it
# code: https://github.com/huggingface/transformers/tree/main/src/transformers/models/gemma
# format of turns etc: https://ai.google.dev/gemma/docs/formatting
# https://medium.com/@coldstart_coder/getting-started-with-googles-gemma-llm-using-huggingface-libraries-a0d826c552ae
################################################################################

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
    max_new_tokens = 400
    print(f"using device {device}")
    model, tokenizer = get_model()

    ### simple generation example
    input_text = "Write me a poem in Dutch."
    input_ids = tokenizer(input_text, return_tensors="pt").to(device)
    with TaskTimer("single generation"):
        outputs = model.generate(**input_ids, max_new_tokens=max_new_tokens)
        print(tokenizer.decode(outputs[0]), "\n")

    # simple instruction example
    chat = [
        {"role": "user", "content": "Write me a poem in Dutch with 2 emojis inside"},
    ]
    input_ids = tokenizer.apply_chat_template(chat, return_tensors="pt").to(device)
    with TaskTimer("single instruction generation"):
        outputs = model.generate(input_ids, max_new_tokens=max_new_tokens)
        print(tokenizer.decode(outputs[0]), "\n")

    ### batch generation example
    # (better than using pipeline which abstracts too much away, giving less control)
    # currenlty it completes the text rather than directly following the instruction
    texts = [
        f"write me a poem in {lang}"
        for lang in ["Dutch", "French", "German", "Spanish"]
    ]
    texts.append(
        "tell me a short story about a kid at the beach for the first time in Europe"
    )
    # chats = [[{ "role": "user", "content": t}] for t in texts]

    with TaskTimer(f"batch generation (n={len(texts)})"):
        batch_inputs = tokenizer(texts, return_tensors="pt", padding=True).to(device)
        batch_outputs = model.generate(**batch_inputs, max_new_tokens=max_new_tokens)

        # https://github.com/huggingface/transformers/blob/main/src/transformers/models/gemma/modeling_gemma.py#L1090
        output_texts: list[str] = tokenizer.batch_decode(
            batch_outputs, skip_special_tokens=True
        )

    for i, res in enumerate(output_texts):
        print(f"\n--- response {i}: ---")
        print(res, "\n")
    print(res)


def get_model():
    # load quantized model (load_in_8_bit is critical to fit in memory)
    quantization_config = BitsAndBytesConfig(llm_int8_threshold=4.0, load_in_8_bit=True)
    with TaskTimer("model load"):
        tokenizer = AutoTokenizer.from_pretrained(MODEL_ID)
        model = AutoModelForCausalLM.from_pretrained(
            MODEL_ID,
            quantization_config=quantization_config,
            torch_dtype=torch.bfloat16,
            device_map="auto",
        )
        return model, tokenizer


if __name__ == "__main__":
    main()
