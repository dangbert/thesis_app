#!/usr/bin/env python3

import argparse
import json
import pandas as pd
import os
import matplotlib.pyplot as plt

import config
import gpt
import prompts as promptlib
from typing import Tuple, Optional
from pydantic import ValidationError
from synthetic_smart import add_ids


def main():
    parser = argparse.ArgumentParser(
        description="Provide feedback on dataset of SMART goals and plans.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--input",
        "-i",
        type=str,
        required=True,
        help="Input file name (csv) e.g. './smart_goals.csv'",
    )
    parser.add_argument(
        "--model",
        "-m",
        type=str,
        default="gpt-3.5-turbo-0125",
        help="Name of OpenAI model to use (see gpt.py).",
    )
    parser.add_argument(
        "--max-retries",
        "-r",
        type=int,
        default=2,
        help="Max number of feedback generation retries per invalid response.",
    )

    args = parser.parse_args()
    if os.path.isdir(args.input):
        args.input = os.path.join(args.input, "smart_goals.csv")
    config.source_dot_env()  # read api key

    df = pd.read_csv(args.input)
    assert args.input.endswith(".csv")
    base_path = args.input[:-4] + "__feedback"
    feedback_path = base_path + ".csv"
    scores_path = base_path + "__scores.csv"
    bkp_path = args.input + ".output.json.bkp"

    if not os.path.isfile(feedback_path):
        outputs = None
        if os.path.isfile(bkp_path):
            print("reloading older feedback outputs")  # e.g. to handle parse error
            with open(bkp_path, "r") as f:
                outputs = json.load(f)

        config.args_to_dict(args, fname=base_path + ".config.json")
        # generate feedback, extending df
        full_df, scores_df = get_feedback(df, args, outputs=outputs)

        full_df.to_csv(feedback_path, index=False)
        print(f"wrote '{feedback_path}'")
        scores_df.to_csv(scores_path, index=False)
        print(f"wrote '{scores_path}'")
    else:
        print("reloading existing feedback!")
        full_df = pd.read_csv(feedback_path)
        full_df["errors"] = full_df["errors"].fillna("").astype(str)
        scores_df = pd.read_csv(scores_path)

    plot_scores_path = base_path + "__scores.pdf"
    plot_comparison_path = base_path + "__comparison.pdf"
    plot_scores(scores_df, fname=plot_scores_path)
    plot_comparisons(full_df, fname=plot_comparison_path)


def add_feedback_prompt(row: pd.Series) -> str:
    """Given row with smart goal and plan, construct prompt for feedback generation."""
    json_schema = promptlib.SMARTFeedback.model_json_schema()
    draft = promptlib.SMARTResponse(smart=row["smart"], plan=row["plan"])
    prompt = promptlib.PROMPT_SMART_FEEDBACK.format(
        FEEDBACK_PRINCIPLES=promptlib.FEEDBACK_PRINCIPLES,
        SMART_RUBRIC=promptlib.SMART_RUBRIC,
        SMART_EXAMPLE=promptlib.SMART_EXAMPLE,
        student_draft=draft.model_dump_json(indent=2),
        json_schema=json_schema,
    )
    return prompt


def clean_attr(attr: str) -> str:
    return attr.replace("-", "_").lower()


