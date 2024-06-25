import json
import time
import backoff
from typing import Optional


from openai.types.completion_usage import CompletionUsage
from openai.types.chat import ChatCompletion
from openai.types.chat.chat_completion import Choice
from openai.types.chat.chat_completion import ChatCompletion
from openai.types.chat.chat_completion_message import ChatCompletionMessage
from openai.types.chat.chat_completion_message_tool_call import Function
from openai.types.chat.chat_completion_message_tool_call import (
    ChatCompletionMessageToolCall,
)
import anthropic
from anthropic import AsyncAnthropic, NOT_GIVEN

from src.entities import Chat
from src.entities import PromptType
from src.entities import LlmConfig

import settings




@backoff.on_exception(
    backoff.expo, (anthropic.RateLimitError, anthropic.APITimeoutError), max_tries=3
)
async def execute(chat: Chat) -> Optional[ChatCompletion]:
    client = AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
    system_prompt = NOT_GIVEN
    messages = chat.messages
    if messages[0]["role"] == "system":
        system_prompt = messages[0]["content"]
        messages = messages[1:]

    try:
        tools = []
        for tool in chat.config.tools:
            tools.append(
                {
                    "name": tool["function"]["name"],
                    "description": tool["function"]["description"],
                    "input_schema": tool["function"]["parameters"],
                }
            )
    except:
        tools = NOT_GIVEN
    message = await client.messages.create(
        max_tokens=chat.config.max_tokens or 4096,
        messages=messages,
        model=chat.config.model,
        stop_sequences=chat.config.stop or NOT_GIVEN,
        system=system_prompt,
        temperature=chat.config.temperature or NOT_GIVEN,
        tool_choice=(
            {"type": "auto"} if chat.config.tool_choice == "auto" else NOT_GIVEN
        ),
        tools=tools,
        top_p=chat.config.top_p or NOT_GIVEN,
    )
    finish_reason = "stop"
    match message.stop_reason:
        case "end_turn":
            finish_reason = "stop"
        case "max_tokens":
            finish_reason = "length"
        case "stop_sequence":
            finish_reason = "stop"
        case "tool_use":
            finish_reason = "tool_calls"
    content = message.content[0].text if message.content[0].type == "text" else None
    tool_calls = None
    if len(message.content) > 1 and message.content[1].type == "tool_use":
        function = Function(
            name=message.content[1].name,
            arguments=json.dumps(message.content[1].input),
        )
        tool_call = ChatCompletionMessageToolCall(
            id=message.content[1].id,
            function=function,
            type="function",
        )
        tool_calls = [tool_call]
    completion_message = ChatCompletionMessage(
        content=content,
        role="assistant",
        function_call=None,
        tool_calls=tool_calls,
    )
    choice = Choice(
        finish_reason=finish_reason,
        index=0,
        message=completion_message,
    )
    return ChatCompletion(
        id=message.id,
        choices=[choice],
        created=int(time.time()),
        model=chat.config.model,
        object="chat.completion",
        usage=CompletionUsage(
            completion_tokens=message.usage.output_tokens,
            prompt_tokens=message.usage.input_tokens,
            total_tokens=message.usage.input_tokens + message.usage.output_tokens,
        ),
    )
