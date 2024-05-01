import re
import json
from pydantic import BaseModel, conint, Field, ValidationError
from typing import Annotated, Union, Any
import config

logger = config.get_logger(__name__)


class SMARTResponse(BaseModel):
    smart: str
    plan: str


class FeedbackAttr(BaseModel):
    score: Annotated[int, conint(ge=1, le=10)] = Field(
        default=None, title="Score in the range [1,10] inclusive.", ge=1, le=10
    )
    feedback: str


class SMARTFeedback(BaseModel):
    specific: FeedbackAttr
    measurable: FeedbackAttr
    action_oriented: FeedbackAttr
    relevant: FeedbackAttr
    time_bound: FeedbackAttr
    overall_feedback: str


def parseSMARTFeedback(response: str, retry: bool = False) -> SMARTFeedback:
    """
    Attempt to find the JSON substring in the response and parse it into a SMARTFeedback object.
    Raises jsonDecodeError or ValidationError on failure.
    """
    json_str = re.search(r"{.*}", response, re.DOTALL).group()

    try:
        data = json.loads(json_str)
    except json.JSONDecodeError as e:
        is_quote_error = "Expecting property name enclosed in double quotes" in str(e)
        if not retry or not is_quote_error:
            print("bad json_str:")
            print(json_str)
            raise e
        if is_quote_error:
            logger.warning(f"retrying with quote replacement: {response}")
            # hacky fix for single quotes (better to avoid this in the first place)
            tmp = response.replace("'", '"')
            return parseSMARTFeedback(tmp, retry=False)
    except ValidationError as e:
        logger.error(f"validation error: {e}")
        raise e

    # TODO: should also catch ValidationErorr here or replace this function with a call to parse_pydantic
    feedback = SMARTFeedback(**data)
    return feedback


def parse_pydantic(text: str, SomeModel, retry: bool = False) -> Union[Any, str]:
    """
    Attempt to find a JSON substring in the given text and parse it into the provided pydantic model.
    Returns string describing error on failure, or instance of SomeModel class on success.
    """
    match = re.search(r"{.*}", text, re.DOTALL)
    if match is None:
        return "no json object found in text"
    json_str = match.group()
    assert issubclass(SomeModel, BaseModel)

    try:
        data = json.loads(json_str)
    except json.JSONDecodeError as e:
        is_quote_error = "Expecting property name enclosed in double quotes" in str(e)
        if not retry or not is_quote_error:
            return f"failed to parse json string: {e}"
        if is_quote_error:
            logger.warning(f"retrying with quote replacement: {text}")
            # hacky fix for single quotes (better to avoid this in the first place)
            tmp = json_str.replace("'", '"')
            return parse_pydantic(tmp, retry=False)

    try:
        obj = SomeModel(**data)
    except ValidationError as e:
        return f"validation error: {e}"
    return obj
