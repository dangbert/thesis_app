#!/usr/bin/env python3

import os
import argparse
import sys
import yaml
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import wandb
from typing import Optional, Callable
import math

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

TUNER_EXP_DIR = os.path.join(SCRIPT_DIR, "llama2_7B/experiments/")
TUNER_EXP_CHAT_DIR = os.path.join(SCRIPT_DIR, "llama2_7B_chat/experiments/")
EXPERIMENTS_DIR = os.path.realpath(os.path.join(SCRIPT_DIR, ".."))
sys.path.append(EXPERIMENTS_DIR)
import config as projconfig  # noqa: E402

logger = projconfig.get_logger(__name__)
settings = projconfig.get_settings()


def main():
    results = dict()  # will collect results from our experiment runs
    logger.info("### gathering fluency baselines:")
    baselines = dict()
    for nickname, fname in [
        ("GPT-4", "fluency_gpt-4-0125-preview_judged_by_gpt-4-0125-preview.csv"),
        ("GPT-3.5", "fluency_gpt-3.5-turbo-0125_judged_by_gpt-4-0125-preview.csv"),
        (
            "Llama-2-7b-chat",
            os.path.join(
                TUNER_EXP_CHAT_DIR, "unnamed/benchmark_chkp_-1_gpt-4-0125-preview.csv"
            ),
        ),
        ("Llama-2-7b", "benchmark_chkp_-1_gpt-4-0125-preview.csv"),
        # plot best Llama-2-7B-nl as well:
        # ("Llama-2-7b-nl", "full1/benchmark_chkp_0_gpt-4-0125-preview.csv"),
        ("Llama-2-7b-nl", "lr5_8c/benchmark_chkp_2_gpt-4-0125-preview.csv"),
    ]:
        if "GPT" in nickname:
            fname = os.path.join(EXPERIMENTS_DIR, "data/synthetic_smart/v4/", fname)
        elif not os.path.isabs(fname):
            fname = os.path.join(TUNER_EXP_DIR, fname)
        df = pd.read_csv(fname)
        print(f"\n{fname}:")
        df = _process_fluency_df(df)
        if nickname == "Llama-2-7b":  # store baseline for later
            results["default"] = {"gpt4": {-1: df["fluency_score"].mean().item()}}
        baselines[nickname] = df["fluency_score"].to_list()
    plot_fluency_baselines(baselines)

    logger.info("### 'full' experiments:")
    # NOTE: full4 was originally silvery-brook-8 but didn't save checkpoints so reran as fine-bird-9
    full_exps = ["full1", "full2", "full3", "full4"]

    def build_nickname(c: dict):
        # return f"grad{c['gradient_accumulation_steps']}"
        lr = round(c["optimizer"]["lr"] * 10**4)
        return f"lr{lr}_grad{c['gradient_accumulation_steps']}"

    for name in full_exps:
        results[name] = {
            "gpt4": get_fluency_scores(name),
            "wandb": get_wandb_stats(
                name,
                build_nickname=build_nickname,
                # build_nickname=lambda c: f"grad{c['gradient_accumulation_steps']}"
            ),
        }
    plot_tuner(results, full_exps, group_name="full", wspace=0.4)

    logger.info("### 'lr' experiments:")

    # b were learning rate experiments of 4 epochs each, c was a rerun with 7 epochs each
    for letter in "bc":
        lr_exps = ["lr4_8", "lr4_16", "lr5_8", "lr5_16"]
        lr_exps = [f"{exp}{letter}" for exp in lr_exps]
        for name in lr_exps:
            results[name] = {
                "gpt4": get_fluency_scores(name),
                "wandb": get_wandb_stats(
                    name,
                    build_nickname=build_nickname,
                    # build_nickname=lambda c: f"lr{int(c['lr']*10**4)}_grad{c['gradient_accumulation_steps']}",
                ),
            }
        plot_tuner(results, lr_exps, group_name=f"lr{letter}")
    print()

    # dump to yaml
    outpath = os.path.join(TUNER_EXP_DIR, "all_results.yaml")
    for key in results.keys():
        if "wandb" in results[key]:
            results[key].pop("wandb")  # pop for cleaner yaml
    with open(outpath, "w") as f:
        yaml.dump(results, f)
    print(f"wrote results to '{outpath}'")


