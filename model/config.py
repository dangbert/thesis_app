import os
import sys
from dotenv import load_dotenv
import argparse
import subprocess
from typing import Optional
import json

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, os.pardir))
DATASETS_DIR = os.path.join(ROOT_DIR, "datasets")
ENV_PATH = os.path.join(ROOT_DIR, ".env")


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
