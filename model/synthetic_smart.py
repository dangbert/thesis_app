#!/usr/bin/env python3
import argparse
import json
import random
import pandas as pd

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
        "-s",
        type=int,
        default=50,
        help="Number of samples to generate.",
    )
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
        required=True,
        default="synthetic_smart.csv",
        help="Output file name (csv) e.g. 'synthetic_smart.csv'.",
    )
    parser.add_argument(
        "--model",
        "-m",
        type=str,
        default="gpt-3.5-turbo-0125",
        help="Name of OpenAI model to use (see gpt.py).",
    )
    args = parser.parse_args()
    config.source_dot_env()  # read api key

    assert args.sample_size > 0
    assert args.output.lower().endswith(".csv")

    df = create_prompts(args)
    df.to_csv(args.output, index=False)  # verify save works before running model

    model = gpt.GPTModel(args.model)
    outputs, meta = model(list(df["prompt"]), top_p=args.top_p, json_mode=True)
    print(f"price = ${model.compute_price(meta):.3f}")

    smart, plan = [], []
    for output in outputs:
        obj = json.loads(output)
        smart.append(obj["smart"])
        plan.append(obj["plan"])

    df = df.assign(errors=df["errors"].apply(lambda x: ", ".join(x)))  # list -> string
    df = df.assign(smart=smart, plan=plan)
    df.to_csv(args.output, index=False)
    print(f"saved to '{args.output}'")


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
        data["errors"].append(smart_errors)

    df = pd.DataFrame(data)
    # sort by len(errors) and reindex
    df = df.sort_values(by="errors").reset_index(drop=True)
    return df


if __name__ == "__main__":
    main()
