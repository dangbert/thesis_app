## Models and Scripts

````bash
# generate synthetic smart goals (into desired directory)
mkdir -p ../datasets/synthetic_smart/v3/
./synthetic_smart.py -o ../datasets/synthetic_smart/v3/ --sample-size 50 -m "gpt-4-0125-preview"

# generate feedback on goals (and make plots)
./feedback.py -i ../datasets/synthetic_smart/v3/ -m "gpt-4-0125-preview"
````