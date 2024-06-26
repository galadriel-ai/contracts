from typing import get_args

import openai

from src.entities import Chat
from src.entities import PromptType
from src.entities import AnthropicModelType
from src.domain.llm import basic_llm
from src.domain.llm import groq_llm
from src.domain.llm import openai_llm
from src.domain.llm import anthropic_llm
from src.domain.llm.entities import LLMResult


async def execute(model: str, chat: Chat) -> LLMResult:
    try:
        if not chat.config or chat.prompt_type == PromptType.DEFAULT:
            if chat.config and chat.config.model in get_args(AnthropicModelType):
                response = await anthropic_llm.execute(chat)
            else:
                response = await basic_llm.execute(model, messages=chat.messages)
        elif chat.prompt_type == PromptType.OPENAI:
            response = await openai_llm.execute(chat)
        elif chat.prompt_type == PromptType.GROQ:
            response = await groq_llm.execute(chat)
        else:
            response = "Invalid promptType"
        return LLMResult(
            chat_completion=response,
            error="",
        )
    except openai.APIError as api_error:
        print(f"OpenAI API error: {api_error}", flush=True)
        return LLMResult(
            chat_completion=None,
            error=api_error.message,
        )
    except Exception as e:
        print(f"LLM generation error: {e}", flush=True)
        return LLMResult(
            chat_completion=None,
            error=str(e),
        )
