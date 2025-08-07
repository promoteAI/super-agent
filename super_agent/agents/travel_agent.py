import json
import os
import sys

from collections.abc import AsyncGenerator
from typing import Any
from openai import OpenAI
from super_agent.openai.client import get_client
from super_agent.settings import settings


class TravelPlannerAgent:
    """travel planner Agent."""

    def __init__(self):
        """初始化旅行对话模型"""
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
                model="llama3.2",
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