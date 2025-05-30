import json
import re
from goose3 import Goose
import pandas as pd
import requests
from query_llm import query_llm
from query_llm import query_llm2
import os
import time
from collections import deque
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def llm_verify(input_file, output_file, output_file2):
    system_prompt = """You are a data quality inspector.You need to check whether the following questions meet the following requirements:
1. The generated question must ask about knowledge of the objective world. Avoid subjective or opinion-based questions.
2. Each question should have one and only one clear and undisputed answer. Avoid ambiguous or open-ended questions.
3. Questions should have a certain level of difficulty to pose a challenge and be educational for learning software engineering concepts. The generated questions cannot be easily answered correctly
4. Each question should contain only one inquiry.

###Here are some examples:
question: What is the purpose of the Box2D library in game development?
response: The question is subjective, [No]

question: In a Drools DRL file, what are the main components that must be included for defining a rule?
response: There is not only clear answer to this question, [No]

question: How can you search for multiple documents in Elasticsearch based on their routing values?
response: The answer is not undisputed, [No]

question: What is the average time complexity of the Floyd-Warshall algorithm for finding shortest paths in a graph?
response: [Yes]

question: Does MinMaxScaler handle NaN values during the fit and transform processes?
response: [Yes]

###If the question is not qualified, provide the reason and then output "[No]". If the question is qualified, output "[Yes]" directly. Let's begin!"""
    new_qas = []
    all_qas = []
    num = 0
    with open(input_file, 'r', encoding='utf-8') as f:
        qas = json.load(f)
        for qa in qas:
            question = qa['question']
            prompt = f"Here is the given question：{question}"
            response = query_llm(prompt, system_prompt)
            pattern = r"\bYes\b"
            if response is not None:
                matches = re.findall(pattern, response)
                if matches:
                    num += 1
                    new_qa = {
                        "question": qa['question'],
                        "answer": qa['answer'],
                        "language": qa['language'],
                    }
                    new_qas.append(new_qa)
                    with open(output_file, 'w', encoding='utf-8') as f:
                        json.dump(new_qas, f, indent=4)
            mark_qa = {
                        "question": qa['question'],
                        "answer": qa['answer'],
                        "response": response
                    }
            all_qas.append(mark_qa)
            with open(output_file2, 'w', encoding='utf-8') as f:
                json.dump(all_qas, f, indent=4)


if __name__ == "__main__":
    # 输入 JSON 文件路径和输出文件路径
    input_file = ""
    output_file = ""
    output_file2 = ""
    llm_verify(input_file, output_file, output_file2)
