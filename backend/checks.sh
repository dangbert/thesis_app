#!/bin/bash
set -e

SCRIPT_DIR="$(realpath "$(dirname "$0")")"

set -e

cd "$SCRIPT_DIR"

echo -e "\nruff format check"
ruff format --check .

echo -e "\nruff checks"
ruff check .

echo -e "\nunit tests"
pytest

echo -e "\nmypy checks"
mypy .

echo -e "\nAll checks passed!"