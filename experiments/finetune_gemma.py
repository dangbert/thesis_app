#!/usr/bin/env python3
################################################################################
# based on (high level) tutorial: https://huggingface.co/blog/gemma-peft
# see also:
#   https://github.com/adithya-s-k/LLM-Alchemy-Chamber/blob/main/Finetuning/Gemma_finetuning_notebook.ipynb
#   https://huggingface.co/google/gemma-7b-it#chat-template
#   https://ai.google.dev/gemma/docs/formatting
#   https://adithyask.medium.com/a-beginners-guide-to-fine-tuning-gemma-0444d46d821c
################################################################################

import argparse
import os
import sys
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
from transformers.models.gemma import modeling_gemma
from transformers.models.gemma.tokenization_gemma_fast import GemmaTokenizerFast
from datasets import load_dataset, Dataset, DatasetDict
from peft import LoraConfig
from trl import SFTTrainer  # https://github.com/huggingface/trl

import config
from config import get_device, TaskTimer

sys.path.append(os.path.join(config.DATASETS_DIR, "alpaca_cleaned"))
from download_alpaca_cleaned import TRANSLATED_PATH

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

MODEL_ID = "google/gemma-2b-it"

logger = config.get_logger(__name__)

prompt_template = """
<start_of_turn>user
{instruction}
{input}<end_of_turn>
<start_of_turn>model
""".strip()


def main():
    max_seq_len = 1000
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

    print(f"using device {device}")
    model, tokenizer = get_model()

    # load translated alpaca dataset
    tdataset: DatasetDict = load_dataset(
        "json", data_files=TRANSLATED_PATH, split="train"
    )
    logger.info(f"reloaded cached dataset from '{TRANSLATED_PATH}'")
    logger.info(f"column names: {tdataset.column_names}")

    def format_entry(entry):
        chat = [
            {"role": "user", "content": f"{entry['instruction']}\\n{entry['input']}"},
            {"role": "assistant", "content": entry["output"]},
        ]
        entry["prompt"] = tokenizer.apply_chat_template(
            chat, tokenize=False, add_generation_prompt=False
        )
        return entry

    with TaskTimer("format dataset entries"):
        tdataset = tdataset.map(format_entry)

    tdataset = tdataset.train_test_split(test_size=0.2)
    train_data = tdataset["train"]
    test_data = tdataset["test"]

    ### simple generation example
    with TaskTimer("single generation"):
        outputs = get_completion(
            "schrijf een gedicht over de liefde",
            model,
            tokenizer,
            device,
        )
        print(outputs)

    logger.info(f"train_data column names: {train_data.column_names}")
    logger.info(f"example data item: train_data[1]['prompt']")

    lora_config = LoraConfig(
        r=8,  # rank (low attention dimension)
        # this list is equivalent to find_all_linear_names() in https://github.com/adithya-s-k/LLM-Alchemy-Chamber/blob/c50a8ac2f0078ed1e7a69427a3953fe58a825699/Finetuning/Gemma_finetuning_notebook.ipynb
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

    tokenizer.pad_token = tokenizer.eos_token  # https://stackoverflow.com/a/76453052
    torch.cuda.empty_cache()
    # pass max_seq_len here?
    # TODO: pass in compute_metrics to log/compute eval metrics as well...
    trainer = SFTTrainer(
        model=model,
        tokenizer=tokenizer,
        train_dataset=train_data,
        eval_dataset=test_data,
        args=transformers.TrainingArguments(
            per_device_train_batch_size=1,
            gradient_accumulation_steps=4,
            warmup_steps=100,
            num_epochs=10,
            max_steps=1_000_000,
            logging_steps=1,
            eval_steps=5,
            learning_rate=2e-4,
            fp16=True,
            output_dir="outputs",
            optim="paged_adamw_8bit",
            save_strategy="epoch",
        ),
        peft_config=lora_config,
        # name of dataset field to read text from
        dataset_text_field="prompt",
    )
    with TaskTimer("finetuning"):
        trainer.train()

    with TaskTimer("final generation:"):
        outputs = get_completion(
            "schrijf een gedicht over de liefde",
            model,
            tokenizer,
            device,
        )
        print(outputs)

    # breakpoint()
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


def get_completion(
    query: str, model, tokenizer, device: str, max_new_tokens: int = 1000
) -> str:
    #     prompt_template = """
    # <start_of_turn>user
    # Below is an instruction that describes a task. Write a response that appropriately completes the request.
    # {query}
    # <end_of_turn>\n<start_of_turn>model
    # """
    #     prompt = prompt_template.format(query=query)
    #     encodeds = tokenizer(prompt, return_tensors="pt", add_special_tokens=True) # also adds special <bos> to start

    # equivalent
    prompt = tokenizer.apply_chat_template(
        [{"role": "user", "content": query}], tokenize=False, add_generation_prompt=True
    )
    encodeds = tokenizer(prompt, return_tensors="pt", add_special_tokens=False)

    model_inputs = encodeds.to(device)
    generated_ids = model.generate(
        **model_inputs,
        max_new_tokens=max_new_tokens,
        do_sample=True,
        pad_token_id=tokenizer.eos_token_id,
    )
    # decoded = tokenizer.batch_decode(generated_ids)
    decoded = tokenizer.decode(generated_ids[0], skip_special_tokens=True)
    return decoded


if __name__ == "__main__":
    main()
