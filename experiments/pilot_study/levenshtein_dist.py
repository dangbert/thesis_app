#!/usr/bin/env python3
"""Script for analyzing/plotting data from pilot.xlsx (see backend/pilot.py)"""

import argparse
import os
import json
import sys
import glob
from typing import Union
import pandas as pd
import Levenshtein as lev
from matplotlib import pyplot as plt

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
EXPERIMENTS_DIR = os.path.realpath(os.path.join(SCRIPT_DIR, ".."))
sys.path.append(EXPERIMENTS_DIR)
import config  # noqa: E402

logger = config.get_logger(__name__)


def main():
    fname = os.path.join(config.ROOT_DIR, "backend/pilot.xlsx")
    assert os.path.isfile(fname)

    a1_df = pd.read_excel(fname, sheet_name="P1", index_col=0)
    a2_df = pd.read_excel(fname, sheet_name="S1", index_col=0)

    logger.info(
        "computer normalized Levenshtein distance between ai_feedback and human_feedback."
    )
    # add column lev_dist_norm to a1df from columns 'ai_feedback' and 'human_feedback'
    a1_df["lev_dist_norm"] = a1_df.apply(
        lambda x: lev.ratio(x["ai_feedback"], x["human_feedback"]), axis=1
    )

    # TODO: consider regenerating AI feedback for S1 and comparing as a baseline
    # to see how much the AI feedback in P1 biased the final feedback
    new_fname = "pilot_lev_dist_norm.xlsx"
    with pd.ExcelWriter(new_fname) as writer:
        a1_df.to_excel(writer, sheet_name="P1")
        a2_df.to_excel(writer, sheet_name="S1")
    logger.info(f"wrote '{new_fname}'")

    plt.figure()
    plt.title("Edit Distance Between AI and Human Feedback")
    plt.ylabel("Normalized Levenshtein Distance")
    plt.violinplot(a1_df["lev_dist_norm"], showmeans=False, showmedians=True)
    # plt.gca().axes.get_xaxis().set_visible(False)
    plt.gcf().set_size_inches(4, 6)
    plt.subplots_adjust(
        left=0.2, right=0.8, top=0.8, bottom=0.2
    )  # add horizontal padding
    plt.ylim(0, 1)
    # plt.scatter([0 for _ in a1_df['lev_dist_norm']], a1_df['lev_dist_norm'], color='red', s=10)

    # x axis label as "A1"
    plt.text(
        0.5,
        -0.1,
        "Assignment 1",
        ha="center",
        va="center",
        transform=plt.gca().transAxes,
    )
    # show ticks but hide numbers
    plt.gca().axes.get_xaxis().set_visible(True)
    plt.gca().axes.get_xaxis().set_ticks([])

    plot_path = "lev_dist_norm.pdf"
    plt.savefig(plot_path)
    logger.info(f"wrote '{plot_path}'")


if __name__ == "__main__":
    main()
