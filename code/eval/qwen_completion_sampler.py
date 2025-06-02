import base64
import time
from typing import Any

import openai
import requests
from openai import OpenAI
from types_local import MessageList, SamplerBase

OPENAI_SYSTEM_MESSAGE_API = "You are a helpful assistant."
OPENAI_SYSTEM_MESSAGE_API_CN = "你是一个智能助手。"
OPENAI_SYSTEM_MESSAGE_CHATGPT = (
    "You are ChatGPT, a large language model trained by OpenAI, based on the GPT-4 architecture."
    + "\nKnowledge cutoff: 2023-12\nCurrent date: 2024-04-01"
)


class QwenCompletionSampler(SamplerBase):
    """
    Sample from OpenAI's chat completion API
    """

    def __init__(
        self,
        model: str = "Qwen/Qwen2.5-7B-Instruct",
        system_message: str | None = None,
        temperature: float = 0.5,
        # max_tokens: int = 1024,
        api_key: str = "",
        base_url: str = "",
    ):
        # self.client = OpenAI(
        #     api_key=api_key,
        #     base_url=base_url,
        # )
        # using api_key=os.environ.get("OPENAI_API_KEY")  # please set your API_KEY
        self.base_url = base_url
        self.api_key = api_key
        self.model = model
        self.system_message = system_message
        self.temperature = temperature
        # self.max_tokens = max_tokens
        self.image_format = "url"

    def _handle_image(
        self, image: str, encoding: str = "base64", format: str = "png", fovea: int = 768
    ):
        new_image = {
            "type": "image_url",
            "image_url": {
                "url": f"data:image/{format};{encoding},{image}",
            },
        }
        return new_image

    def _handle_text(self, text: str):
        return {"type": "text", "text": text}

    def _pack_message(self, role: str, content: Any):
        return {"role": str(role), "content": content}

    def __call__(self, message_list: MessageList) -> str:
        if self.system_message:
            message_list = [self._pack_message("system", self.system_message)] + message_list
        trial = 0
        while True:
            try:
                # response = self.client.chat.completions.create(
                #     model=self.model,
                #     messages=message_list,
                #     temperature=self.temperature,
                #     # max_tokens=self.max_tokens,
                # )
                config = {
                    "model": self.model,  # 明确指定使用的模型
                    "messages": message_list
                    # "max_tokens": 2000,
                    # "temperature": 0.7
                }
                response = requests.post(
                    self.base_url,
                    json=config,
                    headers={
                        'Authorization': f"Bearer {self.api_key}",
                        # "anthropic-version": "2023-06-01",
                        "Content-Type": "application/json"
                    }
                )
                ret = response.json()
                if 'choices' not in ret:
                    print(f"Unexpected response structure: {ret}")
                    print("Message List:", message_list)
                    # exit()
                    return ""

                return ret['choices'][0]['message']['content']
            # NOTE: BadRequestError is triggered once for MMMU, please uncomment if you are reruning MMMU
            # except openai.BadRequestError as e:
            #     print("Bad Request Error", e)
            #     # return ""
            #     trial += 1
            #     if trial < 10:
            #         import random
            #         exception_backoff = random.random() * 2 * trial
            #         time.sleep(exception_backoff)
            #     else:
            #         return ""
                
            except Exception as e:
                print(
                    f"Rate limit exception so wait and retry {trial}",
                    e,
                )
                trial += 1
                if trial < 100:
                    exception_backoff = 2**trial  # expontial back off
                    time.sleep(exception_backoff)
                else:
                    return ""
                    
            # unknown error shall throw exception
