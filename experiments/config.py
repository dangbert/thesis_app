import os
import sys
import time
from dotenv import load_dotenv
import argparse
import subprocess
from typing import Optional
import logging
import json
from haikunator import Haikunator
import torch
from contextlib import contextmanager
from pydantic_settings import BaseSettings, SettingsConfigDict
import pandas as pd
from typing import Union

EXPERIMENTS_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.abspath(os.path.join(EXPERIMENTS_DIR, os.pardir))
DATASETS_DIR = os.path.join(EXPERIMENTS_DIR, "data")
# .env file for loading experiments secrets and config (see Settings class below)
ENV_PATH = os.path.join(EXPERIMENTS_DIR, ".env")


MODEL_NICKNAMES = {
    "gpt-4-0125-preview": "GPT-4",
    "gpt-3.5-turbo-0125": "GPT-3.5",
}


def get_logger(name: str, level: Optional[str] = None):
    # Configure the formatter
    formatter = logging.Formatter(
        "[%(asctime)s] %(levelname)s [%(name)s:%(lineno)s] %(message)s"
    )

    log_levels = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL,
    }
    # Get the LOG_LEVEL from environment, default to 'INFO' if not found

    # Set the logging level
    if level is None:
        level = os.environ.get("LOG_LEVEL", "INFO").upper()
        try:
            level = log_levels[level]
        except KeyError:
            raise ValueError(f"Invalid log level: {level}")

    # Configure the handler and set the formatter
    handler = logging.StreamHandler()
    handler.setFormatter(formatter)

    # Get the package's logger (replace 'my_package' with the actual package name)
    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.addHandler(handler)
    return logger


logger = get_logger(__name__)


def source_dot_env(dotenv_path: str = ENV_PATH):
    logger.debug(f"loading '{dotenv_path}'")
    if not load_dotenv(override=True, dotenv_path=dotenv_path):
        print(f"failed to load '{dotenv_path}'")
        exit(1)


class Settings(BaseSettings):
    model_config = SettingsConfigDict()
    deepl_api_key: str
    openai_api_key: str
    wandb_entity: str
    wandb_project: str  # e.g. "huggingface"


def get_settings(dotenv_path: Optional[str] = ENV_PATH) -> Settings:
    if dotenv_path is not None:
        source_dot_env(dotenv_path)
    return Settings()


def set_seed(seed):
    """
    Function for setting the seed for reproducibility.
    """
    import numpy as np
    import torch

    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed(seed)
        torch.cuda.manual_seed_all(seed)
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False


def args_to_dict(
    args: argparse.Namespace,
    other_data: Optional[dict] = {},
    fname: Optional[str] = None,
) -> dict:
    """Document config used to run a given script by writing to a json file."""
    data = {
        "cmd": " ".join(sys.argv),
        "args": vars(args),
        "git_hash": get_git_hash(),
        **other_data,
    }

    if fname is not None:
        with open(fname, "w") as f:
            json.dump(data, f, indent=2)
    return data


def get_git_hash():
    """Get current git hash of repo."""
    return (
        subprocess.check_output(["git", "rev-parse", "--verify", "HEAD", "--short"])
        .decode("utf-8")
        .strip()
    )


def create_id(token_length: int = 2):
    """Create a humany-friendly UUID."""
    return Haikunator().haikunate(token_length=token_length)


def get_device() -> str:
    """Returns the device for PyTorch to use."""
    device = "cpu"
    if torch.cuda.is_available():
        device = "cuda"
    # mac MPS support: https://pytorch.org/docs/stable/notes/mps.html
    elif torch.backends.mps.is_available():
        if not torch.backends.mps.is_built():
            print(
                "MPS not available because the current PyTorch install was not built with MPS enabled."
            )
        else:
            device = "mps"
    return device


@contextmanager
def TaskTimer(task_name: str, verbose: bool = True):
    """Reports the time a given section of code takes to run."""
    try:
        start_time = time.perf_counter()
        if verbose:
            print(f"\nstarting '{task_name}'...", flush=True)
        yield  # This is where your block of code will execute
    finally:
        dur = time.perf_counter() - start_time
        dur_str = f"{(dur):.2f} secs"
        if dur > 60:
            dur_str = f"{(dur/60):.2f} min"
        if verbose:
            print(f"'{task_name}' complete in {dur_str}!", flush=True)


def safe_append_sheet(
    df: pd.DataFrame,
    sheet_name: str,
    fname: str,
    prompt_overwrite: bool = False,
    verbose: bool = True,
) -> bool:
    """
    Helper function to add a sheet to a (possibly existing) Excel file.
    Returns true on success, false otherwise.
    """
    assert fname.endswith(".xlsx"), f"not a valid Excel file: '{fname}'"

    if not os.path.exists(fname):  # write new file
        with pd.ExcelWriter(fname) as writer:
            df.to_excel(writer, sheet_name=sheet_name, index=False)
        return True

    # append to existing file
    # read existing sheets
    excel_file = pd.ExcelFile(fname)
    sheets = {
        sheet_name: excel_file.parse(sheet_name)
        for sheet_name in excel_file.sheet_names
    }

    if sheet_name in sheets and prompt_overwrite:
        if not prompt_yes_no(f"overwrite sheet '{sheet_name}' in '{fname}'?"):
            return False

    sheets[sheet_name] = df
    with pd.ExcelWriter(fname) as writer:
        for sheet_name, df in sheets.items():
            df.to_excel(writer, sheet_name=sheet_name, index=False)
    if verbose:
        logger.info(f"wrote '{fname}'")
    return True


def safe_read_sheet(
    fname: str, sheet_name: Optional[str] = None
) -> Union[pd.DataFrame, None]:
    """Helper to read a single sheet from an Excel file, returning None if sheet not found."""
    try:
        if fname.endswith(".csv"):
            assert sheet_name is None
            return pd.read_csv(fname)

        assert fname.endswith(".xlsx")
        assert sheet_name is not None
        return pd.read_excel(fname, sheet_name)

    except FileNotFoundError:
        return None
    except ValueError as e:
        if str(e).startswith("Worksheet named") and str(e).endswith("not found"):
            return None
        raise e


def prompt_yes_no(question: str) -> bool:
    """
    returns the response to a y/n question prompt (reprompts until user provides a valid response)
    """
    val = ""
    while val not in ["y", "yes", "n", "no"]:
        val = input(f"{question} (y/n) > ").strip().lower()
    return val in ["y", "yes"]


# props for showing mean on boxplot
MEANPROPS = dict(
    marker="o",
    markerfacecolor="red",
    markeredgecolor="red",
    linestyle="--",
    color="red",
    linewidth=2,
)
