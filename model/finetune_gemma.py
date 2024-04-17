#!/usr/bin/env python3
################################################################################
# based on (high level) tutorial: https://huggingface.co/blog/gemma-peft
# see also:
#   https://adithyask.medium.com/a-beginners-guide-to-fine-tuning-gemma-0444d46d821c 
#   https://github.com/adithya-s-k/LLM-Alchemy-Chamber/blob/main/Finetuning/Gemma_finetuning_notebook.ipynb
################################################################################

import argparse
import os
import torch
import transformers
from transformers import (
    AutoTokenizer,
    AutoModelForCausalLM,
    BitsAndBytesConfig,
    DataCollatorForLanguageModeling,
    Trainer,
    TrainingArguments,
)
import datasets
from peft import LoraConfig
from trl import SFTTrainer  # https://github.com/huggingface/trl

from config import get_device, TaskTimer

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

MODEL_ID = "google/gemma-2b"


def main():
    parser = argparse.ArgumentParser(
        description="fine tune gemma-2b",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--wandb",
        "-w",
        action="store_true",
        help="Enable wandb logging",
    )
    args = parser.parse_args()
    if not args.wandb:
        os.environ["WANDB_MODE"] = "offline"  # don't sync
    else:
        os.environ["WANDB_MODE"] = "online"

    device = get_device()

    model, tokenizer = get_model()

    max_new_tokens = 400
    print(f"using device {device}")
    model, tokenizer = get_model()

    ### simple generation example
    input_text = "Quote: Imagination is more"
    inputs = tokenizer(input_text, return_tensors="pt").to(device)
    with TaskTimer("single generation"):
        outputs = model.generate(**inputs, max_new_tokens=max_new_tokens)
        print(tokenizer.decode(outputs[0]), "\n")


    dataset_text_field = "formatted_text"
    def add_formatted_text(example):
        """Given a single dataset item, adds a formatted text combining quote and author."""
        # Creating the formatted text by combining quote and author
        example[dataset_text_field] = f"Quote: {example['quote']}\nCool Author: {example['author']}"
        return example

    # def format_and_tokenize(batch):
    #     """Given a sample of dataset items, format them as desired and return results of tokenizer."""
    #     formatted_texts = [f"Quote: {quote}\nCool Author: {author}" for quote, author in zip(batch['quote'], batch['author'])]
    #     # Tokenizing the formatted texts
    #     return tokenizer(formatted_texts)

    with TaskTimer("dataset load and process"):
        data = datasets.load_dataset("Abirate/english_quotes")
        print("original column names: ", data.column_names)
        # add field "formatted_text" to each itme
        data = data.map(add_formatted_text)
        # add fields input_ids and attention_mask to each item (actually trainer seems to do this itself)
        # data = data.map(lambda samples: tokenizer(samples[dataset_text_field]), batched=True)

    print("final column names: ", data.column_names)
    print("example data item: ", data["train"][0])

    lora_config = LoraConfig(
        r=8,
        target_modules=[
            "q_proj",
            "o_proj",
            "k_proj",
            "v_proj",
            "gate_proj",
            "up_proj",
            "down_proj",
        ],
        task_type="CAUSAL_LM",
    )

    trainer = SFTTrainer(
        model=model,
        tokenizer=tokenizer,
        train_dataset=data["train"],
        args=transformers.TrainingArguments(
            per_device_train_batch_size=4,
            gradient_accumulation_steps=4,
            warmup_steps=2,
            max_steps=25,
            learning_rate=2e-4,
            fp16=True,
            logging_steps=1,
            output_dir="outputs",
            optim="paged_adamw_8bit",
        ),
        peft_config=lora_config,
        # name of dataset field to read text from
        dataset_text_field=dataset_text_field,
    )
    with TaskTimer("finetuning"):
        trainer.train()

    with TaskTimer("final generation:"):
        outputs = model.generate(**inputs, max_new_tokens=max_new_tokens)
        print(tokenizer.decode(outputs[0], skip_special_tokens=True), "\n")


    breakpoint()
    print(trainer)


def get_model():
    # load quantized model (load_in_8_bit is critical to fit in memory)
    quantization_config = BitsAndBytesConfig(
        load_in_4_bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.bfloat16,
    )
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
