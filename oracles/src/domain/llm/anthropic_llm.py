import json
import time
import backoff
from typing import List
from typing import Union
from typing import Optional


from openai.types.completion_usage import CompletionUsage
from openai.types.chat import ChatCompletion
from openai.types.chat import ChatCompletionToolParam
from openai.types.chat.chat_completion import Choice
from openai.types.chat.chat_completion import ChatCompletion
from openai.types.chat.chat_completion_message import ChatCompletionMessage
from openai.types.chat.chat_completion_message_tool_call import Function
from openai.types.chat.chat_completion_message_tool_call import (
    ChatCompletionMessageToolCall,
)
import anthropic
from anthropic import NotGiven
from anthropic import NOT_GIVEN
from anthropic import AsyncAnthropic
from anthropic.types import Message

from src.entities import Chat

import settings


@backoff.on_exception(
    backoff.expo, (anthropic.RateLimitError, anthropic.APITimeoutError), max_tries=3
)
async def execute(chat: Chat) -> Optional[ChatCompletion]:
    client = AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
    system_prompt = NOT_GIVEN
    messages = chat.messages

    if len(messages) > 0 and messages[0]["role"] == "system":
        system_prompt = messages[0]["content"]
        messages = messages[1:]
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
        tools=_convert_tool_definitions(chat.config.tools),
        top_p=chat.config.top_p or NOT_GIVEN,
    )

    return _convert_output_to_chat_completion(chat, message)


def _convert_output_to_chat_completion(
    chat: Chat, message: Message
) -> Optional[ChatCompletion]:
    content = message.content[0].text if message.content[0].type == "text" else None
    completion_message = ChatCompletionMessage(
        content=content,
        role="assistant",
        function_call=None,
        tool_calls=_convert_tool_calls(message),
    )
    choice = Choice(
        finish_reason=_convert_finish_reason(message.stop_reason),
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


def _convert_tool_definitions(
    tools: Optional[List[ChatCompletionToolParam]],
) -> Union[List[dict], NotGiven]:
    try:
        result = []
        for tool in tools:
            result.append(
                {
                    "name": tool["function"]["name"],
                    "description": tool["function"]["description"],
                    "input_schema": tool["function"]["parameters"],
                }
            )
        return result
    except:
        return NOT_GIVEN


def _convert_tool_calls(
    message: Message,
) -> Optional[List[ChatCompletionMessageToolCall]]:
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
        return [tool_call]


def _convert_finish_reason(finish_reason: str) -> str:
    match finish_reason:
        case "end_turn":
            return "stop"
        case "max_tokens":
            return "length"
        case "stop_sequence":
            return "stop"
        case "tool_use":
            return "tool_calls"
        case _:
            return "stop"
