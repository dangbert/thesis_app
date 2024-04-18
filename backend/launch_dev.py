#!/usr/bin/env python3

import os
import uvicorn
import subprocess

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))


def main():
    # need to set host to make it accessible outside of container
    host = subprocess.check_output(["hostname", "-i"]).decode("utf-8").strip()
    print("running on host: {}".format(host))
    uvicorn.run("app.main:app", host=host, port=8000, reload=True)


if __name__ == "__main__":
    main()
