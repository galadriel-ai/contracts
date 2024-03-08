from typing import Optional

from openai import AsyncOpenAI
from openai.types.chat import ChatCompletion
from src.entities import Chat

import settings


async def execute(model: str, chat: Chat) -> Optional[str]:
    try:
        client = AsyncOpenAI(
            api_key=settings.OPEN_AI_API_KEY,
        )
        chat_completion: ChatCompletion = await client.chat.completions.create(
            messages=chat.messages,
            model=model,
        )
        return chat_completion.choices[0].message.content
    except Exception as exc:
        print(f"OPENAI Exception: {exc}", flush=True)
