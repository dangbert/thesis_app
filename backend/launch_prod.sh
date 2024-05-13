#!/bin/bash
set -e

SCRIPT_DIR="$(realpath "$(dirname "$0")")"

function main() {
    cd "$SCRIPT_DIR"
    ./manageDB.py --maybe-migrate

    export NUM_WORKERS="$(python3 -c 'import multiprocessing; print(multiprocessing.cpu_count() * 2 + 1)')"
    echo "setting NUM_WORKERS=$NUM_WORKERS"

    declare -a CMD=(
        "gunicorn" "app.main:app"
        "--timeout" "300"
        "--reuse-port"
        "--workers" "$NUM_WORKERS"
        "--worker-class" "uvicorn.workers.UvicornWorker"
        "--bind" "0.0.0.0:8001"
    )
    echo -e -n "launching command:\n\t${CMD[@]}\n\n"
    exec ${CMD[@]}
}


main "$@"
