import os
from openai import OpenAI


class UniAPIClient:
    def __init__(self, api_key: str | None = None):
        """
        初始化 UniAPI 客户端
        优先级：
        1. 显式传入 api_key
        2. 环境变量 UNIAPI_KEY
        3. 环境变量 OPENAI_API_KEY
        """
        self.api_key = (
            api_key
            or os.getenv("UNIAPI_KEY")
            or os.getenv("OPENAI_API_KEY")
        )

        if not self.api_key:
            raise ValueError("请设置 UNIAPI_KEY 或 OPENAI_API_KEY")

        self.client = OpenAI(
            base_url="https://api.uniapi.io/v1",
            api_key=self.api_key,
        )

    def chat_completion(
        self,
        messages: list[dict],
        model: str = "gpt-4o-mini",
        temperature: float = 0.2,
        max_tokens: int = 2048,
    ) -> str:
        """
        统一的 Chat Completion 调用
        返回模型的 message.content（字符串）
        """
        resp = self.client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )

        return resp.choices[0].message.content
