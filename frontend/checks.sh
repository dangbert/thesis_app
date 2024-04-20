#!/bin/sh
# validate the codebase with linting etc
# run with -y to automatically fix issues

set -e

SCRIPT_DIR="$(realpath "$(dirname "$0")")"

function main() {
    nx run frontend:test
    nx run frontend:lint

    # ensure production build is possible
    nx run frontend:build:production
}

main "$@"
