#!/bin/bash
# validate the codebase with linting etc
# run with -y to automatically fix issues

set -e

SCRIPT_DIR="$(realpath "$(dirname "$0")")"

# allow unused imports for now
RUFF_IGNORES=(
  --ignore=F401
)

function main() {
  RAN=0
  while getopts "hy" arg; do
    case $arg in
      y)
        fix
        exit 0
        ;;
      h)
        usage
        exit 0
        ;;
      *)
        echo "unknown args provided"
        usage
        exit 1
        ;;
    esac
  done

  # default behavior
  check
}

function check() {
  cd "$SCRIPT_DIR"
  echo -e "running ruff check..."
  ruff check . "${RUFF_IGNORES[@]}"

  echo -e "\n\nrunning mypy..."
  mypy .
}

function fix() {
  echo "running ruff --fix"
  ruff --fix "${RUFF_IGNORES[@]}"

  echo -e "\n\nrunning ruff format"
  ruff format
}

function usage() {
    SCRIPT_NAME="$(basename "$0")"
    #echo -e "Script for...."
    echo -e "\nUSAGE:"
    #echo -e "\tmanage.sh [--export] [--import] [--anki_sync] [--bridge] [--prune] [--renew] [--help]"
    echo -e "\t$SCRIPT_NAME [-y] [-h]\n"
    echo -e "\t$SCRIPT_NAME       # report errors in code"
    echo -e "\t$SCRIPT_NAME -y    # automatically fix errors when possible and reformat code"
    echo -e "\t$SCRIPT_NAME -h    # print this help message and exit"
}


main "$@"
