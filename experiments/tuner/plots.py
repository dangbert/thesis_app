#!/usr/bin/env python3

import os
import argparse
import sys
import yaml
import matplotlib.pyplot as plt

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

TUNER_EXP_DIR = os.path.join(SCRIPT_DIR, "llama2_7B/experiments/")


def main():
    # parser = argparse.ArgumentParser(
    #     formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    # )
    # args = parser.parse_args()

    results_path = os.path.join(TUNER_EXP_DIR, "results.yaml")
    with open(results_path, "r") as f:
        results = yaml.load(f, Loader=yaml.FullLoader)

    exp_names = ["full1", "full2", "full3"]
    for name in exp_names:
        print(f"Experiment: {name}")
        plot_exp(results, name)
    print()


def plot_exp(
    results: dict, exp_name: str, judge: str = "gpt4", save_dir: str = TUNER_EXP_DIR
):
    # create lineplot with epochs 0-4 on x-axis and "Avg. Fluency Score" on y-axis

    epochs = results[exp_name][judge].keys()
    scores = results[exp_name][judge].values()
    baseline_score = results["default"]["gpt4"][-1]

    plt.clf()
    plt.plot(epochs, scores)
    plt.xlabel("Epoch")
    plt.ylabel("Avg. Fluency Score")
    plt.title(f"Experiment {exp_name} across epochs")
    plt.xticks(range(0, max(epochs) + 1))

    # add red baseline
    plt.axhline(y=baseline_score, color="r", linestyle="--")

    fname = os.path.join(TUNER_EXP_DIR, f"{exp_name}_plot.pdf")
    plt.savefig(fname)
    print(f"wrote plot to {fname}")


if __name__ == "__main__":
    main()