def plot_tuner(
    results: dict,
    exp_names: list[str],
    judge: str = "gpt4",
    save_dir: str = TUNER_EXP_DIR,
    group_name: Optional[str] = None,
    wspace: float = 0.45,
):
    """Plot fluency and validation loss across a group of fine-tuning experiments."""

    plt.clf()
    plt.title(f"Fine-Tuning Experiments {group_name}")
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(20, 8))

    max_val_loss = 0.0
    baseline_fluency = results["default"]["gpt4"][-1]
    for exp_name in exp_names:
        epochs = list(results[exp_name][judge].keys())
        scores = list(results[exp_name][judge].values())
        # add 1 to every epoch to be "epochs complete" not 0-index epochs
        epochs = [epoch + 1 for epoch in epochs]
        # also insert baseline score at 0
        epochs.insert(0, 0)
        scores.insert(0, baseline_fluency)

        nickname = results[exp_name]["wandb"]["nickname"]
        ax1.plot(epochs, scores, label=nickname)

        val_loss = results[exp_name]["wandb"]["val_loss"]
        ax2.plot(val_loss["epochs_complete"], val_loss["val_loss"], label=nickname)
        max_val_loss = max(max_val_loss, val_loss["val_loss"].max().item())
    num_epochs = max(epochs) - 1

    title_fontsize = 16
    axis_fontsize = 14

    def set_common(ax):
        ax.set_xlabel("Epochs Complete", fontsize=axis_fontsize)
        ax.set_xticks(range(0, num_epochs + 2))
        ax.set_xlim(0, num_epochs + 1)

    set_common(ax1)
    ax1.set_title("Fluency Score Across Fine-Tuning", fontsize=title_fontsize)
    ax1.set_ylabel("Avg. Fluency Score (5-Point Scale)", fontsize=axis_fontsize)
    ax1.axhline(y=baseline_fluency, color="r", linestyle="--")  # red baseline
    ax1.set_yticks(np.arange(1.0, 5.5, 0.5))  # Label every whole integer
    # unlabeled ticks every 0.5
    ax1.yaxis.set_minor_locator(plt.MultipleLocator(0.5))
    # ax1.yaxis.set_minor_formatter(plt.NullFormatter())

    set_common(ax2)
    ax2.set_ylabel("Avg. Validation Loss", fontsize=axis_fontsize)
    ax2.set_title("Validation Loss Across Fine-Tuning", fontsize=title_fontsize)
    max_val_loss = math.ceil(max_val_loss)
    ax2.set_ylim(0, max_val_loss)

    # add single legend for entire plot, explaining label colors vs exp_name
    handles, labels = [], []
    for ax in [ax1, ax2]:
        for handle, label in zip(*ax.get_legend_handles_labels()):
            if label not in labels:
                handles.append(handle)
                labels.append(label)
    fig.legend(
        handles,
        labels,
        loc="center",
        ncol=1,
        fontsize=axis_fontsize,
        title="Runs",
        title_fontsize=title_fontsize,
    )
    plt.tight_layout()
    plt.subplots_adjust(wspace=wspace)  # more space between plots

    if group_name is None:
        group_name = "_".join(exp_names)
    fname = os.path.join(save_dir, f"tuning_{group_name}.pdf")
    plt.savefig(fname)
    print(f"wrote tuning plot to {fname}")


