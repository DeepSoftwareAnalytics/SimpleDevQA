import json
import os
import time
import random

import requests
import logging
from openai import OpenAI
import http.client

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 配置 API 密钥和重试设置
api_key = ""
api_key2 = ""
api_key3 = ""

base_url = ""
base_url2 = ""
base_url3 = ""
# 确保 API 地址正确
API_HOST = ""
API_ENDPOINT = ""

# 替换为你的 API key
API_KEY = ""
max_retries = 10


def query_llm(prompt, system_prompt="You are a helpful assistant.", model=""):
    """使用 GPT-4 API 发送请求并返回响应"""
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

    ret = None
    retries = 0
    # 使用重试机制调用 API
    while ret is None and retries < max_retries:
        try:
            logger.info("Creating API request")
            response = requests.post(
                    base_url,
                    json=config,
                    headers={
                        'Authorization': api_key,
                        "Content-Type": "application/json"
                    }
                )
            ret = response.json()
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


def query_llm2(prompt, system_prompt="You are a helpful assistant.", model=""):
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
        return response.choices[0].message.content

    except Exception as e:
        logger.error(f"Error querying GPT-4 API: {str(e)}")

    return None


def query_searchllm(prompt):
    """使用 GPT-4 API 发送请求并返回响应"""
    logger.info("Creating API request")
    conn = http.client.HTTPSConnection(API_HOST)
    headers = {
        "Authorization": f"Bearer {API_KEY}",  # 确保 API key 格式正确
        "Content-Type": "application/json"
    }

    data = {
        "max_results": 5,
        "query": prompt,
        "search_service": "google"
    }

    try:
        conn.request("POST", API_ENDPOINT, json.dumps(data), headers)
        response = conn.getresponse()

        # print("HTTP Status:", response.status)
        if response.status == 200:
            response_data = response.read().decode()
            # print("Response JSON:", json.loads(response_data))
            ret = json.loads(response_data)
            return ret
        else:
            print("Error response:", response.read().decode())

    except Exception as e:
        print("Request failed:", str(e))
    finally:
        conn.close()



def query_smallllm(prompt, system_prompt="You are a helpful assistant.", model=""):
    """使用 GPT-4 API 发送请求并返回响应"""
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


    ret = None
    retries = 0
    # 使用重试机制调用 API
    while ret is None and retries < max_retries:
        try:
            logger.info("Creating API request")
            response = requests.post(
                    base_url3,
                    json=config,
                    headers={
                        'Authorization': f"Bearer {api_key3}",
                        # "anthropic-version": "2023-06-01",
                        "Content-Type": "application/json"
                    }
                )
            ret = response.json()
            if 'choices' not in ret:
                logger.warning("Invalid API response, retrying...")
                ret = None
                retries += 1
            else:
                # 将结果添加到列表
                return ret['choices'][0]['message']['content']

        except Exception as e:
            logger.error(f"Error querying GPT-4 API: {str(e)}")
            ret = None
            retries += 1

    logger.error("Max retries reached. Unable to get a valid response.")
    return None