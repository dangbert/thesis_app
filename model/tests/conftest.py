import os
import sys

TEST_DIR = os.path.abspath(os.path.dirname(__file__))


def pytest_sessionstart():
    """Runs once before all tests start."""
    # apprent parent directory to sys.path (so imports like `import config` in prompts.py work)
    sys.path.append(os.path.join(TEST_DIR, ".."))
