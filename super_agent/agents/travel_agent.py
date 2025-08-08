import json
import os
import sys
import subprocess

from collections.abc import AsyncGenerator
from typing import Any
from openai import OpenAI
from super_agent.openai.client import get_client
from super_agent.settings import settings


def ensure_llama3_exists():
    """
    检查本地是否存在llama3.2模型，如果不存在则使用ollama拉取部署。
    """
    try:
        # 检查llama3.2模型是否已存在
        result = subprocess.run(
            ["ollama", "list"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            encoding="utf-8"
        )
        if result.returncode != 0:
            print("无法执行ollama list，请确保ollama已安装并在PATH中。")
            return False

        # 检查输出中是否有llama3.2
        if "llama3:2" not in result.stdout and "llama3.2" not in result.stdout:
            print("本地未检测到llama3.2模型，正在使用ollama拉取...")
            pull_result = subprocess.run(
                ["ollama", "pull", "llama3:2"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                encoding="utf-8"
            )
            if pull_result.returncode != 0:
                print(f"ollama拉取llama3:2失败：{pull_result.stderr}")
                return False
            print("llama3.2模型拉取完成。")
        else:
            print("llama3.2模型已存在。")
        return True
    except Exception as e:
        print(f"检查或拉取llama3.2模型时发生异常：{e}")
        return False


class TravelPlannerAgent:
    """travel planner Agent."""

    def __init__(self):
        """初始化旅行对话模型"""
        # 检查并确保llama3.2模型存在
        model_name = os.getenv("MODEL_NAME", "llama3.2")
        if "llama3" in model_name:
            ensure_llama3_exists()
        self.client = get_client(
            OpenAI, options=settings.openai_model_config
        )

    async def stream(self, query: str) -> AsyncGenerator[dict[str, Any], None]:
        """
        使用OpenAI官方库的流式接口返回大模型的回复。
        """
        try:
            # 构造消息历史
            messages = [
                {
                    "role": "system",
                    "content": (
                        "你是一名专业的旅行助手，擅长行程规划、目的地信息和旅行建议。"
                        "你的目标是根据用户的偏好和约束，帮助他们制定愉快、安全且切实可行的旅行计划。\n"
                        "在提供信息时：\n"
                        "- 建议要具体且实用\n"
                        "- 考虑季节、预算和交通等因素\n"
                        "- 强调文化体验和地道活动\n"
                        "- 提供与目的地相关的实用旅行建议\n"
                        "- 信息清晰，适当使用标题和要点\n"
                        "行程规划时：\n"
                        "- 制定合理的每日计划，考虑景点间交通\n"
                        "- 兼顾热门景点与小众体验\n"
                        "- 包含大致时间安排和实际操作建议\n"
                        "- 推荐当地美食\n"
                        "- 考虑天气、活动和开放时间\n"
                        "始终保持热情、务实的语气，如有知识盲区请坦诚说明。"
                    )
                },
                {
                    "role": "user",
                    "content": query
                }
            ]

            # 使用OpenAI官方库流式生成回复
            response = self.client.chat.completions.create(
                model=os.getenv("MODEL_NAME", "llama3.2"),
                messages=messages,
                temperature=0.7,
                stream=True
            )

            # 注意：OpenAI官方库的流式返回是同步的可迭代对象，不支持async for
            content_buffer = ""
            for chunk in response:
                delta = getattr(chunk.choices[0], "delta", None)
                if delta and getattr(delta, "content", None):
                    content = delta.content
                    content_buffer += content
                    yield {"content": content, "done": False}
            yield {"content": "", "done": True}

        except Exception as e:
            print(f'error：{e!s}')
            yield {
                'content': '抱歉，处理您的请求时发生了错误。',
                'done': True,
            }