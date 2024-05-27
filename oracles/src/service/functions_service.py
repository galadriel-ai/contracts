import asyncio
from asyncio import Semaphore

from src.entities import FunctionCall
from src.domain.storage import reupload_url_to_gcp_use_case
from src.domain.tools import utils
from src.domain.tools.image_generation import generate_image_use_case
from src.domain.tools.search import web_search_use_case
from src.domain.tools.code_interpreter import python_interpreter_use_case
from src.entities import FunctionCall
from src.repositories.web3.function_repository import Web3FunctionRepository

FUNCTION_TASKS = {}
MAX_CONCURRENT_FUNCTION_CALLS = 5


async def execute(repository: Web3FunctionRepository):
    semaphore = asyncio.Semaphore(MAX_CONCURRENT_FUNCTION_CALLS)
    while True:
        try:
            function_calls = await repository.get_unanswered_function_calls()
            for function_call in function_calls:
                if function_call.id not in FUNCTION_TASKS:
                    task = asyncio.create_task(
                        _call_function(repository, function_call, semaphore)
                    )
                    FUNCTION_TASKS[function_call.id] = task
            completed_tasks = [
                index for index, task in FUNCTION_TASKS.items() if task.done()
            ]
            for index in completed_tasks:
                try:
                    await FUNCTION_TASKS[index]
                except Exception as e:
                    print(
                        f"Task for function {index} raised an exception: {e}",
                        flush=True,
                    )
                del FUNCTION_TASKS[index]
        except Exception as exc:
            print(f"Function loop raised an exception: {exc}", flush=True)
        await asyncio.sleep(1)


async def _call_function(
    repository: Web3FunctionRepository,
    function_call: FunctionCall,
    semaphore: Semaphore,
):
    try:
        async with semaphore:
            print(f"Calling function {function_call.id}", flush=True)
            response = ""
            error_message = ""
            if function_call.response is None:
                formatted_input = utils.format_tool_input(function_call.function_input)
                if function_call.function_type == "image_generation":
                    image = await generate_image_use_case.execute(formatted_input)
                    response = (
                        await reupload_url_to_gcp_use_case.execute(image.url)
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
                    python_interpreter_result = (
                        await python_interpreter_use_case.execute(formatted_input)
                    )
                    response = python_interpreter_result.output
                    error_message = python_interpreter_result.error
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
                    flush=True,
                )
    except Exception as ex:
        print(f"Failed to call function {function_call.id}, exc: {ex}", flush=True)
