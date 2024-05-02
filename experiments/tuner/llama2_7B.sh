#!/bin/bash
# https://pytorch.org/torchtune/stable/tutorials/qlora_finetune.html
set -e

CHKP_DIR=/tmp/checkpoints2
mkdir -p "$CHKP_DIR"

tune download meta-llama/Llama-2-7b-hf  --output-dir $CHKP_DIR #\

# tune cp llama2/7B_qlora_single_device llama2_7B_qlora_single_device.yml
tune run lora_finetune_single_device \
  --config ./llama2_7B_qlora_single_device.yaml \
  checkpointer.checkpoint_dir=$CHKP_DIR \
  tokenizer.path=$CHKP_DIR/tokenizer.model \
  checkpointer.output_dir=$CHKP_DIR

exit 0

####### llama3 WIP
# CHKP_DIR=/tmp/checkpoints3
# NUM_GPUS=1
# tune download  meta-llama/Meta-Llama-3-8B  --output-dir $CHKP_DIR

# tune run --nproc_per_node $NUM_GPUS full_finetune_distributed --config llama3_8B_full.yaml \
#   checkpointer.checkpoint_dir=$CHKP_DIR \
#   tokenizer.path=$CHKP_DIR/tokenizer.model \
#   checkpointer.output_dir=$CHKP_DIR

# exit 0

#--hf-token <ACCESS TOKEN>

tune run lora_finetune_single_device \
  --config llama2/7B_lora_single_device \
  checkpointer.checkpoint_dir=$CHKP_DIR \
  tokenizer.path=$CHKP_DIR/tokenizer.model \
  checkpointer.output_dir=$CHKP_DIR