def plot_fluency_baselines(baselines: dict):
    """Boxplots of baseline Dutch fluency score distributions of LLMs of interest."""
    # make boxplots for each model, using nickname as label
    plt.clf()
    plt.title("LLM Fluency Baselines")
    plt.boxplot(baselines.values(), showmeans=True, meanprops=projconfig.MEANPROPS)
    plt.xticks(range(1, len(baselines) + 1), baselines.keys())
    plt.yticks(np.arange(1.0, 5.5, 1.0))  # Label every whole integer
    plt.gca().yaxis.set_minor_locator(plt.MultipleLocator(0.5))
    plt.gca().yaxis.set_minor_formatter(plt.NullFormatter())
    plt.xlabel("Model")
    plt.ylabel("Fluency Score (5-Point Scale)")
    fname = os.path.join(TUNER_EXP_DIR, "fluency_baselines.pdf")
    plt.tight_layout()
    # plt.subplots_adjust(left=0.0, right=1.0)  # more space between plots
    plt.savefig(fname)
    print(f"wrote plot to {fname}")


def get_fluency_scores(exp_name: str, model_name: str = "gpt-4-0125-preview") -> dict:
    """
    Gather fluency scores from benchmarked checkpoints for a given run.
    E.g. run "full1" -> {0: 3.5, 1: 3.2, 2: 3.3, ...}
    """
    print(f"\ngathering fluency scores for '{exp_name}'")
    scores = dict()
    for epoch in range(0, 10):
        fname = os.path.join(
            TUNER_EXP_DIR, exp_name, f"benchmark_chkp_{epoch}_{model_name}.csv"
        )
        # support potentially missing benchmark results for some epochs
        if not os.path.exists(fname):
            continue
        df = pd.read_csv(fname)
        if "fluency_score" not in df.columns:
            logger.warning(f"no fluency_score column in {fname}")
            continue
        print(f"\n{fname}:")
        df = _process_fluency_df(df)
        scores[epoch] = df["fluency_score"].mean().item()
    return scores


def _process_fluency_df(df: pd.DataFrame):
    orig_len = len(df)
    df = df.dropna(subset=["fluency_score"])
    non5s = len(df[df["fluency_score"] != 5])
    print(
        f"NaN count: {orig_len - len(df)} (dropped rows), non-5 scores counts: {non5s}"
    )
    print(df["fluency_score"].describe())
    return df


def get_wandb_stats(run_name: str, build_nickname=Callable) -> dict:
    # auto prompts for wandb login if needed
    api = wandb.Api()
    # get run where config.EXP_NAME == run_name

    # use settings.wandb_project, settings.wandb_entity
    runs: wandb.apis.public.Runs = api.runs(
        f"{settings.wandb_entity}/{settings.wandb_project}",
        {"config.EXP_NAME": run_name},
    )
    assert (
        len(runs) == 1
    ), f"expected 1 run for EXP_NAME='{run_name}', found {len(runs)}"
    run = runs[0]
    if run.state != "finished":
        logger.warning(f"run '{run_name}' is not finished")

    # https://github.com/wandb/wandb/blob/v0.16.6/wandb/apis/public/runs.py

    # (note: only later runs logged the "epoch" key for explititly mapping training steps to epochs)
    val_loss = run.history(keys=["val_loss"])

    num_epochs = run.config["epochs"]  # e.g. 4
    logger.info(f"exp_name={run_name}, num_epochs={num_epochs}")
    total_training_steps = val_loss["_step"][len(val_loss) - 1].item()  # e.g. 8282
    steps_per_epoch = (
        total_training_steps / num_epochs
    )  # assume all epochs were completed
    val_loss["epochs_complete"] = val_loss["_step"] / steps_per_epoch
    if run_name == "full1":
        # throw out rows where "epochs_complete" > 4 (to match other runs)
        val_loss = val_loss[val_loss["epochs_complete"] <= 4.1]

    nickname = build_nickname(run.config)
    logger.info(f"run '{run_name}' -> nickname: {nickname}")
    return {
        "url": run.url,
        "val_loss": val_loss,
        "nickname": nickname,
    }


if __name__ == "__main__":
    main()
