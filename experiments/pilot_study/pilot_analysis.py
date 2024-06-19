#!/usr/bin/env python3
"""Script for analyzing/plotting data from pilot.xlsx (see backend/dump_pilot.py)"""

import argparse
import os
import json
import sys
import glob
from typing import Union
import pandas as pd
import Levenshtein as lev
from matplotlib import pyplot as plt
import docx

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
EXPERIMENTS_DIR = os.path.realpath(os.path.join(SCRIPT_DIR, ".."))
sys.path.append(EXPERIMENTS_DIR)
import config  # noqa: E402

logger = config.get_logger(__name__)


FNAME = os.path.join(config.ROOT_DIR, "backend/pilot.xlsx")


def main():
    parser = argparse.ArgumentParser(
        description="Utils for doing analysis on pilot.xlsx data (see backend/dump_pilot.py)",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--levenshtein",
        "-l",
        action="store_true",
        help="Compute levenshtein edit distances, and plot errors",
    )
    parser.add_argument(
        "--input",
        "-i",
        type=str,
        default=FNAME,
        help="Input file (pilot.xlsx)",
    )
    parser.add_argument(
        "--dump-for-translate",
        "-dt",
        action="store_true",
        help="Create a docx file for translating text fields within pilot.xlsx",
    )
    args = parser.parse_args()

    new_fname = "pilot_lev_dist_norm.xlsx"
    if args.levenshtein:
        levenshtein(args.input, new_fname)
        plot_errors(new_fname) # could read either file here
    elif args.dump_for_translate:
        dump_for_translate(args.input)
    else:
        parser.print_help()
        exit(1)


def _get_dfs(fname: str):
    assert os.path.isfile(fname)
    a1_df = pd.read_excel(fname, sheet_name="P1", index_col=0)
    a2_df = pd.read_excel(fname, sheet_name="S1", index_col=0)
    return a1_df, a2_df


def levenshtein(fname: str, new_fname: str):
    # a1_df, a2_df = _get_dfs(fname)
    excel_file = pd.ExcelFile(fname)
    sheets = {sheet_name: excel_file.parse(sheet_name) for sheet_name in excel_file.sheet_names}
    a1_df, a2_df = sheets["P1"], sheets["S1"]

    logger.info(
        "computing normalized Levenshtein distance between ai_feedback and human_feedback."
    )
    # add column lev_dist_norm to a1df from columns 'ai_feedback' and 'human_feedback'
    a1_df["lev_dist_norm"] = a1_df.apply(
        lambda x: lev.ratio(x["ai_feedback"], x["human_feedback"]), axis=1
    )

    # TODO: consider regenerating AI feedback for S1 and comparing as a baseline
    # to see how much the AI feedback in P1 biased the final feedback
    with pd.ExcelWriter(new_fname) as writer:
        sheets["P1"] = a1_df
        sheets["S1"] = a2_df
        # preserve other arbitrary sheets
        for sheet_name, df in sheets.items():
            df.to_excel(writer, sheet_name=sheet_name, index=False)
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

# matches EvalControls.tsx
ALL_PROBLEMS = {
  'Accuracy/relevance',
  'Feedback style/tone',
  'Structure',
  'Grammar',
  'Too wordy',
  'Too short',
  'Other',
}

def plot_errors(fname: str):
    df = pd.read_excel(fname, sheet_name="anon")

    counts = {error: 0 for error in ALL_PROBLEMS}
    # get rows with review_problems
    df_filtered = df[df["review_problems"].notnull()]
    for i, row in df_filtered.iterrows():
        errors = row["review_problems"].split(";")
        for error in errors:
            counts[error] += 1
    
    total_problems = sum(counts.values())
    logger.info(f"{len(df_filtered)}/{len(df)} attempts tagged with review_problems")
    logger.info(f"{total_problems} problems reported in total (across tagged attempts)")
    
    # sort keys by value largest to smallest
    counts = {k: v for k, v in sorted(counts.items(), key=lambda item: item[1], reverse=True)}
    plt.figure()
    plt.title("LLM Feedback Error Classifications")
    plt.ylabel("Total Occurrences")
    plt.bar(counts.keys(), counts.values())
    plt.xticks(rotation=90)
    # add extra padding below for labels
    plt.subplots_adjust(
        left=0.05, right=0.95, top=0.95, bottom=0.33
    ) # https://matplotlib.org/stable/api/_as_gen/matplotlib.pyplot.subplots_adjust.html

    plot_path = "error_barplot.pdf"
    plt.savefig(plot_path)
    logger.info(f"wrote '{plot_path}'")



def dump_for_translate(fname: str, out_path: str = "pilot_translate.docx"):
    a1_df, a2_df = _get_dfs(fname)
    document = docx.Document()
    for i, df in enumerate([a1_df, a2_df]):
        document.add_paragraph(f"##### assignment {i+1} #####")
        for i, row in df.iterrows():
            text = f"\n=== {row['attempt_id']} ==="
            for key in ["attempt_goal", "attempt_plan", "ai_feedback"]:
                # val = row[key] if row[key] and isinstance(row[key], str) else "" # handle nans (float defaults)
                val = row[key] if isinstance(row[key], str) else "nan"
                text += f"\n\n## {key}:\n{val}"
            document.add_paragraph(text)
            document.add_page_break()

    document.save(out_path)
    logger.info(f"wrote '{out_path}'")


if __name__ == "__main__":
    main()
