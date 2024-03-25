import pytest
import json
import re
import model.prompts as promptlib
from pydantic import ValidationError


def test_SMARTFeedback_parse():
    response = """
    asdfdafs lk adsfaf
    {
    "specific": {
        "score": 10,
        "feedback": "lorum ipsum"
    },
    "measurable": {
        "score": 10,
        "feedback": "lorum ipsum"
    },
    "action_oriented": {
        "score": 10,
        "feedback": "lorum ipsum"
    },
    "relevant": {
        "score": 10,
        "feedback": "lorum ipsum"
    },
    "time_bound": {
        "score": 10,
        "feedback": "lorum ipsum"
    },
    "overall_feedback": "lorum ipsum"
    }
    """

    # shouldn't raise an error
    # Extract JSON substring using regular expressions
    json_str = re.search(r"{.*}", response, re.DOTALL).group()
    obj = promptlib.parseSMARTFeedback(response)

    with pytest.raises(json.JSONDecodeError):
        promptlib.parseSMARTFeedback(response[:-20])

    with pytest.raises(ValidationError):
        promptlib.parseSMARTFeedback(response.replace("10", '"hi"'))

    with pytest.raises(ValidationError):
        promptlib.parseSMARTFeedback(response.replace("10", "11"))
