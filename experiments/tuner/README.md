## Scripts/config for using torchtune to finetune models.

* https://pytorch.org/torchtune/stable/tutorials/e2e_flow.html


usage:
````bash
export EXP_DIR=./llama2_7B # should match same var in .yaml file below
mkdir -p "$EXP_DIR/model" "$EXP_DIR/output"
tune download meta-llama/Llama-2-7b-hf  --output-dir "$EXP_DIR/model"

# start finetuning using my custom code:
# export WANDB_MODE=offline # optionally disable wandb logging
EXP_NAME=changeme tune run recipes/lora_finetune_single_device.py --config ./llama2_7B_qlora_single_device.yaml
# original code:
#tune run lora_finetune_single_device --config ./llama2_7B_qlora_single_device.yaml

# generate output using finetuned model on a given prompt
EXP_NAME=changeme tune run ./recipes/generate.py --config ./generation.yaml CHKP_NUM=3 benchmark_fluency=false prompt="Vertel me een kort verhaal over de dag van een student die aan zijn scriptie werkt."

# benchmark fluency of a given model at desired checkpoint
EXP_NAME=changeme tune run ./recipes/generate.py --config ./generation.yaml CHKP_NUM=3 benchmark_fluency=true benchmark_judge=gpt-3.5-turbo-0125 #gpt-4-0125-preview
````


initial setup steps for reproducibility:
````bash
# note that the .yaml file was initially made from a modified version of a default recipe:
tune ls # view available "recipes"
tune cp llama2/7B_qlora_single_device ./llama2_7B_qlora_single_device.yaml

mkdir -p recipes

tune cp generation generation.yaml 
# seems we can also just copy python files from the torchtune codebase!
tune cp generate recipes/generate.py
tune cp lora_finetune_single_device recipes/lora_finetune_single_device.py
````


TODO: eval on validation dataset 

TODO: try to load a local python file in the config....

