## Scripts/config for using torchtune to finetune models.

* https://pytorch.org/torchtune/stable/tutorials/e2e_flow.html


````bash
export EXP_DIR=./llama2_7B # should match same var in .yaml file below
mkdir -p "$EXP_DIR/model" "$EXP_DIR/output"
tune download meta-llama/Llama-2-7b-hf  --output-dir "$EXP_DIR/model"

tune run lora_finetune_single_device --config ./llama2_7B_qlora_single_device.yaml

````

TODO: eval on validation dataset 

TODO: try to load a local python file in the config....

