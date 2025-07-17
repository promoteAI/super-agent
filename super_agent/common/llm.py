from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
from typing import AsyncGenerator
from google.adk.models.base_llm import BaseLlm
from google.adk.models.llm_request import LlmRequest
from google.adk.models.llm_response import LlmResponse
from google.genai import types

def get_openai_chat_model(
    model_name: str = "gemma2",
    temperature: float = 0.0,
    base_url: str = "http://10.102.32.39:9999/v1",
    api_key: str = "gpustack_99bb71d05be3a1e8_cd2464128f60d27dc9a0b48c76f6f0f4"
):
    params = {
        "model": model_name,
        "temperature": temperature,
    }
    if base_url:
        params["base_url"] = base_url
    if api_key:
        params["api_key"] = api_key
    return ChatOpenAI(**params)

class OpenAICompatibleLlm(BaseLlm):
    """
    继承BaseLlm，实现调用自部署的OpenAI格式大模型
    """

    base_url: str = "http://10.102.32.39:9999/v1"
    api_key: str = "gpustack_99bb71d05be3a1e8_cd2464128f60d27dc9a0b48c76f6f0f4"
    extra_params: dict = {}

    def __init__(
        self,
        model: str="qwen-max",
        base_url: str="https://dashscope.aliyuncs.com/compatible-mode/v1",
        api_key:str="sk-1138e3030a6348c1b95b161d0c468ecd",
        **kwargs
    ):
        # 由于BaseLlm继承自pydantic.BaseModel，不能直接设置未声明的属性
        super().__init__(model=model)
        object.__setattr__(self, "base_url", base_url)
        object.__setattr__(self, "api_key", api_key)
        object.__setattr__(self, "extra_params", kwargs)

    @classmethod
    def supported_models(cls) -> list[str]:
        # 可以根据需要返回支持的模型正则表达式
        return [".*"]

    async def generate_content_async(
        self, llm_request: LlmRequest, stream: bool = False
    ) -> AsyncGenerator[LlmResponse, None]:
        """
        调用自部署的OpenAI格式大模型，返回生成内容
        """
        import httpx

        # 构造OpenAI格式的请求
        messages = []
        for content in llm_request.contents:
            if content.role == "user":
                role = "user"
            elif content.role == "assistant":
                role = "assistant"
            else:
                role = content.role
            text = ""
            for part in content.parts:
                if hasattr(part, "text") and part.text:
                    text += part.text
            messages.append({"role": role, "content": text})

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": getattr(llm_request.config, "temperature", 0.0),
            "stream": stream,
        }
        # 允许额外参数
        payload.update(self.extra_params)

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        async with httpx.AsyncClient(base_url=self.base_url, timeout=60) as client:
            if stream:
                async with client.stream("POST", "/chat/completions", json=payload, headers=headers) as response:
                    async for line in response.aiter_lines():
                        if not line or not line.startswith("data:"):
                            continue
                        data = line.removeprefix("data:").strip()
                        if data == "[DONE]":
                            break
                        import json
                        chunk = json.loads(data)
                        if "choices" in chunk and chunk["choices"]:
                            delta = chunk["choices"][0].get("delta", {})
                            content = delta.get("content", "")
                            if content:
                                # 这里修正为LlmResponse的内容字段名为"content"，而不是"contents"
                                yield LlmResponse(
                                    content=types.Content(
                                        role="assistant",
                                        parts=[types.Part(text=content)]
                                    )
                                )
            else:
                response = await client.post("/chat/completions", json=payload, headers=headers)
                response.raise_for_status()
                result = response.json()
                if "choices" in result and result["choices"]:
                    content = result["choices"][0]["message"]["content"]
                    # 这里修正为LlmResponse的内容字段名为"content"，而不是"contents"
                    yield LlmResponse(
                        content=types.Content(
                            role="assistant",
                            parts=[types.Part(text=content)]
                        )
                    )