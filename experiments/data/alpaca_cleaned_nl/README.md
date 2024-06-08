# [alpaca-cleaned-nl](https://huggingface.co/datasets/dangbert/alpaca-cleaned-nl)

This folder contains the code used to translate a sample of the [aplaca-cleaned](https://huggingface.co/datasets/yahma/alpaca-cleaned) dataset to Dutch, inspired by [this article](https://towardsdatascience.com/creating-a-dutch-question-answering-machine-learning-model-3b666a115be3).


````bash
./manage.py -h # view full options/help

# download original alpaca-cleaned dataset and report some stats about it
./manage.py --download yahma/alpaca-cleaned alpaca-cleaned.nl

# do the same for the latest published alpaca-cleaned-nl
./manage.py --download dangbert/alpaca-cleaned-nl translated_dataset.jsonl

# translate a desired number of samples with DeepL API (resumes from previous run if applicable)
./manage.py --translate --max-samples 500

# afterwards you can upload the translated dataset to hugging face:
huggingface-cli login # enter a token with write acesss to the dataset https://huggingface.co/settings/tokens
./manage.py --upload ./translated_dataset.jsonl
````

### Docx Translations
You can also serialize a portion of the alpaca-cleaned dataset to a word file which you can then translate with DeepL by uploading the document. I found that only about 50 samples could be translated at a time without an error, and sometimes there was still an error and so I just skipped over that sample batch and dumped/translated the next 50.  But in theory you're supposed to be able to translate up to 1 Million characters at a time if you have a DeepL pro plan...
* [info/limits here](https://www.deepl.com/en/features/document-translation/word), [API limit](https://developers.deepl.com/docs/resources/usage-limits#maximum-upload-limits-per-document-format)
* [page to upload docx for translation](https://www.deepl.com/translator/files).

````bash
# for example, serialize/dump samples from alpaca-cleaned:
#   (e.g. if you already translated 600 samples with the API)
mkdir /tmp/converted # create a directory to work out of
./manage.py --dump /tmp/converted/ 600 650 # converts samples [600,650)
# tip: pay attention to the number of chars reported in the output / resulting file size, and adjust the start/stop index parameters as needed

# (now upload the dumped .docx file to DeepL for translation)

# then convert a folder of 1 or more translated .docx files to .jsonl files
./manage.py --deserialize /tmp/converted/
# then merge all the .jsonl files to a single .jsonl file
./manage.py --merge /tmp/converted/ ./output.jsonl

# upload the final dataset to hugging face
./manage.py --upload ./output.jsonl
````

With the `--merge` approach it's possible to combine translated samples from the API, with translated samples from the docx file upload approach (just ensure all the desired .jsonl files are in the same folder passed with `--merge`).