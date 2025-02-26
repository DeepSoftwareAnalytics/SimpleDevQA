import requests
import logging
from openai import OpenAI


# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 配置 API 密钥和重试设置
# gpt-4o
# api_key = "sk-cW2f696POnjSzdFw420212Fb32034c299dA72878F918D5A8"
api_key = "sk-Os9RkOC334PpaLdS725a9082E0Bd4aA381810dC3EcE9Ff3b"
# deepseek
# api_key = "sk-107e20a23e624cfdb63bd85638bf9c83"
# perplexity
api_key2 = "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"

base_url = "https://api.gptapi.us/v1/chat/completions"
# base_url = "https://api.deepseek.com/chat/completions"
base_url2 = "https://api.perplexity.ai"

max_retries = 3


def query_llm(prompt, system_prompt="You are a helpful assistant.", model="gpt-4o-mini"):
    """使用 GPT-4 API 发送请求并返回响应"""
    # 将 context_data 转换为字符串格式，作为上下文
    # context = json.dumps(context_data, ensure_ascii=False, indent=2)
    # results = json.dumps(result, ensure_ascii=False, indent=2)
    # context = eval(context_data)
    # print(result)
    # 构建请求配置
    config = {
        "model": model,  # 明确指定使用的模型
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ],
        # "max_tokens": 2000,
        "temperature": 0.7
    }
    # print(config)
    # exit()

    ret = None
    retries = 0
    # 使用重试机制调用 API
    while ret is None and retries < max_retries:
        try:
            logger.info("Creating API request")
            # async with session.post(base_url, json=config, headers={
            #     'Authorization': f"Bearer {api_key}",  #api_key,
            #     "Content-Type": "application/json"
            # }) as response:
            response = requests.post(
                    base_url,
                    json=config,
                    headers={
                        'Authorization': api_key,
                        # "anthropic-version": "2023-06-01",
                        "Content-Type": "application/json"
                    }
                )
            # if response.status == 200:
            ret = response.json()
            #     return ret['choices'][0]['message']['content']
            # else:
            #     logger.warning(f"Invalid API response: {response.status}")
            #     retries += 1
            #     ret = None
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


def query_llm2(prompt, system_prompt="You are a helpful assistant.", model="sonar-pro"):
    """使用 GPT-4 API 发送请求并返回响应"""
    try:
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ]

        client = OpenAI(api_key=api_key2, base_url=base_url2)

        # chat completion without streaming
        response = client.chat.completions.create(
            model=model,
            messages=messages,
        )
        # print(response)
        # response = response.json()
        # return response["choices"][0]["message"]["content"]
        return response.choices[0].message.content

    except Exception as e:
        logger.error(f"Error querying GPT-4 API: {str(e)}")

    return None