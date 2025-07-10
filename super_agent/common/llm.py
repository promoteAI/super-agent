from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage

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