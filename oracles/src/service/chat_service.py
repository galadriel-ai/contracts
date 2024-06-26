import asyncio
from asyncio import Semaphore

from src.entities import Chat
from src.domain.llm import generate_response_use_case
from src.domain.storage import cache_ipfs_on_gcp_cache_use_case
from src.repositories.ipfs_repository import IpfsRepository
from src.repositories.web3.chat_repository import Web3ChatRepository

CHAT_TASKS = {}
MAX_CONCURRENT_CHATS = 5


async def execute(
    repository: Web3ChatRepository,
    ipfs_repository: IpfsRepository,
):
    semaphore = asyncio.Semaphore(MAX_CONCURRENT_CHATS)
    while True:
        try:
            chats = await repository.get_unanswered_chats()
            for chat in chats:
                if chat.id not in CHAT_TASKS:
                    task = asyncio.create_task(
                        _answer_chat(repository, ipfs_repository, chat, semaphore)
                    )
                    CHAT_TASKS[chat.id] = task
            completed_tasks = [
                index for index, task in CHAT_TASKS.items() if task.done()
            ]
            for index in completed_tasks:
                try:
                    await CHAT_TASKS[index]
                except Exception as e:
                    print(f"Task for chat {index} raised an exception: {e}", flush=True)
                del CHAT_TASKS[index]
        except Exception as exc:
            print(f"Chat loop raised an exception: {exc}", flush=True)
        await asyncio.sleep(1)


async def _answer_chat(
    repository: Web3ChatRepository,
    ipfs_repository: IpfsRepository,
    chat: Chat,
    semaphore: Semaphore,
):
    try:
        async with semaphore:
            print(f"Answering chat {chat.id}", flush=True)
            await _cache_ipfs_urls(chat, ipfs_repository)
            if chat.response is None:
                response = await generate_response_use_case.execute(
                    "gpt-4-turbo-preview", chat
                )
                chat.response = response.chat_completion
                chat.error_message = response.error

            success = await repository.send_chat_response(chat)
            print(
                f"Chat {chat.id} {'' if success else 'not '}"
                f"replied, tx: {chat.transaction_receipt}",
                flush=True,
            )
    except Exception as ex:
        print(f"Failed to answer chat {chat.id}, exc: {ex}", flush=True)


async def _cache_ipfs_urls(chat: Chat, ipfs_repository: IpfsRepository):
    for message in chat.messages:
        contents = message.get("content")
        if isinstance(contents, list):
            for content in contents:
                image_url = content.get("image_url", {}).get("url")
                if image_url and image_url.startswith("ipfs://"):
                    cached_url = await cache_ipfs_on_gcp_cache_use_case.execute(
                        image_url,
                        ipfs_repository,
                    )
                    content["image_url"]["url"] = cached_url
