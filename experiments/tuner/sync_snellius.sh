#!/bin/bash
set -e

# copy results from snellius to local computer (excluding checkpoints)
rsync -ah --progress snellius:thesis_app/experiments/tuner/llama2_7B . -L --exclude "*.pt" --exclude "*.bin"
rsync -ah --progress snellius:thesis_app/experiments/tuner/llama2_7B_chat . -L --exclude "*.pt" --exclude "*.bin"