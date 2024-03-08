import asyncio
from src.repositories.oracle_repository import OracleRepository
from src.domain.llm import generate_response_use_case

repository = OracleRepository()


async def _answer_unanswered_chats():
    chats = await repository.get_unanswered_chats()
    for chat in chats:
        try:
            response = await generate_response_use_case.execute("gpt-4-turbo-preview", chat)
            print(response)
            if response:
                chat.response = response
                await repository.send_response(chat, response)
        except Exception as ex:
            print(f"Failed to answer prompt {chat.id}, exc: {ex}")


async def _listen():
    while True:
        try:
            await _answer_unanswered_chats()
        except Exception as exc:
            print("Failed to index chain, exc:", exc)
        await asyncio.sleep(2)
        print("Looping")


async def main():
    await _listen()


if __name__ == "__main__":
    asyncio.run(main())
