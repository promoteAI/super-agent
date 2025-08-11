from python_a2a import A2AServer, agent, run_server, TaskStatus, TaskState,Message, TextContent,MessageRole
import os
from collections.abc import AsyncGenerator
from typing import Any
from openai import OpenAI
from super_agent.openai_cli.client import get_client
from super_agent.settings import settings

def ensure_llama3_exists(model_name: str):
    """
    检查本地是否存在指定的模型，如果不存在则使用ollama拉取部署。
    """
    import subprocess
    try:
        result = subprocess.run(
            ["ollama", "list"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            encoding="utf-8"
        )
        if result.returncode != 0:
            print("无法执行ollama list，请确保ollama已安装并在PATH中。")
            return False
        if model_name not in result.stdout:
            print(f"本地未检测到{model_name}模型，正在使用ollama拉取...")
            pull_result = subprocess.run(
                ["ollama", "pull", model_name],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                encoding="utf-8"
            )
            if pull_result.returncode != 0:
                print(f"ollama拉取{model_name}失败：{pull_result.stderr}")
                return False
            print(f"{model_name}模型拉取完成。")
        else:
            print(f"{model_name}模型已存在。")
        return True
    except Exception as e:
        print(f"检查或拉取{model_name}模型时发生异常：{e}")
        return False

@agent(
    name="Weather Agent",
    description="Provides weather information",
    version="1.0.0"
)
class WeatherAgent(A2AServer):
    # 显式声明 _use_google_a2a 属性，防止 AttributeError
    _use_google_a2a = False

    def __init__(self):
        # 检查并确保llama3.2模型存在
        model_name = os.getenv("MODEL_NAME", "llama3.2")
        ensure_llama3_exists(model_name=model_name)
        self.client = get_client(
            OpenAI, options=settings.openai_model_config
        )

    def handle_message(self, message: Message) -> Message:
        """
        Handle standard (non-streaming) message requests.
        
        Args:
            message: The incoming message
            
        Returns:
            The response message
        """
        # Extract query from message
        query = message.content.text if hasattr(message.content, "text") else "No query provided"
        
        # Generate complete response
        response_text = (
            f"This is a non-streaming response. For streaming, use the /stream endpoint. "
            f"Your query was: '{query}'"
        )
        
        print(f"[Server] Non-streaming response generated ({len(response_text)} chars)")
        
        # Return as a complete message
        return Message(
            content=TextContent(text=response_text),
            role=MessageRole.AGENT,
            parent_message_id=message.message_id,
            conversation_id=message.conversation_id
        )
    async def stream_response(self, message) -> AsyncGenerator[str, None]:
        query = message.content.text if hasattr(message.content, "text") else "No query provided"
        messages = [
            {
                "role": "system",
                "content": (
                    "你是一名专业的天气助手，擅长提供各地的实时天气信息。"
                    "请根据用户提供的地点，简明扼要地用中文回答当前天气状况。"
                    "如无法获取真实天气，请合理模拟并说明。"
                )
            },
            {
                "role": "user",
                "content": query
            }
        ]
        response = self.client.chat.completions.create(
            model=os.getenv("MODEL_NAME", "llama3.2"),
            messages=messages,
            temperature=0.7,
            stream=True
        )
        for chunk in response:
            delta = getattr(chunk.choices[0], "delta", None)
            if delta and getattr(delta, "content", None):
                content = delta.content
                yield content

# 启动服务
if __name__ == "__main__":
    agent = WeatherAgent()
    run_server(agent, port=5000)