def get_feedback(
    df: pd.DataFrame, args: argparse.Namespace, outputs: Optional[list[str]] = None
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    df["feedback_prompt"] = df.apply(add_feedback_prompt, axis=1)
    df["errors"] = df["errors"].fillna("").astype(str)
    config.source_dot_env()  # read api key
    model = gpt.GPTModel(args.model)

    total_price = 0.0
    if outputs is not None:  # we reuse prior outputs
        assert len(df) == len(outputs)
    else:
        # generate feedback for ALL rows
        outputs, meta = model(list(df["feedback_prompt"]))
        total_price = model.compute_price(meta)
        print(f"price = ${total_price:.3f}")

    # in case json doesn't parse below lets backup these responses
    bkp_path = args.input + ".output.json.bkp"
    with open(bkp_path, "w") as f:
        json.dump(outputs, f, indent=2)

    # post process outputs
    feedback_objs: list[promptlib.SMARTFeedback] = []
    total_retries = 0
    for i, response in enumerate(outputs):
        retry = 0
        while retry < args.max_retries:
            try:
                feedback = promptlib.parseSMARTFeedback(response, retry=True)
                break
            except (json.JSONDecodeError, ValidationError) as e:
                print(e)
                feedback = None

            # TODO: consider including error context in reprompt
            retry += 1
            print(f"retry {retry} for row {i} ...")
            new_output, new_meta = model([df["feedback_prompt"][i]])
            total_price += model.compute_price(new_meta)
            response = new_output[0]
        total_retries += retry
        feedback_objs.append(feedback)

    error_indices = [i for i, x in enumerate(feedback_objs) if x is None]
    print("\nfeedback generation summary:")
    print(f"total retries: {total_retries}")
    print(f"final parse errors: {len(error_indices)}, error_indices: {error_indices}")
    print(f"total price: ${total_price:.3f}")
    assert len(error_indices) == 0

    # extract numerical scores
    scores_data = {}
    fdata = {}  # feedback data
    fdata["feedback_raw"] = outputs
    for attr in promptlib.SMART:
        attr = clean_attr(attr)
        scores_data[attr] = [getattr(obj, attr).score for obj in feedback_objs]
        fdata["overall_feedback"] = [obj.overall_feedback for obj in feedback_objs]
        fdata[f"feedback_{attr}"] = [
            getattr(obj, attr).feedback for obj in feedback_objs
        ]
        fdata[f"score_{attr}"] = [getattr(obj, attr).score for obj in feedback_objs]
    scores_df = add_ids(pd.DataFrame(scores_data))

    full_df = pd.concat([df, pd.DataFrame(fdata)], axis=1)
    return full_df, scores_df


# MARK: plots
def plot_comparisons(full_df: pd.DataFrame, fname: Optional[str] = None):
    """
    Compare scores on basis of intentional errors in smart goal / plan
    """
    with_err = {}
    without_err = {}
    plt.clf()
    fig, axs = plt.subplots(
        1, len(promptlib.SMART), figsize=(len(promptlib.SMART) * 5, 5)
    )  # Adjust figsize for better visibility
    for i, attr in enumerate(promptlib.SMART):
        has_error = full_df["errors"].str.contains(attr)
        attr = clean_attr(attr)
        key = f"score_{attr}"
        with_err[attr] = full_df.loc[has_error == True, key].tolist()
        without_err[attr] = full_df.loc[has_error == False, key].tolist()
        assert len(with_err[attr]) + len(without_err[attr]) == len(full_df)

        axs[i].boxplot([without_err[attr], with_err[attr]], positions=[0.9, 1.1])
        axs[i].set_title(
            f"{attr} (n={len(without_err[attr])} without vs n={len(with_err[attr])} with error)"
        )
        axs[i].set_xticks([0.9, 1.1])
        axs[i].set_xticklabels(["No", "Yes"])
        axs[i].set_xlabel("Intentional Error")
        axs[i].set_ylabel("Values")
        axs[i].set_yticks(range(0, 11))
        axs[i].set_yticklabels([f"{x:.1f}" for x in range(0, 11)])
        axs[i].grid(True)

    fig.suptitle("Scores With vs Without Intentional Errors", fontsize=16)
    plt.tight_layout()
    if fname is not None:
        plt.savefig(fname)
        print(f"wrote '{fname}'")
    else:
        plt.show()


def plot_scores(scores_df: pd.DataFrame, fname: Optional[str] = None):
    plt.clf()
    scores_df.drop("ID", axis=1).boxplot()
    # set y-axis to 0-10, tickmarks every 0.5
    plt.yticks(range(0, 11), [f"{x:.1f}" for x in range(0, 11)])
    plt.title(f"SMART Feedback Scores (n={len(scores_df)} responses)")
    print("\nsummary of scores:")
    # create copy without ID column
    print(scores_df.drop("ID", axis=1).describe())
    if fname is not None:
        plt.savefig(fname)
        print(f"wrote '{fname}'")
    else:
        plt.show()


if __name__ == "__main__":
    main()
