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

system_prompt = f"You are an expert software programmer. Now you need to generate best response based on the given conversation, including query, references and three programming fact QA pairs:\n"\
f"\n"\
f"Your response must have these parts:\n"\
f"[Query]\n"\
f"{{Analyze the conversation to identify key programming topics and generate detailed query.}}\n"\
f"[References]\n"\
f"{{Search based on the formed queries to source the most useful and high-quality references.}}\n"\
f"[QA Pairs]\n"\
f"{{Use the retrieved references to generate three concise questions and answers.}}\n"\
f"\n"\
f"Guidelines for each parts:\n"\
f"1.[Query]: Ensure that the generated queries are precise, relevant, and refined to search for a certain version or a specific scenario, and ensure that high-quality documents are searched, especially some documentation. If the given conversation includes large code segments, pay attention to the code used to generate fine-grained queries.Here are some examples:\n"\
f"  query: Go 1.16 modules support improvements.\n"\
f"  query: new volume management features in Kubernetes 1.21.\n"\
f"  query: index optimization in MySQL 8.x\n"\
f"2.[References]: The types of references obtained from the search should be very rich, including various types of websites."
f"3.[QA Pairs]: The generated QA pairs should preferably involve knowledge from many aspects of software engineering, such as algorithms, data structures, and networking principles, and complex concepts such as binary search trees, dynamic programming, and the intricacies of obiect-oriented design patterns. The generated qa pairs must meet specific criteria:\n"\
f"  -The questions must relate to concrete programming knowledge or concepts, such as \"What is the average time complexity of quicksort?\" Avoid constructing subjective opinion-based questions, like \"What do you think about functional programming?\"\n"\
f"  -The language used in the generated question-answer pair must be consistent with the language used in the prompt in the conversation.\n"\
f"  -The questions asked should have one and only one clear and undisputed entity as an answer, and there should be no ambiguity or ambiguity in the question formulation. Avoid questions like \"Where did the Python language originate?\" or \"What is the purpose of this function\" if it could refer to multiple phases or events.\n"\
f"  -The answers must be timeless, not subject to change. For example, \"Who is currently the lead developer of the XYZ project?\" would not be suitable, as roles can change.\n"\
f"  -Answer the question in the most concise way possible.\n"\
f"  -Questions should have a certain level of difficulty to pose a challenge.\n"\
f"Here are some examples that meet all of the above criteria:\n"\
f"  {{\"question\": \"What is the command to install the react-three/drei package version 9.96.5 using npm?\",\"answer\": \"npm install @react-three/drei@9.96.5\"}}\n"\
f"  {{\"question\": \"In Python, what exception is raised when a user inputs a non-numerical value while attempting to convert to a float?\",\"answer\": \"ValueError\"}}\n"\
f"  {{\"question\": \"Can Bootstrap call the class btn-group to form a button group?\",\"answer\": \"Yes.\"}}\n"\
f"  {{\"question\": \"What is the maximum number of unique characters that can be represented using the ASCII encoding standard?\",\"answer\": \"128 unique characters.\"}}\n"\
f"The generated qa pairs format is as follows:\n"\
f"  {{\"question\": \"[Generated question 1]\", \"answer\": \"[Standard answer 1]\"}},\n"\
f"  {{\"question\": \"[Generated question 2]\", \"answer\": \"[Standard answer 2]\"}},\n"\
f"  {{\"question\": \"[Generated question 3]\", \"answer\": \"[Standard answer 3]\"}},\n"


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


def fetch_document(url: str) -> str:
    RATE_LIMITER.wait()  # 等待以满足速率限制
    """通过 URL 获取网页内容"""
    try:
        # async with aiohttp.ClientSession() as session:
            # 使用 r.jina.ai 服务获取网页内容
            jina_url = f"https://r.jina.ai/{url}"
            # async with session.get(jina_url) as response:
            response = requests.get(jina_url)
            if response.status_code == 200:
                    # html = await response.text()
                    # soup = BeautifulSoup(html, "html.parser")
                    # # 提取网页正文内容
                    # text = soup.get_text(separator="\n", strip=True)
                    # return text
                    # 直接返回网页的文本内容
                return response.text
            else:
                logger.error(f"Failed to fetch document from {url}: {response.status_code}")
                return ""
    except Exception as e:
        logger.error(f"Error fetching document from {url}: {str(e)}")
        return ""


