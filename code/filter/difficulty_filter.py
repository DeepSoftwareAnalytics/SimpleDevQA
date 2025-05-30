import json
import re
from goose3 import Goose
import pandas as pd
import requests
from query_llm import query_smallllm
from query_llm import query_llm2
import os
import time
from collections import deque
import logging
import csv
import os
from collections import OrderedDict
import glob


# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RateLimiter:
    def __init__(self, max_calls: int, period: float):
        """
        初始化速率限制器。
        :param max_calls: 允许的最大调用次数。
        :param period: 时间窗口（以秒为单位）。
        """
        self.max_calls = max_calls
        self.period = period
        self.timestamps = deque()

    def wait(self):
        """
        等待以确保不超过速率限制。
        """
        now = time.time()
        # 移除超过时间窗口的时间戳
        while self.timestamps and self.timestamps[0] <= now - self.period:
            self.timestamps.popleft()
        # 如果当前请求数超过限制，则等待
        if len(self.timestamps) >= self.max_calls:
            wait_time = self.period - (now - self.timestamps[0])
            time.sleep(wait_time)
        # 记录当前时间戳
        self.timestamps.append(time.time())


def predict_answer(input_file, output_file):
    new_qas = []
    with open(input_file, 'r', encoding='utf-8') as f:
        qas = json.load(f)
        for qa in qas:
            question = qa['problem']
            prompt = f"Please carefully analyze the following question and provide a clear, accurate, and structured response based on the core of the question:{question}"
            response = query_smallllm(prompt, model="")
            if response is not None:
                new_qa = {
                    "question": qa['problem'],
                    "answer": qa['answer'],
                    "predict_answer": response,
                }
                new_qas.append(new_qa)
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(new_qas, f, indent=4)


def difficulty_filter(input_file, output_file):
    # 使用pandas读取CSV文件
    df = pd.read_csv(input_file)
    # 提取grade_letter列中值为B的记录，并选择problem和golden_answer列
    filtered_df = df[df['grade_letter'] != 'A'][['problem', 'golden_answer']]
    # 统计提取的记录数量
    record_count = len(filtered_df)
    print(f"提取的记录数量: {record_count}")
    # 重命名列
    filtered_df = filtered_df.rename(columns={'problem': 'problem', 'golden_answer': 'answer'})
    # 保存到新的CSV文件
    filtered_df.to_csv(output_file, index=False)
    print(f"提取的数据已保存到 {output_file}")


if __name__ == "__main__":
    # 输入 JSON 文件路径和输出文件路径
    input_file = ""
    output_file = ""
    RATE_LIMITER = RateLimiter(max_calls=50, period=60)
    predict_answer(input_file, output_file)
    difficulty_filter(input_file, output_file)

