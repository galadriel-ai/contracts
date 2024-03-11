import asyncio
from src.repositories.oracle_repository import OracleRepository
from src.domain.llm import generate_response_use_case
from src.domain.search import web_search_use_case
from src.domain.image_generation import generate_image_use_case
from src.domain.storage import reupload_to_gcp_use_case
from src.entities import Chat
from src.entities import FunctionCall

repository = OracleRepository()


async def _answer_chat(chat: Chat):
    try:
        response = await generate_response_use_case.execute("gpt-4-turbo-preview", chat)
        if response:
            chat.response = response
            await repository.send_chat_response(chat, response)
    except Exception as ex:
        print(f"Failed to answer chat {chat.id}, exc: {ex}")


async def _answer_unanswered_chats():
    chat_tasks = {}
    while True:
        try:
            chats = await repository.get_unanswered_chats()
            for chat in chats:
                if chat.id not in chat_tasks:
                    print(f"Answering chat {chat.id}")
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
            print(f"Chat loop raised an exception: {exc}")
        await asyncio.sleep(2)


async def _call_function(function_call: FunctionCall):
    try:
        response = None
        if function_call.function_type == "image_generation":
            response = await generate_image_use_case.execute(
                function_call.function_input
            )
            response = response.url if response else None
            if response:
                response = await reupload_to_gcp_use_case.execute(response)
        elif function_call.function_type == "web_search":
            response = await web_search_use_case.execute(function_call.function_input)
        if response:
            await repository.send_function_call_response(function_call, response)
        else:
            function_call.response = "Failed to execute function"
    except Exception as ex:
        print(f"Failed to call function {function_call.id}, exc: {ex}")


async def _process_function_calls():
    function_tasks = {}
    while True:
        try:
            function_calls = await repository.get_unanswered__function_calls()
            for function_call in function_calls:
                if function_call.id not in function_tasks:
                    print(f"Calling function {function_call.id}")
                    task = asyncio.create_task(_call_function(function_call))
                    function_tasks[function_call.id] = task
            completed_tasks = [
                index for index, task in function_tasks.items() if task.done()
            ]
            for index in completed_tasks:
                try:
                    await function_tasks[index]
                    print(f"Function {index} called successfully")
                except Exception as e:
                    print(f"Task for function {index} raised an exception: {e}")
                del function_tasks[index]
        except Exception as exc:
            print(f"Function loop raised an exception: {exc}")
        await asyncio.sleep(2)


async def main():
    await asyncio.gather(
        _answer_unanswered_chats(),
        _process_function_calls(),
    )


if __name__ == "__main__":
    asyncio.run(main())
