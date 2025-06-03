From Conversation to Evaluation: Benchmarking LLMs on Development Knowledge via RealDevQA
=============
RealDevQA is a multilingual Development Knowledge QA benchmark derived from large-scale real user dialogues via a rigorous three-phase pipeline. This dataset contains 2,740 Dev Knowledge QA pairs in three languages (English, Chinese, and Russian), and is built from dialogues that cover broad development knowledge, featuring verifiable answers grounded in web-sourced reference documents. 
The data pipeline is as follow:
![](figure/pipeline.png)

Source Code
-------------
### Environment
Create the environment and install the required packages
```python
conda create -n RealDevQA python=3.11
conda activate RealDevQA
```
### Evaluation
You can evaluate LLM performance on RealDevQA by following these steps:

(1) Download the repository [RealDevQA](https://anonymous.4open.science/r/RealDevQA-25E7/).

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
cd RealDevQA
python code/eval/eval_demo.py
```

### Result
we use these metrics to evaluate the performance of LLMs on RealDevQA:
* Correct (CO): The predicted answer fully contains the
reference answer without contradiction.
* Not Attempted (NA): The predicted answer does not fully
cover the reference answer but does not contradict it.
* Incorrect (IN): The predicted answer contradicts the refer-
ence answer, even if the contradiction is later resolved.
* Correct Given Attempted (CGA): The proportion of
correct answers among all attempted answers (including
both correct and incorrect responses).
* F-score: The harmonic mean of the overall percentage of
correctly answered questions and the metric ”Correct Given
Attempted.”
