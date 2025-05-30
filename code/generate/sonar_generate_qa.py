import json
import re
from goose3 import Goose
import pandas as pd
import requests
from query_llm import query_llm
from query_llm import query_llm2
from query_llm import query_searchllm
import os
import time
from collections import deque
import logging


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


def fetch_document_goose(url: str, doc_num) -> str:
    RATE_LIMITER.wait()
    # 初始化 Goose 对象
    g = Goose()
    try:
        # 从 URL 提取内容
        article = g.extract(url=url)
        # 输出提取结果
        return article.cleaned_text
    except Exception as e:
        print(f"Error extracting {url}: {e}")
        return ""


# 提取关键内容
def extract_key_content(webpage):
        content = webpage.get("document", "")
        if content:
            prompt = f"document: {content}"
            system_prompt = f"Extract and retain only the content related to software engineering from the provided document. Remove any irrelevant or redundant information that does not pertain to software engineering, while ensuring that all relevant content is preserved without any modifications. Focus on retaining details about specific versions, scenarios, or technical knowledge directly applicable to software engineering. Only output the final retained content."
            key_content = query_llm(prompt, system_prompt)
        else:
            key_content = ""
        return key_content


# 处理单个 query
def process_single_query(ref, conversation_id, output_folder, output_folder2, doc_num, top_k=3):
    dcontent = []
    # 保存处理后的结果
    output_file = os.path.join(output_folder, f"{conversation_id}.json")
    # 提取所有 link
    urls = []
    for item in ref:
        for result in item['results']:
            urls.append(result['link'])

    for url in urls:
            document = fetch_document_goose(url, doc_num)
            dcontent.append({
                "link": url,
                "document": document,
            })
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(dcontent, f, ensure_ascii=False, indent=4)
    print(f"Sort results saved to {output_file}")

    # 提取关键内容
    results = []
    for webpage in dcontent:
        if webpage['document']:
            key_content = extract_key_content(webpage)
            results.append({
                "link": webpage.get("link", ""),
                "key_content": key_content
            })

    # 保存处理后的结果
    output_file = os.path.join(output_folder2, f"{conversation_id}.json")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=4)
    print(f"Results saved to {output_file}")


# 处理所有 query
def process_all_queries(folder_path, output_folder, output_folder2):
    # 正则表达式匹配文件名中的 conversation_id
    pattern = r"(.+)\.json"
    doc_num = 0
    # 遍历文件夹
    for filename in os.listdir(folder_path):
        file_path = os.path.join(folder_path, filename)
        with open(file_path, 'r', encoding='utf-8') as f:
            ref = json.load(f)
            # 提取 conversation_id
            match = re.match(pattern, filename)
            if match:
                conversation_id = match.group(1)
                process_single_query(ref, conversation_id, output_folder, output_folder2, doc_num)
    # print("文档数量：", doc_num)


def generate_ref(input_file, folder_path, output_folder):
    # 根据query生成ref
    pattern = r"\[Query\](.*)"
    num = 0
    df = pd.read_excel(input_file)
    for idx, row in df.iterrows():
        query_file = os.path.join(folder_path, f"{row['conversation_id']}.json")
        if os.path.exists(query_file):
            with open(query_file, 'r', encoding='utf-8') as f:
                query_data = f.read()
                if query_data:
                    # 使用正则表达式提取整个 [References] 部分
                    match = re.search(pattern, query_data, re.DOTALL)
                    if match:
                        queries = match.group(1).strip()
                        prompt = f"Here is the given queries: {queries}"
                        system_prompt = f"You are an expert software programmer. Based on the provided queries, search for high-quality references, including documentation, technical articles, and official resources. Ensure that the references are relevant, authoritative, and directly address the queries. Provide the correct URLs that can be used to access the content.\n\n"\
                                        f"Your task:\n"\
                                        f"1. Use the provided queries to search for the most useful and high-quality references.\n"\
                                        f"2. Include a variety of sources, such as official documentation, technical blogs, and paper.\n"\
                                        f"3. Ensure the URLs are valid and directly link to the content.\n\n"\
                                        f"Your response must have these parts:\n"\
                                        f"[References]\n"\
                                        f"1. [Title]:[URL]\n"\
                                        f"2. [Title]:[URL]\n"
                        RATE_LIMITER.wait()  # 等待以满足速率限制
                        # response = query_llm2(prompt, system_prompt)
                        response = query_searchllm(prompt, system_prompt)
                        num += 1
                        search_file = os.path.join(output_folder, f"{row['conversation_id']}.json")
                        # 保存获取的 document 到文件
                        with open(search_file, 'w', encoding='utf-8') as f:
                            f.write(response)
                        logger.info(f"conversation_id {row['conversation_id']} be processed")
    print("ref_num: ", num)


