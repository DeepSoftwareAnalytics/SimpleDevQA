import json
import requests
import logging
import os
import re

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 配置 API 密钥和重试设置
# api_key = "sk-cW2f696POnjSzdFw420212Fb32034c299dA72878F918D5A8"
api_key = "sk-Os9RkOC334PpaLdS725a9082E0Bd4aA381810dC3EcE9Ff3b"
base_url = "https://api.gptapi.us/v1/chat/completions"
max_retries = 3

def load_json_data(file_path):
    """从 JSON 文件加载数据"""
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data


def group_conversations_by_id(data):
    """根据 conversation_id 对数据进行分组"""
    conversations = {}
    for item in data:
        conversation_id = item["conversation_id"]
        if conversation_id not in conversations:
            conversations[conversation_id] = []
        conversations[conversation_id].append(item)
    return conversations

def query_gpt4(context_data, model="gpt-4o-mini"):
    """使用 GPT-4 API 发送请求并返回响应"""
    # 将 context_data 转换为字符串格式，作为上下文
    context = json.dumps(context_data, ensure_ascii=False, indent=2)
    # context = eval(context_data)

    # 构建请求配置
    config = {
        "model": model,  # 明确指定使用的模型
        "messages": [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": f"# Task Introduction\n"
                                        f"Classify each round of dialogue in a given conversation into a code scenario.\n"
                                        f"- Each round of the given conversation includes four parts: conversation_id, session_id, prompt, and response.\n"
                                        f"- Single-Round Dialogue: If a conversation has only one round, I will classify it based only on the prompt and response of that single round.\n"
                                        f"- Multi-Round Dialogue: Each `conversation_id` may contain multiple rounds of dialogue (prompt and response). For multi-round dialogues, each round will be analyzed in context. This means using the cumulative information from all preceding rounds within the same conversation_id to determine the code scenario for each round based on the `prompt` and `response`.\n"
                                        f"- The output should only include the following three parts in vaild JSON format: conversation_id, session_id, and category. A corresponding category must be provided for each round of the conversation. The category should be selected from one of the following code scenarios: Dev knowledge qa, code generation, debugging, program repair, code translation, code edit, code summarization, code understanding, test generation, and others.\n"
                                        f"- Descriptions of code scenarios:\n"
                                        f"- **dev knowledge qa**: Questions and answers about basic knowledge of programming theories, concepts, or computer-related technologies.\n"
                                        f"- **code generation**: Generate or supplement code snippets, Or provide a code example.The response must include the generated code or some code instructions, unless the response indicates an inability to generate the code.\n"
                                        f"- **debugging**: Analyzing or identifying issues in the code.\n"
                                        f"- **program repair**: Providing code repair suggestions to meet requirements or solve problems and include the repaired code.\n"
                                        f"- **code translation**: Translate the code from one programming language to another.\n"
                                        f"- **code edit**: Modifying or optimizing existing code, or add new features to the current code.The existing code might have been provided in the earlier rounds of the conversation.\n"
                                        f"- **code summarization**: Add or remove comments in the code.\n"
                                        f"- **code understanding**: Summarizing and explaining the logic or function of the code, or understanding the purpose or intent of complex code.The prompt must include code.\n"
                                        f"- **test generation**: Generating test cases that match the code.\n"
                                        f"- **others**: Other dialogues that do not fit into the above categories.\n"
                                        f"Here is the given conversation：\n{context}"}
        ],
        "max_tokens": 2000,
        "temperature": 0.7
    }

    ret = None
    retries = 0

    # 使用重试机制调用 API
    while ret is None and retries < max_retries:
        try:
            logger.info("Creating API request")
            if base_url == 'https://api.gptapi.us/v1/chat/completions':
                response = requests.post(
                    base_url,
                    json=config,
                    headers={
                        'Authorization': api_key,
                        # "anthropic-version": "2023-06-01",
                        "Content-Type": "application/json"
                    }
                )
                # logger.info(config)
                ret = response.json()
            else:
                response = requests.post(
                    base_url,
                    json=config,
                    headers={'Authorization': api_key}
                )
                ret = response.json()

            # 检查 API 响应是否有效
            if 'choices' not in ret:
                logger.warning("Invalid API response, retrying...")
                ret = None
                retries += 1
            else:
                return ret['choices'][0]['message']['content']

        except Exception as e:
            logger.error(f"Error querying GPT-4 API: {str(e)}")
            ret = None
            retries += 1

    logger.error("Max retries reached. Unable to get a valid response.")
    return None

