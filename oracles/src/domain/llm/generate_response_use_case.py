import backoff
from typing import List
from typing import Optional

from openai import AsyncOpenAI
from openai import RateLimitError
from openai.types.chat import ChatCompletion
from src.entities import Chat

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


async def execute(model: str, chat: Chat) -> Optional[str]:
    try:
        return await _generate(model=model, messages=chat.messages)
    except Exception as exc:
        print(f"Exception: {exc}", flush=True)
