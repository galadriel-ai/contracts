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
        if chat.response is None:
            response = await generate_response_use_case.execute(
                "gpt-4-turbo-preview", chat
            )
            chat.response = response.content
            chat.error_message = response.error

        success = await repository.send_chat_response(chat)
        print(
            f"Chat {chat.id} {'' if success else 'not '}replied, tx: {chat.transaction_receipt}"
        )
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
                except Exception as e:
                    print(f"Task for chat {index} raised an exception: {e}")
                del chat_tasks[index]
        except Exception as exc:
            print(f"Chat loop raised an exception: {exc}")
        await asyncio.sleep(1)


async def _call_function(function_call: FunctionCall):
    try:
        response = ""
        error_message = ""
        if function_call.response is None:
            if function_call.function_type == "image_generation":
                image = await generate_image_use_case.execute(
                    function_call.function_input
                )
                response = (
                    await reupload_to_gcp_use_case.execute(image.url)
                    if image.url != ""
                    else ""
                )
                error_message = image.error
            elif function_call.function_type == "web_search":
                web_search_result = await web_search_use_case.execute(
                    function_call.function_input
                )
                response = web_search_result.result
                error_message = web_search_result.error
            else:
                response = ""
                error_message = f"Unknown function '{function_call.function_type}'"
            function_call.response = response
            function_call.error_message = error_message

        if not function_call.is_processed:
            success = await repository.send_function_call_response(
                function_call, function_call.response
            )
            print(
                f"Function {function_call.id} {'' if success else 'not '}called, tx: {function_call.transaction_receipt}"
            )
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
                except Exception as e:
                    print(f"Task for function {index} raised an exception: {e}")
                del function_tasks[index]
        except Exception as exc:
            print(f"Function loop raised an exception: {exc}")
        await asyncio.sleep(1)


async def main():
    await asyncio.gather(
        _answer_unanswered_chats(),
        _process_function_calls(),
    )


if __name__ == "__main__":
    asyncio.run(main())