def extract_and_parse_json(model_output, error_file):
    """提取模型返回的 Markdown 格式 JSON 并解析为 Python 对象"""
    combined_data = []
    error_data = []

    for item in model_output:
        # 使用正则表达式移除 Markdown 格式的代码块标记
        cleaned_json_str = re.sub(r"```json\s*|\s*```", "", item).strip()

        try:
            # 解析清理后的字符串为 JSON 对象
            parsed_data = json.loads(cleaned_json_str)

            # 检查解析结果是否为列表，并合并到 combined_data 中
            if isinstance(parsed_data, list):
                combined_data.extend(parsed_data)
            # 如果解析结果是字典，转换为包含该字典的列表格式
            elif isinstance(parsed_data, dict):
                combined_data.append(parsed_data)
            else:
                error_data.append(cleaned_json_str)
                print("Parsed data is not a list, skipping:", parsed_data)

        except json.JSONDecodeError as e:
            print("JSON parsing error:", e)
            # print("Skipping this item:", cleaned_json_str)
            error_data.append(cleaned_json_str)

    # 将不合法的字符串保存到错误文件中
    if error_data:
        with open(error_file, 'w', encoding='utf-8') as f:
            json.dump(error_data, f, ensure_ascii=False, indent=4)
        print(f"Invalid JSON strings saved to {error_file}")

    return combined_data

def process_conversations(conversations, output_file, error_file):
    """遍历分组后的对话，并向 GPT-4o API 提问"""
    results = []

    for conversation_id, context_data in conversations.items():
        # # 获取对话中的第一个 session_id 作为标识
        # session_id = context_data[0]["session_id"]

        # 调用 GPT-4o API 获取回答
        response = query_gpt4(context_data)

        if response:
            # # 构建结果对象
            # gpt-4o-result = {
            #     "conversation_id": conversation_id,
            #     "session_id": session_id,
            #     "response": response
            # }
            results.append(response)
            logger.info(f"Processed conversation_id: {conversation_id}")

    # 提取并解析模型输出的 JSON 数据
    parsed_data = extract_and_parse_json(results, error_file)
    # 保存结果到文件
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(parsed_data, f, ensure_ascii=False, indent=4)
    print(f"All responses saved to {output_file}")


def main(input_folder, output_folder, error_folder):
    """将指定文件夹中的所有 Excel 文件转换为 JSON 格式并保存到另一个文件夹"""
    # 如果输出文件夹不存在，则创建该文件夹
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    # 遍历输入文件夹中的所有文件
    for filename in os.listdir(input_folder):
        input_file = os.path.join(input_folder, filename)
        # 输出文件的路径，将 Excel 扩展名替换为 .json
        output_file = os.path.join(output_folder, filename)
        error_file = os.path.join(error_folder, filename)
        # 加载 JSON 数据
        json_data = load_json_data(input_file)

        # 根据 conversation_id 分组对话数据
        conversations = group_conversations_by_id(json_data)

        # 处理每个分组的对话并保存结果
        process_conversations(conversations, output_file, error_file)



if __name__ == "__main__":
    # 输入 JSON 文件路径和输出文件路径
    input_folder = "E:/devwildchat/data/test"  # 输入文件夹路径
    output_folder = "E:/devwildchat/data/gpt-4o-mini-result-3"  # 输出文件夹路径
    error_folder = "E:/devwildchat/data/gpt-4o-mini-error-result"

    # 执行主函数
    main(input_folder, output_folder, error_folder)
