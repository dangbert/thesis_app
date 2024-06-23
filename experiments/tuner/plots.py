#!/usr/bin/env python3

import os
import argparse
import sys
import yaml
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

TUNER_EXP_DIR = os.path.join(SCRIPT_DIR, "llama2_7B/experiments/")
EXPERIMENTS_DIR = os.path.realpath(os.path.join(SCRIPT_DIR, ".."))
sys.path.append(EXPERIMENTS_DIR)
import config as projconfig  # noqa: E402

logger = projconfig.get_logger(__name__)


def main():
    # parser = argparse.ArgumentParser(
    #     formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    # )
    # args = parser.parse_args()

    #### plot fluency baselines
    plot_fluency_baselines()

    #### plot fine-tuning fluency results
    results_path = os.path.join(TUNER_EXP_DIR, "results.yaml")
    with open(results_path, "r") as f:
        results = yaml.load(f, Loader=yaml.FullLoader)

    exp_names = ["full1", "full2", "full3", "full4"]
    for name in exp_names:
        print(f"Experiment: {name}")
        plot_fluency_tuning(
            results, name
        )  # , save_dir=os.path.join(TUNER_EXP_DIR, name))
    print()

    # gather results from second set of experiments (learning rates)
    for name in ["lr4_8", "lr4_16", "lr5_8", "lr5_16"]:
        results[name] = {"gpt4": dict()}
        for epoch in range(0, 3):
            fname = os.path.join(
                TUNER_EXP_DIR, name, f"benchmark_chkp_{epoch}_gpt-4-0125-preview.csv"
            )
            df = pd.read_csv(fname)
            results[name]["gpt4"][epoch] = df["fluency_score"].mean().item()
        plot_fluency_tuning(
            results, name
        )  # , save_dir=os.path.join(TUNER_EXP_DIR, name))
    print()

    outpath = os.path.join(TUNER_EXP_DIR, "all_results.yaml")
    with open(outpath, "w") as f:
        yaml.dump(results, f)
    print(f"wrote results to '{outpath}'")


def plot_fluency_tuning(
    results: dict, exp_name: str, judge: str = "gpt4", save_dir: str = TUNER_EXP_DIR
):
    """Plot fluency benchmark of LLama models across fine-tuning epochs."""

    epochs = results[exp_name][judge].keys()
    scores = results[exp_name][judge].values()
    baseline_score = results["default"]["gpt4"][-1]

    plt.clf()
    plt.title(f"Experiment {exp_name} Fluency Across Epochs")
    plt.plot(epochs, scores)
    plt.xlabel("Epoch")
    plt.ylabel("Avg. Fluency Score (5 Point Scale)")
    plt.xticks(range(0, max(epochs) + 1))
    plt.xlim(0, max(epochs))
    plt.yticks(np.arange(1.0, 5.5, 1.0))  # Label every whole integer
    # unlabeled ticks every 0.5
    plt.gca().yaxis.set_minor_locator(plt.MultipleLocator(0.5))
    plt.gca().yaxis.set_minor_formatter(plt.NullFormatter())

    # add red baseline
    plt.axhline(y=baseline_score, color="r", linestyle="--")

    fname = os.path.join(save_dir, f"{exp_name}_plot.pdf")
    plt.savefig(fname)
    print(f"wrote plot to {fname}")


def plot_fluency_baselines():
    """Boxplots of baseline Dutch fluency score distributions of LLMs of interest."""
    datas = dict()
    for nickname, fname in [
        ("GPT-4", "fluency_gpt-4-0125-preview_judged_by_gpt-4-0125-preview.csv"),
        ("GPT-3.5", "fluency_gpt-3.5-turbo-0125_judged_by_gpt-4-0125-preview.csv"),
        ("Llama-2-7b", "benchmark_chkp_-1_gpt-4-0125-preview.csv"),
        # plot best Llama-2-7B-nl as well!
        ("Llama-2-7b-nl", "full1/benchmark_chkp_0_gpt-4-0125-preview.csv"),
    ]:
        if "GPT" in nickname:
            fname = os.path.join(EXPERIMENTS_DIR, "data/synthetic_smart/v4/", fname)
        else:
            fname = os.path.join(TUNER_EXP_DIR, fname)
        df = pd.read_csv(fname)
        print(f"\n{os.path.basename(fname)}:")
        print(df["fluency_score"].describe())
        non5s = len(df[df["fluency_score"] != 5])
        print(f"non-5 scores counts: {non5s}")
        df = df.dropna(subset=["fluency_score"])
        datas[nickname] = df["fluency_score"].to_list()

    # make boxplots for each model, using nickname as label
    plt.clf()
    meanprops = dict(
        marker="o",
        markerfacecolor="red",
        markeredgecolor="red",
        linestyle="--",
        color="red",
        linewidth=2,
    )
    plt.boxplot(datas.values(), showmeans=True, meanprops=meanprops)
    plt.xticks(range(1, len(datas) + 1), datas.keys())
    plt.yticks(np.arange(1.0, 5.5, 1.0))  # Label every whole integer
    plt.gca().yaxis.set_minor_locator(plt.MultipleLocator(0.5))
    plt.gca().yaxis.set_minor_formatter(plt.NullFormatter())
    plt.xlabel("Model")
    plt.ylabel("Fluency Score (5 Point Scale)")
    fname = os.path.join(TUNER_EXP_DIR, "fluency_baselines.pdf")
    plt.savefig(fname)
    print(f"wrote plot to {fname}")


if __name__ == "__main__":
    main()