def fetch_document_goose(url: str) -> str:
    # 初始化 Goose 对象
    g = Goose()
    try:
        # 从 URL 提取内容
        # url = 'https://www.gnu.org/software/bison/manual/bison.html'
        article = g.extract(url=url)
        # 输出提取结果
        # print(f"Title: {article.title}")
        # print(f"Meta Description: {article.meta_description}")
        # print(f"Main Text: {article.cleaned_text}")
        return article.meta_description+article.cleaned_text
    except Exception as e:
        print(f"Error extracting {url}: {e}")
        return ""


# 提取关键内容
def extract_key_content(webpage):
    # async with aiohttp.ClientSession() as session:
        content = webpage.get("document", "")
        # chunks = chunk_text(content)
        # key_contents = []
        #
        # for chunk in chunks:
        if content:
            prompt = f"document: {content}"
            system_prompt = f"Extract and retain only the content related to software engineering from the provided document. Remove any irrelevant or redundant information that does not pertain to software engineering, while ensuring that all relevant content is preserved without any modifications. Focus on retaining details about specific versions, scenarios, or technical knowledge directly applicable to software engineering. Only output the final retained content."
            key_content = query_llm(prompt, system_prompt)
            # key_contents.append(key_content)
        else:
            key_content = ""
        return key_content


# 处理单个 query
def process_single_query(ref, conversation_id, output_folder, output_folder2, top_k=3):
    dcontent = []
    # 使用正则表达式提取整个 [References] 部分
    pattern = r"\[References\](.*)"
    match = re.search(pattern, ref, re.DOTALL)

    if match:
        references = match.group(1).strip()
        # 提取 URL
        urls = re.findall(r"https?://\S+", references)
        for url in urls:
            # 获取网页内容
            # document = fetch_document(url)
            document = fetch_document_goose(url)
            dcontent.append({
                "link": url,
                "document": document,
            })
    # 保存处理后的结果
    output_file = os.path.join(output_folder, f"{conversation_id}.json")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(dcontent, f, ensure_ascii=False, indent=4)
    print(f"Sort results saved to {output_file}")

    # 提取关键内容
    results = []
    for webpage in dcontent:
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

    # 遍历文件夹
    for filename in os.listdir(folder_path):
        file_path = os.path.join(folder_path, filename)
        with open(file_path, 'r', encoding='utf-8') as f:
            ref = f.read()
            # 提取 conversation_id
            match = re.match(pattern, filename)
            if match:
                conversation_id = match.group(1)
                process_single_query(ref, conversation_id, output_folder, output_folder2)


def generate_qa(input_file, output_folder):
    df = pd.read_excel(input_file)
    for idx, row in df.iterrows():
        conversation = {
            "prompt": row['prompt'],
            "response": row['response']
        }
        prompt = f"Here is the given conversation: {conversation}"
        RATE_LIMITER.wait()  # 等待以满足速率限制
        response = query_llm2(prompt, system_prompt, model="sonar-pro")
        search_file = os.path.join(output_folder, f"{row['conversation_id']}.json")
        # 保存获取的 document 到文件
        with open(search_file, 'w', encoding='utf-8') as f:
            f.write(response)
        logger.info(f"conversation_id {row['conversation_id']} be processed")


def generate_ref(folder_path, output_folder):
    # 根据query生成ref
    pattern = r"\[Query\](.*)"
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
                                        f"2. Include a variety of sources, such as official documentation, technical blogs, and community forums.\n"\
                                        f"3. Ensure the URLs are valid and directly link to the content.\n\n"\
                                        f"Your response must have these parts:\n"\
                                        f"[References]\n"\
                                        f"1. [Title]:[URL]\n"\
                                        f"2. [Title]:[URL]\n"
                        RATE_LIMITER.wait()  # 等待以满足速率限制
                        response = query_llm2(prompt, system_prompt, model="sonar-pro")
                        search_file = os.path.join(output_folder, f"{row['conversation_id']}.json")
                        # 保存获取的 document 到文件
                        with open(search_file, 'w', encoding='utf-8') as f:
                            f.write(response)
                        logger.info(f"conversation_id {row['conversation_id']} be processed")


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


