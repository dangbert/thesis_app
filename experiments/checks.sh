#!/bin/bash
set -e

script_dir="$(realpath "$(dirname "$0")")"
cd "$script_dir"

echo -e "\nruff format check"
ruff format --check .

echo -e "\nruff checks"
ruff check .

echo -e "\nunit tests"
pytest

echo -e "\nmypy checks"
mypy .

echo -e "\nall checks passed!"