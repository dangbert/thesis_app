import json
from typing import Annotated, Tuple
from pydantic import BaseModel, create_model, conint, Field

judgement_template = """
[System]
Please act as an impartial judge and evaluate the quality of the response provided by an assistant to the user question displayed below.
Your evaluation should consider factors such as the helpfulness, relevance, accuracy, depth, creativity, and level of detail of the response, with these factors collectively forming a "utility" score.
{additional_attributes}
Begin your evaluation by providing a short explanation. Be as objective as possible. After providing your explanation, please rate the response on scores on a scale of 1 to 10 by strictly following this json schema:
{format_schema}
For example:
{format_example}

[Question]
{question}
[End of Question]

[Start of Assistant's Answer]
{answer}
[End of Assistant's Answer]
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
