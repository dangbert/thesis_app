## Models and Scripts

````bash
# generate synthetic smart goals (into desired directory)
mkdir -p ../datasets/synthetic_smart/example
./synthetic_smart.py -o ../datasets/synthetic_smart/example/ --sample-size 50 -m "gpt-4-0125-preview"

# generate feedback on smart goals (and make plots)
./feedback.py -i ../datasets/synthetic_smart/example/ -m "gpt-4-0125-preview"
# do the same with gpt3
./feedback.py -i ../datasets/synthetic_smart/example/ -m "gpt-3.5-turbo-0125"

python3 benchmark.py -ig /Users/dan/Downloads/COURSES/thesis/repos/thesis_app/datasets/synthetic_smart/v3/smart_goals.csv -i3 /Users/dan/Downloads/COURSES/thesis/repos/thesis_app/datasets/synthetic_smart/v3/feedback_gpt-3.5-turbo-0125__judged_gpt-4-0125-preview.csv -i4 /Users/dan/Downloads/COURSES/thesis/repos/thesis_app/datasets/synthetic_smart/v3/feedback_gpt-4-0125-preview__judged_gpt-4-0125-preview.csv

````

## Misc References
* [Hugging Face LLama2 docs](https://huggingface.co/docs/transformers/main/model_doc/llama2) (how to quanitize, fine-tune etc).