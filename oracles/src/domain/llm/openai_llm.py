import backoff
from typing import Optional

import openai
from openai import AsyncOpenAI
from openai.types.chat import ChatCompletion

from src.entities import Chat
from src.domain.llm.utils import TIMEOUT
import settings


@backoff.on_exception(
    backoff.expo, (openai.RateLimitError, openai.APITimeoutError), max_tries=3
)
async def execute(chat: Chat) -> Optional[ChatCompletion]:
    client = AsyncOpenAI(
        api_key=settings.OPEN_AI_API_KEY,
        timeout=TIMEOUT,
    )
    chat_completion: ChatCompletion = await client.chat.completions.create(
        messages=chat.messages,
        model=chat.config.model,
        frequency_penalty=chat.config.frequency_penalty,
        logit_bias=chat.config.logit_bias,
        max_tokens=chat.config.max_tokens,
        presence_penalty=chat.config.presence_penalty,
        response_format=chat.config.response_format,
        seed=chat.config.seed,
        # TODO gpt-4-turbo currently broken, keep the default for now
        # stop=chat.config.stop,
        temperature=chat.config.temperature,
        top_p=chat.config.top_p,
        tools=chat.config.tools,
        tool_choice=chat.config.tool_choice,
        user=chat.config.user,
    )
    assert (
        chat_completion.choices[0].message.content
        or chat_completion.choices[0].message.tool_calls
    )
    return chat_completion
