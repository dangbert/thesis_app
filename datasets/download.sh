#!/bin/bash

set -e

SCRIPT_DIR="$(realpath "$(dirname "$0")")"

function main() {
  cd "$SCRIPT_DIR"

  if ! [ -d MMLU ]; then
    # MMLU https://github.com/hendrycks/test
    wget https://people.eecs.berkeley.edu/~hendrycks/data.tar
    tar -xvf data.tar && mv data MMLU && rm -f data.tar
  else
    echo "MMLU already downloaded!"
  fi
}

main "$@"
