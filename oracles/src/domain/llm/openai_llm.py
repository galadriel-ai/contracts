import backoff
from typing import Optional, List, Tuple, Union

import openai
from openai import AsyncOpenAI
from openai.types.chat import ChatCompletion
from langchain_core.documents import Document

from src.entities import Chat
from src.domain.llm.utils import TIMEOUT
from src.repositories.langchain_knowledge_base_repository import LangchainKnowledgeBaseRepository
import settings


@backoff.on_exception(
    backoff.expo, (openai.RateLimitError, openai.APITimeoutError), max_tries=3
)
async def execute(langchain_repository: LangchainKnowledgeBaseRepository, chat: Chat) -> Tuple[Optional[ChatCompletion], int, dict[str, Union[str, List[dict[str, str]]]], List[dict[str, Union[str, int]]]]:
    client = AsyncOpenAI(
        api_key=settings.OPEN_AI_API_KEY,
        timeout=TIMEOUT,
    )
    last_message = chat.messages.pop()
    num_docs: int = chat.config.rag_config.num_documents
    system_prompt_formatted: dict[str, Union[str, List[dict[str, str]]]] = {
        "role": "system",
        "content": []
    }
    if num_docs > 0:
        docs: List[Document] = await langchain_repository.query(last_message['content'], num_docs)
        context = "\n".join([doc.page_content for doc in docs])
        system_prompt = f"""You are an assistant for question-answering tasks.Use the following pieces of retrieved context to answer the question. If you don't know the answer, say that you don't know. Use three sentences maximum and keep the answer concise, Always say "thanks for asking!" at the end of the answer.
            

        {context}"""

        system_prompt_content = {"type": "text", "text": system_prompt}
        system_prompt_formatted["content"].append(system_prompt_content)
        chat.messages.append(system_prompt_formatted)
        chat.messages.append(last_message)

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
    
    system_prompt_message: dict[str, Union[str, List[dict[str, str]]]] = {
        "role": "system",
        "content": []
    }

    for content in system_prompt_formatted["content"]:
        # include image url in parsing when necessary
        system_prompt_message["content"].append({"contentType": "text", "value": content["text"]})

    return chat_completion, num_docs, system_prompt_message
