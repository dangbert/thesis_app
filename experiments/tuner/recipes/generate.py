# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.
import itertools
import os
import sys
import time
from typing import Any, Dict, List, Optional, Tuple

import torch
from omegaconf import DictConfig

from torch import nn

from torchtune import config, utils
from torchtune.data import AlpacaInstructTemplate

import pandas as pd
from jinja2 import Environment, FileSystemLoader
from openai.types.chat.chat_completion import ChatCompletion

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
EXPERIMENTS_DIR = os.path.realpath(os.path.join(SCRIPT_DIR, ".."))
sys.path.append(EXPERIMENTS_DIR)
from AbstractModel import AbstractModel, IPrompt  # noqa: E402
from gpt import GPTModel  # noqa: E402
import config as projconfig  # noqa: E402

logger = utils.get_logger("DEBUG")


class InferenceRecipe(AbstractModel):
    """
    Recipe for generating tokens from a dense Transformer-based LLM.

    Currently this recipe supports single-GPU generation only. Speculative
    decoding is not supported.

    For more details on how to use this recipe for generation, please see our
    tutorial: https://pytorch.org/torchtune/main/tutorials/e2e_flow.html#generation

    For using this recipe with a quantized model, please the following section of
    the above tutorial:
    https://pytorch.org/torchtune/main/tutorials/e2e_flow.html#speeding-up-generation-using-quantization
    """

    def __init__(self, cfg: DictConfig) -> None:
        self._device = utils.get_device(device=cfg.device)
        self._dtype = utils.get_dtype(dtype=cfg.dtype)
        self._quantizer = config.instantiate(cfg.quantizer)
        self._quantization_mode = utils.get_quantizer_mode(self._quantizer)

        self.alpaca_template = AlpacaInstructTemplate()

        utils.set_seed(seed=cfg.seed)

    def setup(self, cfg: DictConfig) -> None:
        checkpointer = config.instantiate(cfg.checkpointer)
        if self._quantization_mode is None:
            ckpt_dict = checkpointer.load_checkpoint()
        else:
            # weights_only needs to be False when loading a quantized model
            # currently loading a quantized model is only supported with the
            # FullModelTorchTuneCheckpointer
            ckpt_dict = checkpointer.load_checkpoint(weights_only=False)

        self._model = self._setup_model(
            model_cfg=cfg.model,
            model_state_dict=ckpt_dict[utils.MODEL_KEY],
        )
        self._tokenizer = config.instantiate(cfg.tokenizer)

    def _setup_model(
        self,
        model_cfg: DictConfig,
        model_state_dict: Dict[str, Any],
    ) -> nn.Module:
        with utils.set_default_dtype(self._dtype), self._device:
            model = config.instantiate(model_cfg)

        if self._quantization_mode is not None:
            model = self._quantizer.quantize(model)
            model = model.to(device=self._device, dtype=self._dtype)

        model.load_state_dict(model_state_dict)

        # Validate model was loaded in with the expected dtype.
        utils.validate_expected_param_dtype(model.named_parameters(), dtype=self._dtype)
        logger.info(f"Model is initialized with precision {self._dtype}.")

        # Ensure the cache is setup on the right device
        with self._device:
            model.setup_caches(max_batch_size=1, dtype=self._dtype)

        return model

    def __call__(
        self,
        prompts: List[IPrompt],
        cfg: DictConfig,
    ) -> Tuple[List[str], List[ChatCompletion]]:
        raw_outputs = [self.generate(cfg, prompt) for prompt in prompts]
        return raw_outputs, None

    @torch.no_grad()
    def generate(self, cfg: DictConfig, prompt: str):
        tokens = self._tokenizer.encode(prompt, add_bos=True, add_eos=False)
        prompt = torch.tensor(tokens, dtype=torch.int, device=self._device)

        custom_generate_next_token = None

        # since quantized model uses torch.compile to get speedup, it needs a warm up / prefill run
        # to get the accurate performance measurement
        if self._quantization_mode is not None:
            logger.info("Starting compilation to improve generation performance ...")
            custom_generate_next_token = torch.compile(
                utils.generate_next_token, mode="max-autotune", fullgraph=True
            )
            t0 = time.perf_counter()
            _ = utils.generate(
                model=self._model,
                prompt=prompt,
                max_generated_tokens=2,
                temperature=cfg.temperature,
                top_k=cfg.top_k,
                eos_id=self._tokenizer.eos_id,
                custom_generate_next_token=custom_generate_next_token,
            )
            t = time.perf_counter() - t0
            logger.info(f"Warmup run for quantized model takes: {t:.02f} sec")

        t0 = time.perf_counter()
        generated_tokens = utils.generate(
            model=self._model,
            prompt=prompt,
            max_generated_tokens=cfg.max_new_tokens,
            temperature=cfg.temperature,
            top_k=cfg.top_k,
            eos_id=self._tokenizer.eos_id,
            custom_generate_next_token=custom_generate_next_token,
        )
        t = time.perf_counter() - t0

        raw_output = self._tokenizer.decode(generated_tokens)
        logger.info(raw_output)

        model_size = sum(
            [
                p.numel() * p.dtype.itemsize
                for p in itertools.chain(
                    self._model.parameters(), self._model.buffers()
                )
            ]
        )

        tokens_generated = len(generated_tokens) - prompt.size(0)
        tokens_sec = tokens_generated / t
        logger.info(
            f"Time for inference: {t:.02f} sec total, {tokens_sec:.02f} tokens/sec"
        )
        logger.info(f"Bandwidth achieved: {model_size * tokens_sec / 1e9:.02f} GB/s")
        logger.info(f"Memory used: {torch.cuda.max_memory_allocated() / 1e9:.02f} GB")
        return raw_output


