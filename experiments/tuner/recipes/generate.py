"""Adapated generation script (from tourchtune) which supports benchmarking model checkpoints on fluency."""

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

import jinja2
from openai.types.chat.chat_completion import ChatCompletion

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
EXPERIMENTS_DIR = os.path.realpath(os.path.join(SCRIPT_DIR, "../.."))
sys.path.append(EXPERIMENTS_DIR)
from AbstractModel import AbstractModel, IPrompt  # noqa: E402
from gpt import GPTModel  # noqa: E402
import config as projconfig  # noqa: E402

FLUENCY_QUESTION = "provide a paragraph of feedback in Dutch on a student's assignment."
FNAME_GOALS = os.path.join(
    projconfig.DATASETS_DIR, "synthetic_smart/v4/smart_goals.csv"
)

logger = utils.get_logger("INFO")


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
        verbose: bool = True,
    ) -> Tuple[List[str], List[ChatCompletion]]:
        raw_outputs = [
            self.generate(cfg, prompt, verbose=verbose) for prompt in prompts
        ]
        return raw_outputs, None

    @torch.no_grad()
    def generate(self, cfg: DictConfig, prompt: str, verbose: bool = True):
        tokens = self._tokenizer.encode(prompt, add_bos=True, add_eos=False)
        prompt = torch.tensor(tokens, dtype=torch.int, device=self._device)

        custom_generate_next_token = None

        logf = logger.info if verbose else logger.debug  # logger function

        # since quantized model uses torch.compile to get speedup, it needs a warm up / prefill run
        # to get the accurate performance measurement
        if self._quantization_mode is not None:
            logf("Starting compilation to improve generation performance ...")
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
            logf(f"Warmup run for quantized model takes: {t:.02f} sec")

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
        logf(raw_output)

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
        logf(f"Time for inference: {t:.02f} sec total, {tokens_sec:.02f} tokens/sec")
        logf(f"Bandwidth achieved: {model_size * tokens_sec / 1e9:.02f} GB/s")
        logf(f"Memory used: {torch.cuda.max_memory_allocated() / 1e9:.02f} GB")
        return raw_output


def benchmark_fluency_local(
    cfg: DictConfig, max_samples: Optional[int] = None
) -> float:
    """Benchmark the Dutch fluency of a local LLama model's checkpoints."""
    df_goals = _get_goals_df(FNAME_GOALS, max_samples=max_samples)
    outpath = os.path.join(
        cfg.EXP_DIR, f"benchmark_chkp_{cfg.CHKP_NUM}_{cfg.benchmark_judge}.csv"
    )

    ### 1. get outputs from local model (instructed to write feedback in Dutch on example assignments)
    if os.path.isfile(outpath):
        logger.info(f"resumed from '{outpath}'")
        return _measure_fluency(outpath, cfg.benchmark_judge)

    else:
        recipe = InferenceRecipe(cfg=cfg)
        recipe.setup(cfg=cfg)

        df = df_goals.copy()[["goal_id"]]  # build new df documenting this benchmark
        # NOTE: local_prompt could be renamed 'speaker_prompt'
        df["local_prompt"] = df_goals.apply(_build_speaker_prompt, axis=1).to_list()
        logger.info(f"generating local outputs for {len(df)} prompts")
        outputs, _ = recipe(df["local_prompt"], cfg=cfg, verbose=False)
        outputs = [get_subresponse(output) for output in outputs]
        df["local_output"] = outputs
        _flush_df(df, outpath)
        return _measure_fluency(outpath, cfg.benchmark_judge)


def benchmark_fluency_openai(
    candidate_model: str, judge_model: str, max_samples: Optional[int] = None
) -> float:
    """
    Benchmark the Dutch abilities of a candidate OpenAI model (e.g. "gpt-3.5-turbo-0125") using a given judge model (e.g. "gpt-4-0125-preview")
    (This function is independent of LLama, using just the OpenAI API).
    """

    logger.info(f"benchmarking fluency of '{candidate_model}' using '{judge_model}'")
    df_goals = _get_goals_df(FNAME_GOALS, max_samples=max_samples)
    outpath = os.path.join(
        os.path.dirname(FNAME_GOALS),
        f"fluency_{candidate_model}_judged_by_{judge_model}.csv",
    )
    if os.path.isfile(outpath):
        logger.info(f"resumed from '{outpath}'")
        return _measure_fluency(outpath, judge_model)

    # generate outputs with candidate_model
    df = df_goals.copy()[["goal_id"]]
    df["speaker_prompt"] = df_goals.apply(_build_speaker_prompt, axis=1).to_list()
    logger.info(f"generating {candidate_model} outputs for {len(df)} prompts")

    gpt = GPTModel(candidate_model)
    gpt_outputs, meta = gpt(df["speaker_prompt"].tolist(), temperature=0.2)
    logger.info(f"price=${gpt.compute_price(meta):.4f}")

    df["speaker_output"] = gpt_outputs
    _flush_df(df, outpath)
    return _measure_fluency(outpath, judge_model)


