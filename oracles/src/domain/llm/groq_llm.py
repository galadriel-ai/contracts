from typing import Optional,Tuple, Union

import backoff
import groq
from groq import AsyncGroq
from groq.types.chat import ChatCompletion as GroqChatCompletion
from openai.types.chat.chat_completion import ChatCompletion
from langchain_core.documents import Document
from typing import List

import settings
from src.domain.llm.utils import TIMEOUT
from src.entities import Chat
from src.repositories.langchain_knowledge_base_repository import LangchainKnowledgeBaseRepository


@backoff.on_exception(
    backoff.expo, (groq.RateLimitError, groq.APITimeoutError), max_tries=3
)
async def execute(langchain_repository: LangchainKnowledgeBaseRepository, chat: Chat) -> Tuple[Optional[GroqChatCompletion], int, dict[str, Union[str,List[dict[str, str]]]], List[dict[str, Union[str, int]]]]:
    try:
        client = AsyncGroq(
            api_key=settings.GROQ_API_KEY,
            timeout=TIMEOUT,
        )
        for message in chat.messages:
            if len(message.get("content")) and message.get("content"):
                content = message.get("content")
                if type(content) is not str:
                    message["content"] = message.get("content")[0].get("text")
        num_docs: int = chat.config.rag_config.num_documents
        system_prompt_formatted: dict[str, Union[str, List[dict[str, str]]]] = {
            "role": "system",
            "content": []
        }
        score_list = []
        if num_docs > 0:
            last_message = chat.messages.pop()
            docs: List[Document] = await langchain_repository.query(last_message['content'], num_docs)
            score_map = {}
            for doc in docs:
                if doc.metadata["owner"] not in score_map:
                    score_map[doc.metadata["owner"]] = doc.metadata["score"]
                else:
                    score_map[doc.metadata["owner"]] += doc.metadata["score"]
            score_list = [{'owner': owner, 'score': int(score * 100)} for owner, score in score_map.items()]
            context = "\n".join([doc.page_content for doc in docs])
            system_prompt = f"""You are an assistant for question-answering tasks.Use the following pieces of retrieved context to answer the question. If you don't know the answer, say that you don't know. Use three sentences maximum and keep the answer concise, Always say "thanks for asking!" at the end of the answer.
            

            {context}"""
            print("system_prompt", system_prompt)
            system_prompt_contend = {"type": "text", "text": system_prompt}
            system_prompt_formatted["content"].append(system_prompt_contend)

            system_prompt_llama = system_prompt_formatted.copy()
            system_prompt_llama["content"] = system_prompt_formatted["content"][0]["text"]
            chat.messages.append(system_prompt_llama)
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
            stop=chat.config.stop,
            temperature=chat.config.temperature,
            top_p=chat.config.top_p,
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

        return chat_completion, num_docs, system_prompt_message, score_list
    except Exception as e:
        print(f"Failed to execute chat completion, exc: {e}", flush=True)
        return "", 0, {}, []