def benchmark_fluency(cfg: DictConfig) -> float:
    gpt = GPTModel(cfg.benchmark_judge)
    fname = os.path.join(
        projconfig.DATASETS_DIR, "synthetic_smart/v4/feedback_gpt-3.5-turbo-0125.csv"
    )
    env = Environment(loader=FileSystemLoader(os.path.join(EXPERIMENTS_DIR, "prompts")))
    fluency_template = env.get_template("fluency_score.jinja2")
    df = pd.read_csv(fname)

    recipe = InferenceRecipe(cfg=cfg)
    recipe.setup(cfg=cfg)
    prompts = [
        recipe.alpaca_template.format({"instruction": prompt})
        for prompt in df["prompt"].tolist()
    ]

    outputs, _ = recipe(prompts, cfg=cfg)
    outputs = [get_subresponse(output) for output in outputs]
    df["output_llama2"] = outputs
    outname = "tmp.csv"
    df.to_csv(outname)

    def build_fluency_prompt(row: pd.Series) -> str:
        return fluency_template.render(
            {
                "question": "provide feedback in Dutch on a student's assignment.",
                "answer": row["output_llama2"],
            }
        )

    df["fluency_prompts"] = df.apply(build_fluency_prompt, axis=1).to_list()
    df.to_csv(outname)

    outputs, meta = gpt(df["fluency_prompts"].tolist(), temperature=0.2)
    total_price = gpt.compute_price(meta)
    print(f"total_price=${total_price:.4f}")

    df["fluency_scores"] = [int(output) for output in outputs]
    print(f"fluency scores (model={gpt.model_name}):")
    print(df["fluency_scores"].describe())
    df.to_csv(outname)
    print(f"wrote '{outname}'")
    return df["fluency_scores"].mean()


def get_subresponse(output: str) -> str:
    """
    Get the relevant part of a response where the prompt is also included.
    Assumes the prompt used the AplacaInstructTemplate
    """
    marker = "\n### Response:\n"
    idx = output.find(marker)
    if idx != -1:
        return output[idx + len(marker) :]
    return output  # fallback


@config.parse
def main(cfg: DictConfig) -> None:
    if cfg.benchmark_fluency:
        benchmark_fluency(cfg)
        return

    t = AlpacaInstructTemplate()
    # reformat prompt to align with training format
    cfg.prompt = t.format({"instruction": cfg.prompt})

    config.log_config(recipe_name="InferenceRecipe", cfg=cfg)
    recipe = InferenceRecipe(cfg=cfg)
    recipe.setup(cfg=cfg)
    recipe.generate(cfg=cfg, prompt=cfg.prompt)


if __name__ == "__main__":
    sys.exit(main())