def generate_query(input_file, output_folder):
    df = pd.read_excel(input_file)
    for idx, row in df.iterrows():
        conversation = {
            "prompt": row['prompt'],
            "response": row['response']
        }
        prompt = f"Here is the given conversation: {conversation}"
        system_prompt = f"You are an expert software programmer. Analyze the given conversation to identify key programming topics and generate detailed, precise, and relevant queries. Ensure that the queries are refined to search for high-quality documentation or technical resources.. Pay special attention to any code segments in the conversation to generate fine-grained queries.\n"\
                        f"For conversations containing code:\n"\
                        f"1. Identify the programming language, libraries, frameworks, or tools used in the code.\n"\
                        f"2. Generate queries that focus on finding official documentation, API signatures, usage examples, or best practices related to the code.\n"\
                        f"3. Prioritize queries that can lead to version-specific documentation, API references, or practical usage examples.\n\n"\
                        f"Your response must have these parts:\n"\
                        f"[Query]\n"\
                        f"Query 1: [Generated query]\n"\
                        f"Query 2: [Generated query]\n\n"\
                        f"Examples of good queries:\n"\
                        f"- Go 1.16 modules support improvements.\n"\
                        f"- Kubernetes 1.21 volume management API examples\n"\
                        f"- Index optimization in MySQL 8.x.\n"\
                        f"- Python requests library API documentation for handling HTTP errors.\n"\
                        f"- How to use React useState hook with TypeScript in React 18.\n"
        RATE_LIMITER.wait()  # 等待以满足速率限制
        response = query_llm(prompt, system_prompt)
        search_file = os.path.join(output_folder, f"{row['conversation_id']}.json")
        # 保存获取的 document 到文件
        with open(search_file, 'w', encoding='utf-8') as f:
            f.write(response)
        logger.info(f"conversation_id {row['conversation_id']} be processed")


