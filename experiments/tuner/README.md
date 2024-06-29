## Scripts/config for using torchtune to finetune models.

* https://pytorch.org/torchtune/stable/tutorials/e2e_flow.html


### usage:

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

To upload a given model checkpoint to a HuggingFace repo, I manually created a new model repo on huggingface.co and ran the following:
    * [reference docs](https://pytorch.org/torchtune/stable/tutorials/e2e_flow.html#uploading-your-model-to-the-hugging-face-hub)

````bash
cd llama2_7B/experiments

# I choose to create a new folder with just the single checkpoint I wanted
#   but alternatatively see additional args available with: huggingface-cli upload -h
mkdir upload_tmp
cp full1/hf_model_000?_0.pt full1/config.json upload_tmp/ # copying checkpoint 0 of experiment "full1"
huggingface-cli upload dangbert/Llama-2-7b-nl . --commit-message "add full1, checkpoint 0" 

# ^if you get an authetication error, then run this first and enter a token with write access to your model's repo
huggingface-cli login
````

### initial setup steps for reproducibility:
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
