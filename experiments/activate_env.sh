# source me to load existing conda env!
module purge
echo "loading modules..."
module load 2023
# for full list run `module spider conda`
module load Anaconda3/2023.07-2

ENV_NAME="thesis"
ENV_FILE="./environment.yml"

echo "activating environment '$ENV_NAME'"
source activate "$ENV_NAME"
echo -e "python3 location: '`which python3`'\n"