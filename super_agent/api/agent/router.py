"""Agent service router."""

import asyncio
import uuid
from typing import AsyncGenerator, Dict, List
import httpx

from a2a.server.events.event_consumer import EventConsumer
from a2a.server.events.event_queue import EventQueue
from a2a.types import AgentCard, Role
from a2a.utils.message import get_message_text
from ag_ui.core import (
    EventType,
    RunAgentInput,
    RunFinishedEvent,
    RunStartedEvent,
    TextMessageContentEvent,
    TextMessageEndEvent,
    TextMessageStartEvent,
    UserMessage,
)
from ag_ui.encoder import EventEncoder
from fastapi import APIRouter, HTTPException,Request
from fastapi.responses import StreamingResponse

from super_agent.agents.registry import agent_registry

router = APIRouter(prefix="/agent", tags=["agent"])


@router.get("/", description="List all agents.")
async def list_agents() -> List[AgentCard]:
    """List all available agents."""
    return [agent.card for agent in agent_registry]


@router.get("/{agentId}", description="Get agent details by ID.")
async def get_agent(agentId: str) -> AgentCard:  # noqa: N803
    """Get details of a specific agent by its ID."""
    if agentId not in agent_registry:
        raise HTTPException(status_code=404, detail="Agent not found")

    agent = agent_registry.get_agent(agentId)
    if agent is None:
        raise HTTPException(status_code=404, detail="Agent not found")
    return agent.card


# In-memory store mapping job IDs to generators
job_generators: Dict[str, AsyncGenerator[str, None]] = {}


async def process_message(
    agentId: str, message: RunAgentInput  # noqa: N803
) -> AsyncGenerator[str, None]:
    """Process a user message for a given agent and streams Server-Sent Events (SSE) representing the agent's response.

    This coroutine yields encoded SSE events for the following stages:
        - Run started
        - Assistant message start
        - Assistant message content (streamed in chunks)
        - Assistant message end
        - Run finished

    Args:
        agentId (str): The unique identifier of the agent to execute.
        message (RunAgentInput): The input message containing user content, thread ID, and run ID.

    Yields:
        str: Encoded SSE event strings representing the progress and content of the agent's response.

    Raises:
        Any exceptions raised by the agent execution or event streaming will propagate.

    """
    # Create an event encoder to properly format SSE events
    encoder = EventEncoder()

    # Send run started event
    yield encoder.encode(
        RunStartedEvent(
            type=EventType.RUN_STARTED,
            thread_id=message.thread_id,
            run_id=message.run_id,
        )
    )

    # Generate a message ID for the assistant's response
    message_id = uuid.uuid4().hex

    # Create a streaming completion request
    queue = EventQueue()
    last_message_content = None
    last_message_role = None
    if message.messages and len(message.messages) > 0:
        last_message = message.messages[-1]
        last_message_content = last_message.content
    task = asyncio.create_task(
        agent_registry.execute_agent(
            agentId,
            queue=queue,
            options={
                "message_id": message_id,
                "role": Role.user,
                "text": last_message_content,
                "thread_id": message.thread_id,
            },
        )
    )

    consumer = EventConsumer(queue)
    task.add_done_callback(consumer.agent_task_callback)
    started = False
    async for event in consumer.consume_all():
        print("event",event)
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

        yield encoder.encode(
            TextMessageContentEvent(
                type=EventType.TEXT_MESSAGE_CONTENT,
                message_id=message_id,
                delta=get_message_text(event),
            )
        )

    # Send text message end event
    yield encoder.encode(
        TextMessageEndEvent(type=EventType.TEXT_MESSAGE_END, message_id=message_id)
    )

    # Send run finished event
    yield encoder.encode(
        RunFinishedEvent(
            type=EventType.RUN_FINISHED,
            thread_id=message.thread_id,
            run_id=message.run_id,
        )
    )

