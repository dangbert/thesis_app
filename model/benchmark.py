import os
import json
from typing import Annotated, Tuple
from pydantic import BaseModel, create_model, conint, Field
import argparse
import pandas as pd
import prompts as promptlib


judgement_template = """
[System]
Please act as an impartial judge and evaluate the quality of the response provided by an assistant to the user question displayed below.
[Question]
{question}
[End of Question]
[Start of Assistant's Answer]
{answer}
[End of Assistant's Answer]

Now conduct your evaluation of the assistants answer to the question observed above. Consider factors such as the helpfulness, relevance, accuracy, depth, creativity, and level of detail of the response, with these factors collectively forming a "utility" score.
{additional_attributes}
Begin your evaluation by providing a short explanation. Be as objective as possible. After providing your explanation, please rate the response on scores on a scale of 1 to 10 by strictly following this json schema:
{format_schema}
For example:
{format_example}

""".strip()

# list of default attributes baked into judgement_prompt
default_attributes = ["utility"]


def build_judge_prompt(
    question: str,
    answer: str,
    other_attributes: dict[str, str] = dict(),
    # format_schema: str,
    # format_example: str,
) -> Tuple[str, BaseModel]:
    """
    Builds a prompt for evaluating the quality of an assistant's response.
    Returns the prompt and a Pydantic model for the response schema.
    See http://arxiv.org/abs/2306.05685 (Figure 6) for original inspiration.
    """
    additional_attributes = ""
    for attr, criteria in other_attributes.items():
        additional_attributes += f'\nAdditionally a "{attr}" score shall follow from the criteria:\n{criteria}\n'

    # dynamically create a Pydantic model for the response scores
    all_attributes = default_attributes + list(other_attributes.keys())
    fields = {
        attr: (Annotated[int, conint(ge=1, le=10)], Field(ge=1, le=10))
        for attr in all_attributes
    }
    AttrModel = create_model("AttrModel", **fields)
    format_example = json.dumps({attr: 5 for attr in all_attributes})
    # santity check this example fits the model (would raise exception otherwise)
    AttrModel(**json.loads(format_example))

    prompt = judgement_template.format(
        question=question,
        answer=answer,
        additional_attributes=additional_attributes,
        format_schema=AttrModel.model_json_schema(),
        format_example=format_example,
    )
    return prompt, AttrModel

def main():
    parser = argparse.ArgumentParser(
        description="Create a synthetic dataset of SMART goals and plans.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--input-goals",
        "-ig",
        type=str,
        required=True,
        help="smart_goals.csv",
    )
    parser.add_argument(
        "--input3",
        "-i3",
        type=str,
        required=True,
        help="judgements from GPT3",
    )
    parser.add_argument(
        "--input4",
        "-i4",
        type=str,
        required=True,
        help="judgements from GPT4",
    )
    args = parser.parse_args()

    assert os.path.exists(args.input_goals) and args.input_goals.endswith(".csv")
    assert os.path.exists(args.input3) and args.input3.endswith(".csv")
    assert os.path.exists(args.input4) and args.input4.endswith(".csv")

    # hardcoded for now to get ScoreModel
    feedback_path = "/Users/dan/Downloads/COURSES/thesis/repos/thesis_app/datasets/synthetic_smart/v3/feedback_gpt-3.5-turbo-0125.csv"
    feedback_df = pd.read_csv(feedback_path)
    _, ScoreModel = build_judge_prompt(question=feedback_df["prompt"][0], answer=feedback_df["response"][0], other_attributes=other_attributes)

    goals_df = pd.read_csv(args.input_goals)
    def parse_df(judge_fname: str):
        print(judge_fname)
        judge_df = pd.read_csv(judge_fname)
        objs = []
        for i, row in judge_df.iterrows():
            # print(row["response"])
            obj = promptlib.parse_pydantic(row["response"], ScoreModel)
            assert not isinstance(obj, str)
            print(obj.dict())
            objs.append(obj)
        return objs
    
    judges = {
        "judge3": parse_df(args.input3),
        "judge4": parse_df(args.input4),
    }

    attrs = ["utility", "safety"]
    data = {}
    for judge, objs in judges.items():
        for atrr in attrs:
            data[judge + "_" + atrr] = [getattr(obj, atrr) for obj in objs]

if __name__ == "__main__":
    main()