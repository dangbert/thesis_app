#!/usr/bin/env python3

import argparse
import json
import pandas as pd
import os
import matplotlib.pyplot as plt
import seaborn as sns

import config
import gpt
import prompts as promptlib
from prompts import SMARTFeedback, SMARTResponse
from typing import Optional
from synthetic_smart import add_ids

logger = config.get_logger(__name__)


def main():
    parser = argparse.ArgumentParser(
        description="Generate feedback on dataset of SMART goals and plans.",
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

    legacy_feedback_format = (
        False  # whether to request/expect feedback in SMARTFeedback model format
    )

    args = parser.parse_args()
    config.source_dot_env()  # read api key

    assert os.path.isdir(args.input_dir)
    fname = os.path.join(args.input_dir, "smart_goals.csv")
    goals_df = pd.read_csv(fname)

    base_path = args.input_dir + f"feedback_{args.model}"
    feedback_path = os.path.join(args.input_dir, "feedback.xlsx")
    base_dot_path = args.input_dir + f".feedback_{args.model}"

    bkp_path = base_dot_path + ".output.json.bkp"
    feedback_df = config.safe_read_sheet(feedback_path, args.model)

    if feedback_df is not None:
        print("reloaded existing feedback!")
    else:
        config.args_to_dict(args, fname=base_dot_path + ".config.json")
        feedback_df = get_feedback(
            goals_df, args, bkp_path=bkp_path, validate=legacy_feedback_format
        )
        assert config.safe_append_sheet(feedback_df, feedback_path, args.model)

        if legacy_feedback_format:
            feedback_df = extend_outputs(feedback_df)
            assert config.safe_append_sheet(feedback_df, feedback_path, args.model)

    if not legacy_feedback_format:
        logger.info("skipping feedback score plots")
        return

    plot_scores(feedback_df, base_path=base_path)

    goals_path = os.path.join(args.input_dir, "smart_goals.csv")
    goals_df = pd.read_csv(goals_path)
    full_df = pd.merge(goals_df, feedback_df, on="goal_id")

    # plot feedback scores with vs without intentional errors
    plot_comparisons(full_df, fname=base_path + "__comparison.pdf")


def add_feedback_prompt(row: pd.Series) -> str:
    """Given row with smart goal and plan, construct prompt for feedback generation."""
    # json_schema = SMARTFeedback.model_json_schema()
    draft = SMARTResponse(smart=row["smart"], plan=row["plan"])
    prompt = promptlib.PROMPT_SMART_FEEDBACK_TEXT_ONLY.format(
        FEEDBACK_PRINCIPLES=promptlib.FEEDBACK_PRINCIPLES,
        SMART_RUBRIC=promptlib.SMART_RUBRIC,
        learning_goal=draft.smart,
        action_plan=draft.plan,
        language="Dutch",
    )
    return prompt


def clean_attr(attr: str) -> str:
    return attr.replace("-", "_").lower()


def get_feedback(
    df: pd.DataFrame,
    args: argparse.Namespace,
    bkp_path: Optional[str] = None,
    validate: bool = False,  # whether to validate feedback against SMARTFeedback model
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

    def noop_validator(text: str):
        return True

    model = gpt.GPTModel(args.model)
    logger.info(f"validator enabled: {validate}")
    outputs, total_price, total_calls = gpt.auto_reprompt(
        validator if validate else noop_validator,
        args.max_retries,
        model,
        data["prompt"],
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


def extend_outputs(feedback_df: pd.DataFrame) -> pd.DataFrame:
    """Parse the 'response' column, splitting out into separate columns for each SMART attribute."""
    if "overall_feedback" in feedback_df.columns:
        logger.info("feedback_df already has extended columns, skipping regeneration")
        return feedback_df

    feedback_objs = [
        promptlib.parse_pydantic(text, SMARTFeedback)
        for text in feedback_df["response"]
    ]
    fdata = {}  # feedback data
    for attr in promptlib.SMART:
        attr = clean_attr(attr)
        fdata["overall_feedback"] = [obj.overall_feedback for obj in feedback_objs]
        fdata[f"feedback_{attr}"] = [
            getattr(obj, attr).feedback for obj in feedback_objs
        ]
        fdata[f"score_{attr}"] = [getattr(obj, attr).score for obj in feedback_objs]
    full_df = pd.concat([feedback_df, pd.DataFrame(fdata)], axis=1)
    return full_df


# MARK: plots
def plot_scores(feedback_df: pd.DataFrame, base_path: Optional[str] = None):
    """Plot distribution of each SMART attribute's score + correlation matrix."""
    feedback_objs = [
        promptlib.parse_pydantic(text, SMARTFeedback)
        for text in feedback_df["response"]
    ]
    scores_data = {}
    for attr in promptlib.SMART:
        attr = clean_attr(attr)
        scores_data[attr] = [getattr(obj, attr).score for obj in feedback_objs]
    scores_df = pd.DataFrame(scores_data)

    plt.clf()
    scores_df.boxplot()
    # set y-axis to 0-10, tickmarks every 0.5
    plt.yticks(range(0, 11), [f"{x:.1f}" for x in range(0, 11)])
    plt.title(f"SMART Feedback Scores (n={len(scores_df)} responses)")
    print("\nsummary of scores:")
    # create copy without ID column
    print(scores_df.describe())
    if base_path is not None:
        fname = base_path + "__scores.pdf"
        plt.savefig(fname)
        print(f"\nwrote '{fname}'")
    else:
        plt.show()

    correlations = scores_df.corr(method="pearson")
    plt.clf()
    plt.figure(figsize=(10, 8))
    sns.heatmap(correlations, annot=True, cmap="coolwarm")
    plt.title("Correlations Between SMART Feedback Scores")
    if base_path is not None:
        fname = base_path + "__corr.pdf"
        plt.savefig(fname)
        print(f"\nwrote '{fname}'")
    else:
        plt.show()


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
        print(f"\nwrote '{fname}'")
    else:
        plt.show()


if __name__ == "__main__":
    main()
