## Models and Scripts

````bash
# generate synthetic smart goals (into desired directory)
mkdir -p ../datasets/synthetic_smart/v3/
./synthetic_smart.py -o ../datasets/synthetic_smart/v3/ --sample-size 50 -m "gpt-4-0125-preview"

# generate feedback on goals (and make plots)
./feedback.py -i ../datasets/synthetic_smart/v3/ -m "gpt-4-0125-preview"

python3 benchmark.py -ig /Users/dan/Downloads/COURSES/thesis/repos/thesis_app/datasets/synthetic_smart/v3/smart_goals.csv -i3 /Users/dan/Downloads/COURSES/thesis/repos/thesis_app/datasets/synthetic_smart/v3/feedback_gpt-3.5-turbo-0125__judged_gpt-4-0125-preview.csv -i4 /Users/dan/Downloads/COURSES/thesis/repos/thesis_app/datasets/synthetic_smart/v3/feedback_gpt-4-0125-preview__judged_gpt-4-0125-preview.csv

````