def generate_qa_by_doc(input_file, folder_path, qa_output_folder, outfile):
    qas = []
    df = pd.read_excel(input_file)
    for idx, row in df.iterrows():
        document_file = os.path.join(folder_path, f"{row['conversation_id']}.json")
        # print(document_file)
        if os.path.exists(document_file):
            with open(document_file, 'r', encoding='utf-8') as f:
                document_data = json.load(f)
                if document_data and isinstance(document_data, list) and len(document_data) > 0:
                    # 根据 'link' 字段去重（保留顺序）
                    seen_links = set()
                    unique_data = []
                    for item in document_data:
                        link = item.get('link')
                        if link not in seen_links:
                            seen_links.add(link)
                            unique_data.append({
                                "link": item['link'],
                                "key_content": item['document'],  # documents
                                # "key_content": item['key_content'],  # filter_documents, jina.ai
                            })
                    # 提取关键内容并拼接
                    key_contents = []
                    for webpage in unique_data:
                        key_content = webpage['key_content']
                        if key_contents:
                            # key_contents.append(key_content)
                            key_contents.append(f"{webpage['link']}\n{key_content}")
                    # document = "".join(key_contents)  # 直接拼接，不插入空格
                    # 将 key_contents 列表中的所有内容用换行符拼接成一段文本
                    document = '\n'.join(key_contents)
                    conversation = {
                        # "prompt": row[1]['prompt'],
                        # "response": row[1]['response']
                        "prompt": row['prompt'],
                        "response": row['response']
                    }
                    # conversation = json.dumps(conversation, ensure_ascii=False, indent=2)
                    prompt = f"Here is the given conversation: {conversation},document:{document}"
                    system_prompt = f"""You are an expert software programmer. Now you need to generate three programming fact-based questions and their corresponding standard answers based on the given conversation and document. The QA pairs must meet the following requirements:
1. **Relevance to Software Engineering**: The questions must relate to concrete programming knowledge or concepts in software engineering, such as algorithms, data structures, design patterns, libraries, APIs, or best practices. Avoid subjective or opinion-based questions.
2. **Language Consistency**: The language used in the generated question-answer pairs must be consistent with the language used in the conversation.
3. **Clarity and Precision**: Each question should have one and only one clear and undisputed answer. Avoid ambiguous or open-ended questions.
4. **Timeless Answers**: The answers must be timeless and not subject to change. Avoid questions about roles, events that may change over time.
5. **Conciseness**: Answers should be as concise as possible while remaining accurate.
6. **Educational Value**: Questions should have a certain level of difficulty to pose a challenge and be educational for learning software engineering concepts.The generated questions cannot be easily answered correctly
7. **Version-Specific Knowledge**: The questions and answers are preferably version-specific to maintain accuracy.

Your response must have the following format:
[QA Pairs]
  {{\"question\": \"[Generated question 1]\", \"answer\": \"[Standard answer 1]\"}},
  {{\"question\": \"[Generated question 2]\", \"answer\": \"[Standard answer 2]\"}},
  {{\"question\": \"[Generated question 3]\", \"answer\": \"[Standard answer 3]\"}}

### Examples of High-Quality QA Pairs ###
{{\"question\": \"In Python 3.9, what is the time complexity of the merge operation in the heapq.merge function when merging k sorted lists with a total of n elements?\", \"answer\": \"O(n log k).\"}},
{{\"question\": \"In Python, what exception is raised when a user inputs a non-numerical value while attempting to convert to a float?\", \"answer\": \"ValueError.\"}},
{{\"question\": \"What library in Python provides the ImageDataGenerator class for data augmentation in deep learning?\", \"answer\": \"TensorFlow Keras.\"}},
{{\"question\": \"In Java 11, what is the default initial capacity of a HashMap if no initial capacity is specified in the constructor?\", \"answer\": \"16\"}},
{{\"question\": \"What is the command to install the react-three/drei package version 9.96.5 using npm?\", \"answer\": \"npm install @react-three/drei@9.96.5\"}},
{{\"question\": \"In the sed command, what does the 's' represent?\", \"answer\": \"The substitute operation.\"}},
{{\"question\": \"What transformation matrix method resets the current transform to the identity matrix in the Canvas 2D API?\", \"answer\": \"resetTransform().\"}}
{{\"question\": \"In max pooling with a 2x2 filter and a stride of 2, by what factor is the feature map size reduced?\", \"answer\": \"by a factor of 4.\"}}
{{\"question\": \"Does MinMaxScaler handle NaN values during the fit and transform processes?\", \"answer\": \"No.\"}}
{{\"question\": \"What is the term for grouping related data and functions (or methods) into a single unit in object-oriented programming (OOP).\", \"answer\": \"Encapsulation.\"}}
"""
                    RATE_LIMITER.wait()  # 等待以满足速率限制
                    # response = query_llm(prompt, system_prompt, model="gpt-4o")
                    response = query_llm2(prompt, system_prompt, model="gpt-4o")
                    search_file = os.path.join(qa_output_folder, f"{row['conversation_id']}.json")
                    # 保存获取的 document 到文件
                    with open(search_file, 'w', encoding='utf-8') as f:
                        f.write(response)
                    # 提取出qa对
                    # 使用正则表达式提取整个 [QA Pairs] 部分
                    pattern = r"\[QA Pairs\](.*)"
                    match = re.search(pattern, response, re.DOTALL)
                    if match:
                        qa = match.group(1).strip()
                        qas.append(qa)
                        new_qas = '\n'.join(qas)
                        # 保存获取的 document 到文件
                        with open(outfile, 'w', encoding='utf-8') as f:
                            # json.dump(new_qas, f, indent=4)
                            f.write(new_qas)


def two_steps_generate_qa(input_file, output_folder, outfile):
    # 生成query
    query_output_folder = "queries"
    generate_query(input_file, query_output_folder)
    # 生成references
    generate_ref(input_file, query_output_folder, output_folder)
    # 从references中获取文档内容并提取
    folder_path = "filter_documents"
    qa_output_folder = "output_qa"
    process_all_queries(output_folder, "documents", folder_path)
    generate_qa_by_doc(input_file, "/data/generate_qa/goose_documents", qa_output_folder, outfile)  # goose


if __name__ == "__main__":
    # 输入 JSON 文件路径和输出文件路径
    input_file = "filtered_conversations_threelang.xlsx"
    output_folder = "references"  # 输出文件夹路径
    outfile = "initial_qas.json"
    # 设置速率限制
    RATE_LIMITER = RateLimiter(max_calls=5, period=1)
    two_steps_generate_qa(input_file, output_folder, outfile)

    out_qafile = ""

