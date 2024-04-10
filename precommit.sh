#!/bin/bash
set -e

SCRIPT_DIR="$(realpath "$(dirname "$0")")"

function main() {
    cd "$SCRIPT_DIR"

    echo -e "ensuring terraform format..."
    terraform fmt -recursive terraform/

    echo -e "\ncalling checks.sh"
    ./checks.sh

    echo -e "\nall done!"
}


main "$@"