async def process_stream_message(
    agentId: str, message: RunAgentInput  # noqa: N803
) -> AsyncGenerator[str, None]:
    """
    参考loop_client.py，使用A2AClient发送流式请求，并将响应内容以SSE格式返回。
    针对send_message_streaming流式延迟很久的问题，去除await asyncio.sleep(0.1)以减少延迟。
    """
    import httpx
    from a2a.client import A2AClient
    from a2a.types import MessageSendParams, SendStreamingMessageRequest

    encoder = EventEncoder()

    # 发送run started事件
    yield encoder.encode(
        RunStartedEvent(
            type=EventType.RUN_STARTED,
            thread_id=message.thread_id,
            run_id=message.run_id,
        )
    )

    # 生成assistant消息ID
    message_id = uuid.uuid4().hex

    # 获取用户输入内容
    last_message_content = None
    if message.messages and len(message.messages) > 0:
        last_message = message.messages[-1]
        last_message_content = last_message.content

    # 构造A2A消息参数
    send_message_payload = {
        'message': {
            'role': 'user',
            'parts': [{'type': 'text', 'text': last_message_content}],
            'messageId': message_id,
        },
    }

    # 使用A2AClient发送流式请求
    async with httpx.AsyncClient() as httpx_client:
        client = A2AClient(
            httpx_client,
            url='http://localhost:10001'  # TODO: 可根据agentId动态路由
        )
        streaming_request = SendStreamingMessageRequest(
            id=uuid.uuid4().hex,
            params=MessageSendParams(**send_message_payload)
        )
        stream_response = client.send_message_streaming(streaming_request)

        started = False
        async for chunk in stream_response:
            print(chunk)
            # 首次发送assistant消息开始事件
            if not started:
                yield encoder.encode(
                    TextMessageStartEvent(
                        type=EventType.TEXT_MESSAGE_START,
                        message_id=message_id,
                        role="assistant",
                    )
                )
                started = True

            # 解析chunk内容
            data = chunk.model_dump(mode='json', exclude_none=True)
            delta = ""
            if data["result"].get("artifact"):
                delta = data["result"]["artifact"]["parts"][0]["text"]
            
            # 去除延迟，提升流式响应速度
            # await asyncio.sleep(0.1)
            if delta:
                yield encoder.encode(
                    TextMessageContentEvent(
                        type=EventType.TEXT_MESSAGE_CONTENT,
                        message_id=message_id,
                        delta=delta,
                    )
                )

    # assistant消息结束
    yield encoder.encode(
        TextMessageEndEvent(type=EventType.TEXT_MESSAGE_END, message_id=message_id)
    )

    # run finished事件
    yield encoder.encode(
        RunFinishedEvent(
            type=EventType.RUN_FINISHED,
            thread_id=message.thread_id,
            run_id=message.run_id,
        )
    )

@router.post(
    "{agentId}/start", description="Send new chat message and start processing."
)
async def send_message(
    agentId: str,  # noqa: N803
    message: RunAgentInput,
):
    """Send a new chat message."""
    # Generate a unique job id
    job_id = message.run_id
    # Store the generator for streaming responses.
    # job_generators[job_id] = process_message(agentId, message)
    job_generators[job_id] = process_stream_message(agentId, message)
    # Return the job id to the client.
    return {"runId": job_id}


@router.get("/stream/{runId}", description="Stream chat message updates via SSE.")
async def stream_message(runId: str):  # noqa: N803
    """Return an SSE stream for the provided job id."""
    generator = job_generators.get(runId)
    if generator is None:
        raise HTTPException(status_code=404, detail="Job not found")
    del job_generators[runId]
    return StreamingResponse(generator, media_type="text/event-stream")

@router.post("/agentic_a2a_chat")
async def agui_send_message_streaming(input_data: RunAgentInput, request: Request):
    """
    AG-UI协议流式消息处理接口
    """
    print("input_data:",input_data)
    # 简单示例：根据关键词选择agent
    agent_id = "search_query_agent"
    # 发送启动消息请求
    runId = (await send_message(agentId=agent_id, message=input_data))["runId"]

    # 获取流式响应
    return await stream_message(runId)    
