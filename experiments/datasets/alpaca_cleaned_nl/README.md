# [alpaca-cleaned-nl](https://huggingface.co/datasets/dangbert/alpaca-cleaned-nl)

This folder contains the code used to translate a sample of the [aplaca-cleaned](https://huggingface.co/datasets/yahma/alpaca-cleaned) dataset to Dutch, inspired by [this article](https://towardsdatascience.com/creating-a-dutch-question-answering-machine-learning-model-3b666a115be3).


````bash
# download original alpaca-cleaned dataset and report some stats about it
./manage.py

# translate up to 500 samples total (resumes from previous run if applicable)
./manage.py --translate --max-samples 500
````