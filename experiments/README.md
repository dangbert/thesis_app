## Experiments (Models, Scripts, Datasets)

See also:
* [./tuner](./tuner) for experiments on fine-tuning Llama2.
  * [./jobs/tuner.job](./jobs/tuner.job) documents how fine-tuning experiments and fluency benchmarks were ran (see commented out code).

* [./data/alpaca_cleaned_nl](./data/alpaca_cleaned_nl) for the (machine translated) Dutch instruction fine-tuning dataset, [alpaca-cleaned-nl](https://huggingface.co/datasets/dangbert/alpaca-cleaned-nl)

* [Microsoft promptflow repo for this project](https://github.com/madiepev/aistudio-feedback-generation)


### setup
Install dependencies:

````bash
cd experiments/
pip install virtualenv
virtualenv .venv
. .venv/bin/activate

# install poetry project (defined by pyproject.toml)
pip install poetry
poetry install

# if your computer has a GPU and you want to run GPU-dependendent experiments:
poetry install -E gpu

# copy template config file for secrets and project config
#   (see experiments/config.py for more info)
cp .env.sample .env
# ^now edit the .env file as needed (e.g. add your OpenAI API key)
````

<details>
<summary>Show Snellius server specific directions</summary>
Note for the commands below, if you're not running on a [slurm server](https://slurm.schedmd.com/overview.html) then use `bash` in place of `sbatch`


Disclaimer: the conda environment is now deprecated in favor of poetry (as shown above).  The finetuning job, tuner.job, uses this approach.

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
</details>


### usage


Note: you can replace the "v4" path in the example commands below with a path to a folder containing your own smart_goals.csv

````bash
# generate synthetic smart goals (into desired directory)
mkdir -p ../datasets/synthetic_smart/v4
./synthetic_smart.py -o ./data/synthetic_smart/v4/ --sample-size 50 -m gpt-4-0125-preview

# generate feedback on smart goals (creates/modifies feedback.xlsx in input folder each time you call)
#   you can replace 'example' with 'v4' below
./feedback.py -i ./data/synthetic_smart/v4/ -m gpt-4-0125-preview
#   do the same with gpt3
./feedback.py -i ./data/synthetic_smart/v4/ -m gpt-3.5-turbo-0125

# now benchmark generated feedback.xlsx, comparing models:
./benchmark.py -i data/synthetic_smart/v4/ -m gpt-4-0125-preview
````

For the other experiments with running models locally, you may first need to run `huggingface-cli login` and [enter a token from your hugging face account](https://huggingface.co/settings/tokens).


## Misc References
* [Hugging Face LLama2 docs](https://huggingface.co/docs/transformers/main/model_doc/llama2) (how to quanitize, fine-tune etc).