def _measure_fluency(fname: str, judge_model: str) -> float:
    """
    Given a csv of model outputs, benchmark them using the given GPT judge model (e.g. 'gpt-4-0125-preview').
    Edits the csv in place to add a 'fluency_score' columns
    """
    ### 2. evaluate outputs using GPT model as a fluency judge
    df = pd.read_csv(fname)
    if "fluency_score" in df.columns:
        logger.info(f"skipping rerun of existing benchmark: '{fname}'")
        return -1

    speaker_key = "local_output" if "local_output" in df.columns else "speaker_output"

    # df_goals["fluency_prompts"] = df_goals.apply(build_fluency_prompt, axis=1).to_list()
    env = jinja2.Environment(
        loader=jinja2.FileSystemLoader(os.path.join(EXPERIMENTS_DIR, "prompts"))
    )
    fluency_template = env.get_template("fluency_score_nl.jinja2")

    def build_fluency_prompt(row: pd.Series) -> str:
        """Prompt for judge model to use."""
        return fluency_template.render(
            {
                "question": FLUENCY_QUESTION,
                "answer": row[speaker_key],
            }
        )

    df["fluency_prompt"] = df.apply(build_fluency_prompt, axis=1).to_list()
    _flush_df(df, fname)

    gpt = GPTModel(judge_model)
    logger.info(f"computing {len(df)} model outputs")

    gpt_outputs, meta = gpt(df["fluency_prompt"].tolist(), temperature=0.2)
    logger.info(f"price=${gpt.compute_price(meta):.4f}")

    scores = []
    for output in gpt_outputs:
        try:
            num = int(output)
        except ValueError:
            num = None
        scores.append(num)

    df["fluency_score"] = scores
    _flush_df(df, fname)

    # count nones
    bad_count = len(df[df["fluency_score"].isna()])
    if bad_count > 0:
        logger.warning(f"non-integer fluency scores: {bad_count}")

    print(f"fluency scores (model={gpt.model_name}):")
    print(df["fluency_score"].describe())
    return df["fluency_score"].mean()


def _build_speaker_prompt(row: pd.Series) -> str:
    """Prompt for a model to speak Dutch (for later fluency evaluation)."""
    local_template = AlpacaInstructTemplate()
    student_draft = f"{row['smart']}\n{row['plan']}"
    return local_template.format(
        {"instruction": FLUENCY_QUESTION, "input": student_draft}
    )


def _flush_df(x: pd.DataFrame, outpath: str):
    x.to_csv(outpath)
    print(f"wrote '{outpath}'")


def _get_goals_df(fname: str, max_samples: Optional[int] = None) -> pd.DataFrame:
    df_goals = pd.read_csv(FNAME_GOALS)
    if max_samples is not None:
        logger.info(
            f"limiting to max_samples={max_samples} (original size = {len(df_goals)})"
        )
        df_goals = df_goals[:max_samples]
    return df_goals


def get_subresponse(output: str) -> str:
    """
    Get the relevant part of a response where the prompt is also included.
    Assumes the prompt used the AlpacaInstructTemplate.
    Useful for extracting just the response from the local LLama model.
    """
    marker = "\n### Response:\n"
    idx = output.find(marker)
    if idx != -1:
        return output[idx + len(marker) :]
    return output  # fallback


@config.parse
def main(cfg: DictConfig) -> None:
    #### benchmark GPT model fluencies
    #   uncomment this section and run with:
    #   tune run ./recipes/generate.py --config ./generation.yaml # (generation.yaml doesn't influence the output in this case)
    #   TODO: move this to ../../benchmark.py?
    """
    judge_model = "gpt-4-0125-preview"
    for candidate_model in ["gpt-3.5-turbo-0125", "gpt-4-0125-preview"]:
        benchmark_fluency_openai(candidate_model, judge_model)  # , max_samples=5)
    exit(0)
    """

    #### benchmark Dutch fluency of local LLama model checkpoint
    if cfg.benchmark_fluency:
        benchmark_fluency_local(cfg)
        return

    #### otherwise generate output for a given prompt
    t = AlpacaInstructTemplate()
    # reformat prompt to align with training format
    cfg.prompt = t.format({"instruction": cfg.prompt})

    config.log_config(recipe_name="InferenceRecipe", cfg=cfg)
    recipe = InferenceRecipe(cfg=cfg)
    recipe.setup(cfg=cfg)
    recipe.generate(cfg=cfg, prompt=cfg.prompt)


if __name__ == "__main__":
    sys.exit(main())
