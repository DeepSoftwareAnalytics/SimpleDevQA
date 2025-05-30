import json
import os
import time
from collections import deque
from goose3 import Goose
import pandas as pd
import requests
from typing import Dict, Any, List
from llama_index.core import VectorStoreIndex, Document
from query_llm import query_searchllm, query_llm
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, ServiceContext, Settings
from llama_index.core.agent.workflow import FunctionAgent
import asyncio
from llama_index.llms.openai_like import OpenAILike
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.llms.deepseek import DeepSeek
from llama_index.llms.openllm import OpenLLM
import logging
import csv
from llama_index.core import StorageContext, load_index_from_storage

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


Settings.llm = OpenLLM(model="", api_base="", api_key="", is_chat_model=True)
Settings.embed_model = HuggingFaceEmbedding(model_name="")
# Create a RAG tool using LlamaIndex
# documents = SimpleDirectoryReader("").load_data()
# index = VectorStoreIndex.from_documents(documents)
# Save the index
# index.storage_context.persist("")
# Later, load the index
storage_context = StorageContext.from_defaults(persist_dir="")
index = load_index_from_storage(
    storage_context,
    embed_model=Settings.embed_model,
)
query_engine = index.as_query_engine()


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


def fetch_document_goose(url: str):
    RATE_LIMITER.wait()
    # 初始化 Goose 对象
    g = Goose()
    try:
        # 从 URL 提取内容
        article = g.extract(url=url)
        return article, article.title
    except Exception as e:
        print(f"Error extracting {url}: {e}")
        return "", ""


def get_documents(input_file, outpath):
    with open(input_file, 'r', encoding='utf-8') as f:
        ref = json.load(f)
    urls = []
    for result in ref['results']:
        urls.append(result['link'])
    doc_num = 0
    for url in urls:
        document, title = fetch_document_goose(url)
        ref_file = os.path.join(outpath, f"{str(doc_num)}.json")
        doc_num += 1
        with open(ref_file, 'w', encoding='utf-8') as file:
            file.write(document)


def search_ref(input_file, output_path):
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    df = pd.DataFrame(data)  # 将 JSON 数据转换为 DataFrame
    for idx, row in df.iterrows():
        links = query_searchllm(row['question'])
        # 创建以 idx 命名的文件夹路径
        folder_path = os.path.join(output_path, str(idx))
        # 如果文件夹不存在，则创建
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)
        ref_file = os.path.join(folder_path, "urls.json")
        with open(ref_file, 'w', encoding='utf-8') as file:
            json.dump(links, file, indent=4)
        get_documents(ref_file, folder_path)


# 使用llamaindex
def get_raganswer_llamaindex(input_file, output_file):
    df = pd.read_csv(input_file)
    qas = []
    for idx, row in df.iterrows():
        response = query_engine.query(row['problem'])
        qas.append({
            "problem": row['problem'],
            "golden_answer": row['golden_answer'],
            "rag_answer": str(response),
            "language": row['language']
        })
        new_df = pd.DataFrame(qas)
        new_df.to_csv(output_file, index=False)


if __name__ == "__main__":
    # 从 JSON 文件加载查询
    RATE_LIMITER = RateLimiter(max_calls=200, period=60)
    input_file = ""
    output_file = ""
    output_file1 = ""
    search_ref(input_file, output_file)
    get_raganswer_llamaindex(output_file, output_file1)