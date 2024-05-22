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

# check if arg --skip-mypy
if [ "$1" == "-n" ]; then
    echo -e "\n-n flag detected, skipping mypy checks"
else
    echo -e "\nmypy checks"
    mypy . #--cache-dir=/dev/null
fi
echo -e "\nall checks passed!"