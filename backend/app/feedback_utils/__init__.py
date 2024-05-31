"""Good for providing AI generated feedback to students."""

from sqlalchemy.orm import Session
from pydantic import ValidationError
import os
import pandas as pd

from .AbstractModel import AbstractModel, IPrompt, IConversation
from . import prompts
from .gpt import GPTModel

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

GOLDEN_PATH = os.path.join(SCRIPT_DIR, "golden_feedback.csv")


def build_few_shot_instructions(fname: str = GOLDEN_PATH) -> str:
    assert os.path.isfile(GOLDEN_PATH)
    df = pd.read_csv(GOLDEN_PATH)

    df.columns()
