import os
from dotenv import load_dotenv

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, os.pardir))
ENV_PATH = os.path.join(ROOT_DIR, ".env")


def source_dot_env(dotenv_path: str = ENV_PATH):
    if not load_dotenv(override=True, dotenv_path=dotenv_path):
        print(f"failed to load '{dotenv_path}'")
        exit(1)
