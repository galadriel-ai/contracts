import asyncio
from src.repositories.oracle_repository import OracleRepository
from src.domain.llm import generate_response_use_case
from src.entities import Chat

repository = OracleRepository()


async def _answer_chat(chat: Chat):
    try:
        response = await generate_response_use_case.execute("gpt-4-turbo-preview", chat)
        if response:
            chat.response = response
            await repository.send_response(chat, response)
    except Exception as ex:
        print(f"Failed to answer chat {chat.id}, exc: {ex}")


async def _answer_unanswered_chats():
    chat_tasks = {}
    while True:
        try:
            chats = await repository.get_unanswered_chats()
            for chat in chats:
                print(f"Answering chat {chat.id}")
                if chat.id not in chat_tasks:
                    task = asyncio.create_task(_answer_chat(chat))
                    chat_tasks[chat.id] = task
            completed_tasks = [
                index for index, task in chat_tasks.items() if task.done()
            ]
            for index in completed_tasks:
                try:
                    await chat_tasks[index]
                    print(f"Chat {index} answered successfully")
                except Exception as e:
                    print(f"Task for chat {index} raised an exception: {e}")
                del chat_tasks[index]
        except Exception as exc:
            print(f"Main loop raised an exception: {exc}")
        await asyncio.sleep(2)


async def main():
    await _answer_unanswered_chats()


if __name__ == "__main__":
    asyncio.run(main())
