#!/usr/bin/env python3
"""Generates synethetic SMART goals using a GPT model, writing them to a csv."""

import argparse
import json
import random
import pandas as pd
import os

import config
import gpt
import prompts as promptlib


def main():
    parser = argparse.ArgumentParser(
        description="Create a synthetic dataset of SMART goals and plans.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--sample-size",
        "-n",
        type=int,
        default=50,
        help="Number of samples to generate.",
    )
    # parser.add_argument(
    #     "--seed",
    #     type=int,
    #     default=42,
    #     help="Random seed",
    # )
    parser.add_argument(
        "--top-p",
        "-p",
        type=float,
        default=0.65,
        help="Temperature-like control for higher diversity.",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=str,
        default=os.path.join(config.DATASETS_DIR, "synthetic_smart", "smart_goals.csv"),
        help="Output file name (csv) e.g. 'smart_goals.csv' or folder path.",
    )
    parser.add_argument(
        "--model",
        "-m",
        type=str,
        default="gpt-3.5-turbo-0125",
        help="Name of OpenAI model to use (see gpt.py).",
    )
    args = parser.parse_args()
    # config.set_seed(args.seed)
    config.source_dot_env()  # read api key

    assert args.sample_size > 0
    if os.path.isdir(args.output):
        args.output = os.path.join(args.output, "smart_goals.csv")
    assert not os.path.isfile(args.output), f"refusing to overwrite '{args.output}'"
    assert args.output.endswith(".csv")
    base_path = args.output[:-4]

    print(f"\ncreating {args.sample_size} prompts... ", flush=True)
    df = create_prompts(args)
    df.to_csv(args.output, index=False)  # verify save works before running model
    config.args_to_dict(args, fname=base_path + ".config.json")  # document config

    print(f"\ngenerating {args.sample_size} outputs... ", flush=True)
    model = gpt.GPTModel(args.model)
    outputs, meta = model(list(df["prompt"]), top_p=args.top_p, json_mode=True)
    print(f"price = ${model.compute_price(meta):.3f}")

    print("\npost processing... ", flush=True)
    # in case json doesn't parse below lets backup these responses
    bkp_name = args.output + ".output.json.bkp"
    with open(bkp_name, "w") as f:
        json.dump(outputs, f, indent=2)

    smart, plan = [], []
    for output in outputs:
        obj = json.loads(output)
        smart.append(obj["smart"])
        plan.append(obj["plan"])

    df = df.assign(response=outputs, smart=smart, plan=plan)
    df.to_csv(args.output, index=False)
    print(f"saved to '{args.output}'")
    os.remove(bkp_name)


def create_prompts(args):
    data = {
        "skill": [],
        "prompt": [],
        "tone": [],
        "errors": [],
    }

    for _ in range(args.sample_size):
        skill = random.choice(list(promptlib.SKILLS.keys()))
        tone = random.choice(promptlib.TONES)
        skill_description = promptlib.SKILLS[skill]

        smart_errors = []
        # for extra diversity, ask for a specific word to be included in the response
        extra = f"And incorporate the word '{random.choice(promptlib.EDUCATION_WORDS)}' into your response. "
        if random.randint(0, 1) == 0:
            # randomly make a few errors in SMART formulation
            num_errors = random.choices([1, 2, 3], weights=[0.5, 0.35, 0.15])[0]
            smart_errors = random.sample(promptlib.SMART, num_errors)
            extra += f"Also intentionally formulate your SMART goal/plan such that the following attributes are NOT adherent to the SMART formulation: {', '.join(smart_errors)}."

        prompt = promptlib.PROMPT_SYNTHETIC_SMART.format(
            SMART_RUBRIC=promptlib.SMART_RUBRIC,
            SMART_EXAMPLE=promptlib.SMART_EXAMPLE,
            skill=skill,
            skill_description=skill_description,
            tone=tone,
            extra=extra,
        )
        data["skill"].append(skill)
        data["tone"].append(tone)
        data["prompt"].append(prompt)
        smart_errors.sort(key=lambda x: promptlib.SMART.index(x))
        # delimit by semicolon instead of storing as list
        data["errors"].append(";".join(smart_errors))

    df = pd.DataFrame(data)
    # sort by len(errors) and reindex
    df = df.sort_values(by="errors").reset_index(drop=True)
    return add_ids(df, "goal_id")


def add_ids(df: pd.DataFrame, name: str) -> pd.DataFrame:
    assert name not in df.columns
    goal_ids = [config.create_id() for _ in range(len(df))]
    df.insert(0, name, goal_ids)
    return df


if __name__ == "__main__":
    main()
