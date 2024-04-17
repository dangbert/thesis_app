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

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, os.pardir))
DATASETS_DIR = os.path.join(ROOT_DIR, "datasets")
ENV_PATH = os.path.join(ROOT_DIR, ".env")


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


def source_dot_env(dotenv_path: str = ENV_PATH):
    if not load_dotenv(override=True, dotenv_path=dotenv_path):
        print(f"failed to load '{dotenv_path}'")
        exit(1)


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
