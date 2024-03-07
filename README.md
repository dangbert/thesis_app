# Thesis

This repo corresponds to my VU A.I. Master's thesis project.

## Setup / Usage

Note for the commands below, if you're not running on a [slurm server](https://slurm.schedmd.com/overview.html) then use `bash` in place of `sbatch`

````bash
# create conda environment
# (if already existing, the environment is updated to be consistent with ./environment.yml)
sbatch jobs/install_env.yml

# now you can activate the conda environment:
source activate thesis
# or if on slurm:
source activate_env.sh

# not currently working:
# launch jupyter notebook server (useful on slurm)
sbatch jobs/launch_jupyter.job
````

## References
* [Hugging Face LLama2 docs](https://huggingface.co/docs/transformers/main/model_doc/llama2) (how to quanitize, fine-tune etc).