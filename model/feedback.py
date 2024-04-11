#!/usr/bin/env python3

import argparse
import json
import pandas as pd
import os
import matplotlib.pyplot as plt

import config
import gpt
import prompts as promptlib
from prompts import SMARTFeedback, SMARTResponse
from typing import Tuple, Optional
from pydantic import ValidationError
from synthetic_smart import add_ids

logger = config.get_logger(__name__)


def main():
    parser = argparse.ArgumentParser(
        description="Provide feedback on dataset of SMART goals and plans.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--input-dir",
        "-i",
        type=str,
        required=True,
        help="Input file directory (should contain 'smart_goals.csv' file)",
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
        help="Max number of feedback generation iterations (given invalid response formats).",
    )

    args = parser.parse_args()
    config.source_dot_env()  # read api key

    assert os.path.isdir(args.input_dir)
    fname = os.path.join(args.input_dir, "smart_goals.csv")
    goals_df = pd.read_csv(fname)

    base_path = args.input_dir + f"feedback_{args.model}"
    feedback_path = base_path + ".csv"
    base_dot_path = args.input_dir + f".feedback_{args.model}"
    bkp_path = base_dot_path + ".output.json.bkp"
    if not os.path.isfile(feedback_path):
        outputs = None
        # if os.path.isfile(bkp_path):
        #     print("reloading older feedback outputs")  # e.g. to handle parse error
        #     with open(bkp_path, "r") as f:
        #         outputs = json.load(f)

        config.args_to_dict(args, fname=base_dot_path + ".config.json")
        # generate feedback, extending df
        # df = df[-4:]  # TODO for now
        # breakpoint()
        feedback_df = get_feedback(goals_df, args, bkp_path=bkp_path)
        feedback_df.to_csv(feedback_path, index=False)
        print(f"wrote '{feedback_path}'")
    else:
        print("reloading existing feedback!")
        feedback_df = pd.read_csv(feedback_path)
        # feedback_df.to_csv(feedback_path)

        # feedback_df["errors"] = feedback_df["errors"].fillna("").astype(str)
        # scores_df = pd.read_csv(scores_path)
    exit(0)

    # join feedback_df with goals_df on goal_id
    # TOOD: get plot_scores working again
    full_df = pd.merge(goals_df, feedback_df, on="goal_id")
    if len(full_df) < len(goals_df):
        logger.warning(
            f"lost {len(goals_df) - len(full_df)} rows merging feedback onto goals"
        )
    breakpoint()

    plot_scores_path = base_path + "__scores.pdf"
    plot_comparison_path = base_path + "__comparison.pdf"
    plot_scores(scores_df, fname=plot_scores_path)
    plot_comparisons(feedback_df, fname=plot_comparison_path)


def add_feedback_prompt(row: pd.Series) -> str:
    """Given row with smart goal and plan, construct prompt for feedback generation."""
    json_schema = SMARTFeedback.model_json_schema()
    draft = SMARTResponse(smart=row["smart"], plan=row["plan"])
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
    df: pd.DataFrame,
    args: argparse.Namespace,
    bkp_path: Optional[str] = None,
) -> pd.DataFrame:
    """
    Generates feedback for dataframe of smart goals and plans, returning a new dataframe with the feedback.
    Returned dataframe has columns ["goal_id", "prompt", "response"].
    """

    # feedback data
    data = {
        "goal_id": df["goal_id"].to_list(),
        "prompt": df.apply(add_feedback_prompt, axis=1).to_list(),
    }

    def validator(text: str):
        res = promptlib.parse_pydantic(text, SMARTFeedback)
        return isinstance(res, SMARTFeedback)

    model = gpt.GPTModel(args.model)
    outputs, total_price, total_calls = gpt.auto_reprompt(
        validator, args.max_retries, model, data["prompt"]
    )

    if bkp_path is not None:  # backup just in case
        with open(bkp_path, "w") as f:
            json.dump(outputs, f, indent=2)

    if total_calls > len(data["prompt"]):
        logger.warning(
            f"{total_calls - len(data['prompt'])} extra generation calls needed while processing {len(data['prompt'])} prompts"
        )

    error_indices = [i for i, x in enumerate(outputs) if x is None]
    bad_count = len(error_indices)
    if bad_count > 0:
        logger.error(f"{len(error_indices)} outputs failed to parse")

    print("\nfeedback generation summary:")
    print(f"total generation calls: {total_calls}")
    print(f"final parse errors: {len(error_indices)}, error_indices: {error_indices}")
    print(f"total price: ${total_price:.3f}")
    # assert len(error_indices) == 0
    data["response"] = outputs
    return add_ids(pd.DataFrame(data), "feedback_id")


def extract_scores_df(df: pd.DataFrame) -> pd.DataFrame:
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
