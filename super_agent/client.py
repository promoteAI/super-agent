import logging
from typing import Any
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse

import httpx

from a2a.client import A2ACardResolver, A2AClient
from a2a.types import (
    AgentCard,
    MessageSendParams,
    SendStreamingMessageRequest,
)
from a2a.utils.message import get_message_text

from ag_ui.core import RunAgentInput  # 假设ag_ui.core已安装
from ag_ui.encoder import EventEncoder
from ag_ui.core import (
    RunStartedEvent,
    RunFinishedEvent,
    EventType,
    TextMessageStartEvent,
    TextMessageContentEvent,
    TextMessageEndEvent,
)
import json
import asyncio

app = FastAPI()

# 日志配置
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

PUBLIC_AGENT_CARD_PATH = '/.well-known/agent.json'
EXTENDED_AGENT_CARD_PATH = '/agent/authenticatedExtendedCard'
BASE_URL = 'http://localhost:10102'

async def get_final_agent_card(httpx_client) -> AgentCard:
    resolver = A2ACardResolver(
        httpx_client=httpx_client,
        base_url=BASE_URL,
    )
    final_agent_card_to_use: AgentCard | None = None
    try:
        logger.info(
            f'尝试获取公共 agent card: {BASE_URL}{PUBLIC_AGENT_CARD_PATH}'
        )
        _public_card = await resolver.get_agent_card()
        logger.info('成功获取公共 agent card:')
        logger.info(_public_card.model_dump_json(indent=2, exclude_none=True))
        final_agent_card_to_use = _public_card
        logger.info('使用公共 agent card 初始化 client（默认）')

        if _public_card.supportsAuthenticatedExtendedCard:
            try:
                logger.info(
                    f'公共 card 支持扩展卡，尝试获取: {BASE_URL}{EXTENDED_AGENT_CARD_PATH}'
                )
                auth_headers_dict = {
                    'Authorization': 'Bearer dummy-token-for-extended-card'
                }
                _extended_card = await resolver.get_agent_card(
                    relative_card_path=EXTENDED_AGENT_CARD_PATH,
                    http_kwargs={'headers': auth_headers_dict},
                )
                logger.info('成功获取扩展 agent card:')
                logger.info(_extended_card.model_dump_json(indent=2, exclude_none=True))
                final_agent_card_to_use = _extended_card
                logger.info('使用扩展 agent card 初始化 client')
            except Exception as e_extended:
                logger.warning(
                    f'获取扩展 agent card 失败: {e_extended}，将继续使用公共卡。',
                    exc_info=True,
                )
        elif _public_card:
            logger.info('公共卡不支持扩展卡，使用公共卡。')
    except Exception as e:
        logger.error(
            f'获取公共 agent card 发生严重错误: {e}', exc_info=True
        )
        raise RuntimeError(
            '无法获取公共 agent card，无法继续。'
        ) from e
    return final_agent_card_to_use

