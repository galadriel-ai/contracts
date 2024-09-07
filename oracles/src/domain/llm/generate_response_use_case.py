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
from src.repositories.langchain_knowledge_base_repository import LangchainKnowledgeBaseRepository


async def execute(model: str, langchain_repository: LangchainKnowledgeBaseRepository, chat: Chat) -> LLMResult:
    try:
        num_docs = 0
        if not chat.config or chat.prompt_type == PromptType.DEFAULT:
            if chat.config and chat.config.model in get_args(AnthropicModelType):
                response, num_docs, chat.system_prompt = await anthropic_llm.execute(langchain_repository, chat)
            else:
                response, num_docs, chat.system_prompt = await basic_llm.execute(langchain_repository, model, messages=chat.messages)
        elif chat.prompt_type == PromptType.OPENAI:
            response, num_docs, chat.system_prompt = await openai_llm.execute(langchain_repository, chat)
        elif chat.prompt_type == PromptType.GROQ:
            response, num_docs, chat.system_prompt = await groq_llm.execute(langchain_repository,chat)
        else:
            response = "Invalid promptType"
        return LLMResult(
            chat_completion=response,
            system_prompt=chat.system_prompt,
            num_documents=num_docs,
            error="",
        )
    except openai.APIError as api_error:
        print(f"OpenAI API error: {api_error}", flush=True)
        return LLMResult(
            chat_completion=None,
            system_prompt={},
            num_documents=num_docs,
            error=api_error.message,
        )
    except Exception as e:
        print(f"LLM generation error: {e}", flush=True)
        return LLMResult(
            chat_completion=None,
            system_prompt={},
            num_documents=num_docs,
            error=str(e),
        )
