import asyncio
from asyncio import Semaphore

import settings
from src.domain.llm import generate_response_use_case
from src.domain.storage import reupload_to_gcp_use_case
from src.domain.tools import utils
from src.domain.tools.image_generation import generate_image_use_case
from src.domain.tools.search import web_search_use_case
from src.domain.tools.code_interpreter import python_interpreter_use_case
from src.entities import Chat
from src.entities import FunctionCall
from src.repositories.oracle_repository import OracleRepository

repository = OracleRepository()

CHAT_TASKS = {}
FUNCTION_TASKS = {}
MAX_CONCURRENT_CHATS = 5
MAX_CONCURRENT_FUNCTION_CALLS = 5


async def _answer_chat(chat: Chat, semaphore: Semaphore):
    try:
        async with semaphore:
            print(f"Answering chat {chat.id}", flush=True)
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
                flush=True
            )
    except Exception as ex:
        print(f"Failed to answer chat {chat.id}, exc: {ex}", flush=True)


async def _answer_unanswered_chats():
    semaphore = asyncio.Semaphore(MAX_CONCURRENT_CHATS)
    while True:
        try:
            chats = await repository.get_unanswered_chats()
            for chat in chats:
                if chat.id not in CHAT_TASKS:
                    task = asyncio.create_task(_answer_chat(chat, semaphore))
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


async def _call_function(function_call: FunctionCall, semaphore: Semaphore):
    try:
        async with semaphore:
            print(f"Calling function {function_call.id}", flush=True)
            response = ""
            error_message = ""
            if function_call.response is None:
                formatted_input = utils.format_tool_input(function_call.function_input)
                if function_call.function_type == "image_generation":
                    image = await generate_image_use_case.execute(
                        formatted_input
                    )
                    response = (
                        await reupload_to_gcp_use_case.execute(image.url)
                        if image.url != ""
                        else ""
                    )
                    error_message = image.error
                elif function_call.function_type == "web_search":
                    web_search_result = await web_search_use_case.execute(
                        formatted_input
                    )
                    response = web_search_result.result
                    error_message = web_search_result.error
                elif function_call.function_type == "code_interpreter":
                    python_interpreter_result = await python_interpreter_use_case.execute(
                        formatted_input
                    )
                    response = python_interpreter_result.stdout
                    error_message = python_interpreter_result.stderr
                else:
                    response = ""
                    error_message = f"Unknown function '{function_call.function_type}'"
                function_call.response = response
                function_call.error_message = error_message

            if not function_call.is_processed:
                success = await repository.send_function_call_response(
                    function_call, function_call.response, function_call.error_message
                )
                print(
                    f"Function {function_call.id} {'' if success else 'not '}"
                    f"called, tx: {function_call.transaction_receipt}",
                    flush=True
                )
    except Exception as ex:
        print(f"Failed to call function {function_call.id}, exc: {ex}", flush=True)


async def _process_function_calls():
    semaphore = asyncio.Semaphore(MAX_CONCURRENT_CHATS)
    while True:
        try:
            function_calls = await repository.get_unanswered__function_calls()
            for function_call in function_calls:
                if function_call.id not in FUNCTION_TASKS:
                    task = asyncio.create_task(_call_function(function_call, semaphore))
                    FUNCTION_TASKS[function_call.id] = task
            completed_tasks = [
                index for index, task in FUNCTION_TASKS.items() if task.done()
            ]
            for index in completed_tasks:
                try:
                    await FUNCTION_TASKS[index]
                except Exception as e:
                    print(f"Task for function {index} raised an exception: {e}", flush=True)
                del FUNCTION_TASKS[index]
        except Exception as exc:
            print(f"Function loop raised an exception: {exc}", flush=True)
        await asyncio.sleep(1)


async def _serve_metrics():
    try:
        from fastapi import FastAPI
        from starlette.responses import PlainTextResponse
        import uvicorn

        app = FastAPI()

        @app.get("/metrics", response_class=PlainTextResponse)
        async def metrics():
            return f'sei_oracle_chat_tasks{{chain="testnet"}} {len(CHAT_TASKS)}\nsei_oracle_function_tasks{{chain="testnet"}} {len(FUNCTION_TASKS)}\n'

        config = uvicorn.Config(app, host="0.0.0.0", port=8000)
        server = uvicorn.Server(config)
        await server.serve()
    except ImportError as e:
        print(f"Required module not found: {e}. FastAPI server will not start.", flush=True)


async def main():
    tasks = [
        _answer_unanswered_chats(),
        _process_function_calls(),
    ]

    if settings.SERVE_METRICS:
        print("Serving metrics", flush=True)
        tasks.append(_serve_metrics())

    print("Oracle started!")
    await asyncio.gather(*tasks)


if __name__ == "__main__":
    asyncio.run(main())
