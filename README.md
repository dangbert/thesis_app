# Thesis

This repo corresponds to my VU A.I. Master's thesis project.

## Setup / Usage

### Website

For instructions on running the website locally see [./docker/README.md](./docker/README.md)


For instructions on how to deploy the ezfeedback site for production use, see [./terraform/README.md](./terraform/README.md)!

### Experiments
Install dependencies:
````bash
cd experiments/
pip install virtualenv
virtualenv .venv
. .venv/bin/activate

# install poetry project (defined by pyproject.toml)
pip install poetry
poetry install
````

For info on generating synthetic smart goals / and benchmarking feedback, see [./experiments/README.md](./experiments/README.md)


<details>
<summary>Show Snellius server specific directions</summary>
Note for the commands below, if you're not running on a [slurm server](https://slurm.schedmd.com/overview.html) then use `bash` in place of `sbatch`


Disclaimer: the conda environment is now (somewhat) deprecated in favor of poetry...

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