@app.post("/agentic_a2a_chat")
async def agui_send_message_streaming(input_data: RunAgentInput, request: Request):
    """
    AG-UI协议：流式消息发送接口
    输入参数：RunAgentInput（pydantic模型），request（FastAPI Request对象）
    返回参数：StreamingResponse，内容为AG-UI协议格式的事件流
    """
    logger.info(f"请求参数:{input_data},{request}")
    # 获取accept头，决定返回内容类型
    accept_header = request.headers.get("accept")
    encoder = EventEncoder(accept=accept_header)

    async def event_generator():
        # 在生成器内部创建httpx_client和A2AClient，保证流式期间client不关闭
        async with httpx.AsyncClient(timeout=120) as httpx_client:
            try:
                agent_card = await get_final_agent_card(httpx_client)
                print("AgentCard", agent_card)
                client = A2AClient(httpx_client=httpx_client, agent_card=agent_card)

                # 构造A2A协议的消息内容
                # 这里只取最后一条用户消息作为输入
                user_message = None
                if input_data.messages and len(input_data.messages) > 0:
                    for msg in reversed(input_data.messages):
                        if getattr(msg, "role", None) == "user":
                            user_message = msg
                            break
                user_text = getattr(user_message, "content", "我想要去海南旅游")

                send_message_payload: dict[str, Any] = {
                    'message': {
                        'role': 'user',
                        'parts': [
                            {'kind': 'text', 'text': user_text}
                        ],
                        'messageId': uuid4().hex,
                        'contextId': input_data.thread_id,
                    },
                }
                streaming_request = SendStreamingMessageRequest(
                    id=str(uuid4()), params=MessageSendParams(**send_message_payload)
                )
                stream_response = client.send_message_streaming(streaming_request)

                # 发送run started事件
                yield encoder.encode(
                    RunStartedEvent(
                        type=EventType.RUN_STARTED,
                        thread_id=input_data.thread_id,
                        run_id=input_data.run_id
                    ),
                )
                message_id = uuid4().hex
                # 逐步流式返回A2A协议的chunk，转换为AG-UI协议的TextMessageContentEvent
                started=False
                async for chunk in stream_response:
                    try:
                        if not started:
                            # Send text message start event
                            yield encoder.encode(
                                TextMessageStartEvent(
                                    type=EventType.TEXT_MESSAGE_START,
                                    message_id=message_id,
                                    role="assistant",
                                )
                            )
                            started = True
                        print("Chunk:", chunk.root.result)
                        chunk=chunk.root
                        # 解析A2A协议的chunk，转换为AG-UI事件
                        text = ""

                        # 1. 如果chunk有result字段，说明是一次性响应（如SendStreamingMessageSuccessResponse）
                        if hasattr(chunk, "result"):
                            result = getattr(chunk, "result", None)
                            # result为TaskStatusUpdateEvent（含status.message）
                            if result and hasattr(result, "status") and hasattr(result.status, "message"):
                                msg = result.status.message
                                if hasattr(msg, "parts") and msg.parts:
                                    part = msg.parts[0]
                                    if hasattr(part, "root") and hasattr(part.root, "text"):
                                        text = part.root.text
                                    elif isinstance(part, dict) and "text" in part:
                                        text = part["text"]
                                if not text:
                                    try:
                                        text = msg.model_dump_json(exclude_none=True)
                                    except Exception:
                                        text = str(msg)
                            else:
                                # 其他类型，直接序列化
                                text = str(chunk)
                        # 2. 如果chunk有text字段
                        elif hasattr(chunk, "text"):
                            text = chunk.text
                        # 3. 如果chunk有parts字段
                        elif hasattr(chunk, "parts") and chunk.parts:
                            part = chunk.parts[0]
                            text = getattr(part, "text", "")
                        # 4. 如果chunk有message且message有parts
                        elif hasattr(chunk, "message") and hasattr(chunk.message, "parts"):
                            part = chunk.message.parts[0]
                            text = getattr(part, "text", "")

                        print("提取的文本:",text)
                        # 输出AG-UI事件
                        yield encoder.encode(
                            TextMessageContentEvent(
                                type=EventType.TEXT_MESSAGE_CONTENT,
                                message_id=message_id,
                                delta=text if text else ""
                            )
                        )
                    except (asyncio.CancelledError, GeneratorExit):
                        logger.info("前端已关闭连接，停止发送流式内容。")
                        break
                    except Exception as e:
                        logger.warning(f"流式内容发送异常: {e}", exc_info=True)
                        break
                # 发送TextMessageEndEvent
                yield encoder.encode(
                    TextMessageEndEvent(
                        type=EventType.TEXT_MESSAGE_END,
                        message_id=message_id
                    )
                )
                # 发送run finished事件
                yield encoder.encode(
                    RunFinishedEvent(
                        type=EventType.RUN_FINISHED,
                        thread_id=input_data.thread_id,
                        run_id=input_data.run_id
                    ),
                )
            except (asyncio.CancelledError, GeneratorExit):
                logger.info("前端已关闭连接，停止事件生成。")
                return
            except Exception as e:
                logger.error(f"事件生成异常: {e}", exc_info=True)
                return

    return StreamingResponse(event_generator(), media_type=encoder.get_content_type())

# 调用agui_send_message_streaming测试
if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
    # import asyncio
    # from ag_ui.core import RunAgentInput, UserMessage
    # from uuid import uuid4

    # class DummyRequest:
    #     def __init__(self):
    #         self.headers = {"accept": "application/json"}

    # async def test_agui_send_message_streaming():
    #     # 构造测试输入，补全所有必需字段，messages用UserMessage实例
    #     input_data = RunAgentInput(
    #         thread_id="test_thread",
    #         run_id="test_run",
    #         state={},  # 必填字段，填空字典
    #         tools=[],  # 必填字段，填空列表
    #         context=[],  # 必填字段，填空字典
    #         forwardedProps={},  # 必填字段，填空字典
    #         messages=[
    #             UserMessage(
    #                 id=uuid4().hex,  # 必填字段，补充id
    #                 role="user",
    #                 content="你好，帮我推荐海南旅游路线"
    #             )
    #         ]
    #     )
    #     request = DummyRequest()
    #     # 调用接口
    #     response = await agui_send_message_streaming(input_data, request)
    #     print("StreamingResponse内容类型:", response.media_type)
    #     # 读取流式内容
    #     async for chunk in response.body_iterator:
    #         print(chunk.decode("utf-8") if isinstance(chunk, bytes) else chunk)

    # asyncio.run(test_agui_send_message_streaming())