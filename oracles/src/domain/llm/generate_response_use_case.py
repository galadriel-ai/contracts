import backoff
from typing import List
from typing import Optional

from openai import AsyncOpenAI
from openai import RateLimitError
from openai import APIError
from openai.types.chat import ChatCompletion
from src.entities import Chat
from src.domain.llm.entities import LLMResult

import settings


@backoff.on_exception(backoff.expo, RateLimitError)
async def _generate(model: str, messages: List[dict]) -> Optional[str]:
    client = AsyncOpenAI(
        api_key=settings.OPEN_AI_API_KEY,
    )
    chat_completion: ChatCompletion = await client.chat.completions.create(
        messages=messages,
        model=model,
    )
    return chat_completion.choices[0].message.content


async def execute(model: str, chat: Chat) -> LLMResult:
    try:
        response = await _generate(model=model, messages=chat.messages)
        return LLMResult(
            content=response,
            error="",
        )
    except APIError as api_error:
        print(f"OpenAI API error: {api_error}", flush=True)
        return LLMResult(
            content="",
            error=api_error.message,
        )
    except Exception as e:
        print(f"LLM generation error: {e}", flush=True)
        return LLMResult(
            content="",
            error=str(e),
        )
