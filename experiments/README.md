## Experiments (Models, Scripts, Datasets)

See also:
* [./tuner](./tuner) for experiments on fine-tuning Llama2

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


Disclaimer: the conda environment is now deprecated in favor of poetry (as shown above)

````bash
cd .. # enter root of repo

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


````bash
# generate synthetic smart goals (into desired directory)
mkdir -p ../datasets/synthetic_smart/example
./synthetic_smart.py -o ./data/synthetic_smart/example/ --sample-size 50 -m "gpt-4-0125-preview"

# generate feedback on smart goals (and make plots)
./feedback.py -i ./data/synthetic_smart/example/ -m "gpt-4-0125-preview"
# do the same with gpt3
./feedback.py -i ./data/synthetic_smart/example/ -m "gpt-3.5-turbo-0125"

# compare feedback judgements
# see also benchmark.ipynb which is more complete!
./benchmark.py -if data/synthetic_smart/v3/smart_goals.csv -i3 data/synthetic_smart/v3/feedback_gpt-3.5-turbo-0125__judged_gpt-4-0125-preview.csv -i4 data/synthetic_smart/v3/feedback_gpt-4-0125-preview__judged_gpt-4-0125-preview.csv
````

For the other experiments with running models locally, you may first need to run `huggingface-cli login` and [enter a token from your hugging face account](https://huggingface.co/settings/tokens).


## Misc References
* [Hugging Face LLama2 docs](https://huggingface.co/docs/transformers/main/model_doc/llama2) (how to quanitize, fine-tune etc).