# RealDevQA
RealDevQA is a multilingual Development Knowledge QA benchmark derived from large-scale real user dialogues via a rigorous three-phase pipeline. This dataset contains 2,740 Dev Knowledge QA pairs in three languages (English, Chinese, and Russian), and is built from dialogues that cover broad development knowledge, featuring verifiable answers grounded in web-sourced reference documents. 

## Evals
You can evaluate LLM performance on RealDevQA by following these steps:

(1) Download the GitHub repository and install the required packages:

```python
git clone https://github.com/DeepSoftwareAnalytics/RealDevQA.git
```

(2) In the `code/eval/eval_demo.py` file, please add the grader model you wish to use and its corresponding API key and base URL:
```python
grading_sampler = ChatCompletionSampler(
        model="",
        system_message=OPENAI_SYSTEM_MESSAGE_API,  
        api_key="",
        base_url=""
    )
```

(3) In the `code/eval/eval_demo.py` file, please add some eval models you wish to use and its corresponding API key and base URL:
```python
samplers = { 
    "model_name": ChatCompletionSampler(
            model="model_name",
            system_message=OPENAI_SYSTEM_MESSAGE_API,  
            api_key="",
            base_url=""
        ),
    # ...
}
```

(4) Run the eval script. After running it, you can get the eval results:
```python
python code/eval/eval_demo.py
```
