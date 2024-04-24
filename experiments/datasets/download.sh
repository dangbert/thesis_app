#!/bin/bash

set -e

SCRIPT_DIR="$(realpath "$(dirname "$0")")"

function main() {
  cd "$SCRIPT_DIR"

  TARGET="MMLU"
  if ! [ -d "$TARGET" ]; then
    # MMLU https://github.com/hendrycks/test
    wget https://people.eecs.berkeley.edu/~hendrycks/data.tar
    tar -xvf data.tar && mv data "$TARGET" && rm -f data.tar
  else
    echo -e "$TARGET already downloaded!\n"
  fi

  TARGET="PeerRead"
  if ! [ -d "$TARGET" ]; then
    git clone git@github.com:allenai/PeerRead.git "$TARGET"
    #cd "$TARGET" && ./setup.sh && cd -
  else
    echo -e "$TARGET already downloaded!\n"
  fi
}

main "$@"
