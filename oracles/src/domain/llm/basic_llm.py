from typing import List
from typing import Optional

import backoff
import openai
from openai import AsyncOpenAI
from openai.types.chat import ChatCompletion

import settings
from src.domain.llm.utils import TIMEOUT


@backoff.on_exception(
    backoff.expo, (openai.RateLimitError, openai.APITimeoutError), max_tries=3
)
async def execute(model: str, messages: List[dict]) -> Optional[str]:
    client = AsyncOpenAI(
        api_key=settings.OPEN_AI_API_KEY,
        timeout=TIMEOUT,
    )
    chat_completion: ChatCompletion = await client.chat.completions.create(
        messages=messages,
        model=model,
    )
    return chat_completion.choices[0].message.content
