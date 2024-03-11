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
    AutoConfig,
    AutoTokenizer,
    AutoModelForCausalLM,
    BitsAndBytesConfig,
    pipeline,
)
from langchain_community.llms import HuggingFacePipeline
from transformers.models.llama.tokenization_llama_fast import DEFAULT_SYSTEM_PROMPT
from langchain.prompts import PromptTemplate
from typing import Dict
from contextlib import contextmanager

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATASETS_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, os.pardir, "datasets"))
PEER_READ_DIR = os.path.join(DATASETS_DIR, "PeerRead")


MODEL_ID = "meta-llama/Llama-2-7b-chat-hf"


def main():
    # interactive()
    play_datasets()


def play_datasets():
    """
    Note:
    tokenizer is of type:
    from transformers.models.llama.tokenization_llama_fast import LlamaTokenizerFast
    see DEFAULT_SYSTEM_PROMPT also in that file^
    """

    cur_dir = os.path.join(PEER_READ_DIR, "data/iclr_2017/train/parsed_pdfs/")

    fname = os.path.join(cur_dir, "304.pdf.json")
    assert os.path.exists(fname)
    print(f"reading {fname}", flush=True)
    with open(fname, "r") as f:
        data = json.load(f)

    paper_text = pdf_json_to_text(data)

    config = AutoConfig.from_pretrained(MODEL_ID)
    MAX_TOKENS = config.max_position_embeddings
    max_new_tokens = 1000
    model, tokenizer = get_model()
    # tokenizer_kwargs = {
    #     "max_length": MAX_TOKENS - max_new_tokens,
    #     "truncation": True
    # }

    def limit_text_len(prompt: str, max_tokens: int):
        """Somewhat hacky way to ensure the token length of a given string is <= max_tokens."""
        max_tokens = max(0, max_tokens)
        res = tokenizer(prompt)
        if len(res.data["input_ids"]) <= max_tokens:
            return prompt
        return tokenizer.decode(
            res.data["input_ids"][:max_tokens], skip_special_tokens=True
        )

    prompt_template = "The text that follows is a student's work on a research assignment. Create a plausible assignment rubric / set of directions that could reflect the assignment/goal the student completed.  Respond only with the assignment directions. The student's work follows:\n{paper_text}"
    prompt = prompt_template.format(paper_text=paper_text)
    prompt = limit_text_len(prompt, MAX_TOKENS - 1500)
    # tokenizer.use_default_system_prompt = True
    messages = [
        {"role": "system", "content": DEFAULT_SYSTEM_PROMPT},
        {"role": "user", "content": prompt},
    ]
    # the pipeline is supposed to automatically call apply_chat_template if passed messages, but I don't see this behavior
    # https://huggingface.co/docs/transformers/main/en/chat_templating#is-there-an-automated-pipeline-for-chat
    final_prompt: str = tokenizer.apply_chat_template(messages, tokenize=False)
    # tokenized_chat = tokenizer.apply_chat_template(messages, tokenize=True, return_tensors="pt", **tokenizer_kwargs).to(model.device)

    pipe = pipeline(
        "text-generation",
        model=model,
        tokenizer=tokenizer,
        max_new_tokens=max_new_tokens,
    )
    # get response (omitting the input prompt)
    with TaskTimer("rubric generation"):
        rubric: str = pipe(final_prompt, return_full_text=False)[0][
            "generated_text"
        ].strip()
    print("\nfinal output:")
    print(rubric)

    messages += [
        {"role": "assistant", "content": rubric},
        {"role": "user", "content": "Judge the student's work according to the defined rubric. Report a score out of 10 for each aspect."},
    ]
    with TaskTimer("grade generation"):
        grade: str = pipe(tokenizer.apply_chat_template(messages, tokenize=False), return_full_text=False)[0][
            "generated_text"
        ].strip()
    print("\nfinal grade:")
    print(grade)
    breakpoint()
    print()


def interactive():
    """Play with LLama by chatting through stdin."""
    model, tokenizer = get_model()

    # https://python.langchain.com/docs/integrations/llms/huggingface_pipelines
    print("creating pipline...")
    pipe = pipeline(
        "text-generation",
        model=model,
        tokenizer=tokenizer,
        max_new_tokens=1000,
        framework="pt",
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
    with TaskTimer("loading model", verbose=verbose):
        # the model will be automatically downloaded and cached (e.g. in ~/.cache/huggingface/)
        #  cache dir / running offline info: https://huggingface.co/docs/datasets/en/cache
        tokenizer = AutoTokenizer.from_pretrained(MODEL_ID)
        # tokenizer.use_default_system_prompt = False

        # load quantized model (load_in_8_bit is critical to fit in memory)
        quantization_config = BitsAndBytesConfig(llm_int8_threshold=4.0, load_in_8_bit=True)
        model = AutoModelForCausalLM.from_pretrained(
            MODEL_ID,
            quantization_config=quantization_config,
            device_map="auto",
        )
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

@contextmanager
def TaskTimer(task_name: str, verbose: bool = True):
    try:
        start_time = time.perf_counter()
        if verbose:
            print(f"\nstarting {task_name}...", flush=True)
        yield  # This is where your block of code will execute
    finally:
        end_time = time.perf_counter()
        if verbose:
            print(f"{task_name} completed in {(end_time - start_time):.2f} secs!", flush=True)



def pdf_json_to_text(data: Dict):
    """Convert PeerRead json object to a single string."""
    combined = ""
    for section in data["metadata"]["sections"]:
        heading, text = section["heading"], section["text"]
        combined += f"\n{heading}\n{text}"

    return combined.strip()


if __name__ == "__main__":
    main()