def two_steps_generate_qa(input_file, output_folder, outfile):
    # 生成query
    query_output_folder = "E:\devwildchat\data/test/sonar_goose_query_long2"
    # generate_query(input_file,query_output_folder)
    # 生成references
    # generate_ref(query_output_folder, output_folder)
    # 从references中获取文档内容并提取
    folder_path = "E:\devwildchat\data/test\sonar_filter_documents_goose_long2"
    qa_output_folder = "E:\devwildchat\data/test/sonar_goose_qa_long2"
    process_all_queries(output_folder, "E:\devwildchat\data/test\sonar_documents_goose_long2", folder_path)
    # 生成qa
    # 遍历文件夹
    qas = []
    df = pd.read_excel(input_file)
    for idx, row in df.iterrows():
        document_file = os.path.join(folder_path, f"{row['conversation_id']}.json")
        if os.path.exists(document_file):
            with open(document_file, 'r', encoding='utf-8') as f:
                document_data = json.load(f)
                if document_data and isinstance(document_data, list) and len(document_data) > 0:
                    # 提取关键内容并拼接
                    key_contents = []
                    for webpage in document_data:
                        key_content = webpage['key_content']
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
4. **Timeless Answers**: The answers must be timeless and not subject to change. Avoid questions about roles, events, or versions that may change over time.
5. **Conciseness**: Answers should be as concise as possible while remaining accurate.
6. **Educational Value**: Questions should have a certain level of difficulty to pose a challenge and be educational for learning software engineering concepts.
7. **Version-Specific Knowledge**: If the conversation involves specific versions of libraries, frameworks, or tools, ensure the questions and answers are version-specific to maintain precision.

Your response must have the following format:
[QA Pairs]
  {{\"question\": \"[Generated question 1]\", \"answer\": \"[Standard answer 1]\"}},
  {{\"question\": \"[Generated question 2]\", \"answer\": \"[Standard answer 2]\"}},
  {{\"question\": \"[Generated question 3]\", \"answer\": \"[Standard answer 3]\"}}

### Examples of High-Quality QA Pairs ###
{{\"question\": \"What is the average time complexity of quicksort?\", \"answer\": \"O(n log n).\"}},
{{\"question\": \"In Python, what exception is raised when a user inputs a non-numerical value while attempting to convert to a float?\", \"answer\": \"ValueError.\"}},
{{\"question\": \"Which library in Python provides the RandomForestClassifier?\", \"answer\": \"scikit-learn.\"}},
{{\"question\": \"What is the maximum number of unique characters that can be represented using the ASCII encoding standard?\", \"answer\": \"128 unique characters.\"}},
{{\"question\": \"What is the command to install the react-three/drei package version 9.96.5 using npm?\", \"answer\": \"npm install @react-three/drei@9.96.5\"}},
{{\"question\": \"In the sed command, what does the 's' represent?\", \"answer\": \"The substitute operation.\"}},
{{\"question\": \"Which CSS properties control how long words break when they overflow their container?\", \"answer\": \"overflow-wrap or word-break.\"}},
{{\"question\": \"Can Bootstrap call the class btn-group to form a button group?\", \"answer\": \"Yes.\"}}
"""
                    RATE_LIMITER.wait()  # 等待以满足速率限制
                    response = query_llm(prompt, system_prompt)
                    search_file = os.path.join(qa_output_folder, f"{row['conversation_id']}.json")
                    # 保存获取的 document 到文件
                    with open(search_file, 'w', encoding='utf-8') as f:
                        f.write(response)
                    #提取出qa对
                    # 使用正则表达式提取整个 [QA Pairs] 部分
                    pattern = r"\[QA Pairs\](.*)"
                    match = re.search(pattern, response, re.DOTALL)
                    if match:
                        qa = match.group(1).strip()
                        qa = qa.replace('\\"', '"')
                        qas.append(qa)
    qas = '\n'.join(qas)
    # 保存获取的 document 到文件
    with open(outfile, 'w', encoding='utf-8') as f:
        json.dump(qas, f, ensure_ascii=False, indent=4)
    # logger.info(f"conversation_id {row['conversation_id']} be processed")


if __name__ == "__main__":
    # 输入 JSON 文件路径和输出文件路径
    input_file = "E:\devwildchat\data/test/filtered_one_conversations.xlsx"
    output_folder = "E:/devwildchat/data/test/sonar_ref_long2"  # 输出文件夹路径
    outfile = "E:/devwildchat/data/test/test_with_sonar_goose_long2.json"
    # 设置速率限制
    # wiki:每小时最多 500 次调用
    RATE_LIMITER = RateLimiter(max_calls=50, period=60)
    # generate_qa(input_file, output_folder)
    two_steps_generate_qa(input_file, output_folder, outfile)

