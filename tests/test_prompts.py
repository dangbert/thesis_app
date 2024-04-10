import pytest
import json
import model.prompts as promptlib
from model.prompts import SMARTFeedback
import model.benchmark as benchmark
from pydantic import ValidationError, BaseModel


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
    _ = promptlib.parseSMARTFeedback(response)

    with pytest.raises(json.JSONDecodeError):
        promptlib.parseSMARTFeedback(response[:-20])

    with pytest.raises(ValidationError):
        promptlib.parseSMARTFeedback(response.replace("10", '"hi"'))

    with pytest.raises(ValidationError):
        promptlib.parseSMARTFeedback(response.replace("10", "11"))

    # handles single quotes
    single_quote_res = """
    Overall, the student has shown a good understanding of crafting a SMART goal and action plan, with a focus on enhancing their innovation skills in presentations. Adding a specific timeframe for achieving the goal would further strengthen their plan.

{'specific': {'score': 8, 'feedback': 'The goal is specific and well-defined.'}, 
 'measurable': {'score': 8, 'feedback': 'The goal is measurable through the use of storytelling techniques, interactive elements, and visual aids.'}, 
 'action_oriented': {'score': 8, 'feedback': 'Concrete actions are outlined in the action plan.'}, 
 'relevant': {'score': 7, 'feedback': 'The goal is relevant to enhancing innovation skills in presentations.'}, 
 'time_bound': {'score': 6, 'feedback': 'Consider adding a specific timeframe for achieving the goal.'}, 
 'overall_feedback': 'Well done on formulating a SMART goal and action plan. Consider adding a timeframe to make it even more effective.'}
    """

    with pytest.raises(json.JSONDecodeError):
        # single quoted json is bad
        promptlib.parseSMARTFeedback(single_quote_res)

    # hacky workaround test
    _ = promptlib.parseSMARTFeedback(single_quote_res, retry=True)


def test_parse_pydantic():
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

    def expect_error(res, expect: bool):
        if expect:
            assert isinstance(res, str)
        else:
            assert issubclass(type(res), BaseModel)

    # shouldn't give error
    expect_error(promptlib.parse_pydantic(response, SMARTFeedback), False)

    # give errors
    expect_error(promptlib.parse_pydantic(response[:-20], SMARTFeedback), True)
    expect_error(
        promptlib.parse_pydantic(response.replace("10", '"hi"'), SMARTFeedback), True
    )
    expect_error(
        promptlib.parse_pydantic(response.replace("10", "11"), SMARTFeedback), True
    )


def test_build_judgement_prompt():
    question = "what time is it"
    answer = "don't ask me that"
    prompt, AttrModel = benchmark.build_judgement_prompt(question, answer)
    assert isinstance(prompt, str)
    assert issubclass(AttrModel, BaseModel)

    # map additional attributes to their criteria
    other_attributes = {
        "safety": promptlib.FEEDBACK_PRINCIPLES,
        "funny": "what does it mean to be funny?",
    }

    prompt, AttrModel = benchmark.build_judgement_prompt(
        question, answer, other_attributes
    )
