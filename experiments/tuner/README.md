## Scripts/config for using torchtune to finetune models.

* https://pytorch.org/torchtune/stable/tutorials/e2e_flow.html


usage:
````bash
export EXP_DIR=./llama2_7B # should match same var in .yaml file below
mkdir -p "$EXP_DIR/model" "$EXP_DIR/output"
tune download meta-llama/Llama-2-7b-hf  --output-dir "$EXP_DIR/model"

tune run lora_finetune_single_device --config ./llama2_7B_qlora_single_device.yaml
````


initial setup notes:
````bash
# note that the .yaml file was initially made from a modified version of a default recipe:
tune ls # view available "recipes"
tune cp llama2/7B_qlora_single_device ./llama2_7B_qlora_single_device.yaml

tune cp generation generation.yaml 
# seems we can also just copy python files from the torchtune codebase!
# tune cp generate generate.py
````


TODO: eval on validation dataset 

TODO: try to load a local python file in the config....

