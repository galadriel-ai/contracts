from typing import List, Tuple, Union
from typing import Optional

import backoff
import openai
from openai import AsyncOpenAI
from openai.types.chat import ChatCompletion

import settings
from src.domain.llm.utils import TIMEOUT
from src.repositories.langchain_knowledge_base_repository import LangchainKnowledgeBaseRepository


@backoff.on_exception(
    backoff.expo, (openai.RateLimitError, openai.APITimeoutError), max_tries=3
)
async def execute(langchain_repository: LangchainKnowledgeBaseRepository ,model: str, messages: List[dict]) -> Tuple[Optional[str], int, dict[str, Union[str, dict[str, str]]], List[dict[str, Union[str, int]]]]:
    client = AsyncOpenAI(
        api_key=settings.OPEN_AI_API_KEY,
        timeout=TIMEOUT,
    )
    chat_completion: ChatCompletion = await client.chat.completions.create(
        messages=messages,
        model=model,
    )
    return chat_completion.choices[0].message.content, 0, {}, []
