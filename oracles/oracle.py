import asyncio
from asyncio import Semaphore

import settings
from src.domain.llm import generate_response_use_case
from src.domain.storage import reupload_to_gcp_use_case
from src.domain.tools import utils
from src.domain.tools.image_generation import generate_image_use_case
from src.domain.tools.search import web_search_use_case
from src.domain.knowledge_base import index_knowledge_base_use_case
from src.domain.knowledge_base import query_knowledge_base_use_case
from src.domain.tools.code_interpreter import python_interpreter_use_case
from src.entities import Chat
from src.entities import FunctionCall
from src.entities import KnowledgeBaseIndexingRequest
from src.entities import KnowledgeBaseQuery
from src.repositories.ipfs_repository import IpfsRepository
from src.repositories.oracle_repository import OracleRepository
from src.repositories.knowledge_base_repository import KnowledgeBaseRepository

repository = OracleRepository()
ipfs_repository = IpfsRepository()
kb_repository = KnowledgeBaseRepository(max_size=settings.KNOWLEDGE_BASE_CACHE_MAX_SIZE)


CHAT_TASKS = {}
FUNCTION_TASKS = {}
KB_INDEXING_TASKS = {}
KB_QUERY_TASKS = {}
MAX_CONCURRENT_CHATS = 5
MAX_CONCURRENT_FUNCTION_CALLS = 5
MAX_CONCURRENT_INDEXING = 5
MAX_CONCURRENT_KB_QUERIES = 5


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
                flush=True,
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
                    image = await generate_image_use_case.execute(formatted_input)
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


async def _process_function_calls():
    semaphore = asyncio.Semaphore(MAX_CONCURRENT_CHATS)
    while True:
        try:
            function_calls = await repository.get_unanswered_function_calls()
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
                    print(
                        f"Task for function {index} raised an exception: {e}",
                        flush=True,
                    )
                del FUNCTION_TASKS[index]
        except Exception as exc:
            print(f"Function loop raised an exception: {exc}", flush=True)
        await asyncio.sleep(1)


async def _index_knowledgebase_function(
    request: KnowledgeBaseIndexingRequest,
    ipfs_repository: IpfsRepository,
    kb_repository: KnowledgeBaseRepository,
    semaphore: Semaphore,
):
    try:
        async with semaphore:
            indexing_result = await index_knowledge_base_use_case.execute(
                request, ipfs_repository, kb_repository
            )
            success = await repository.send_kb_indexing_response(
                request,
                index_cid=indexing_result.index_cid,
                error_message=indexing_result.error,
            )
            print(
                f"Knowledge base indexing {request.id} {'' if success else 'not '} indexed, tx: {request.transaction_receipt}"
            )
    except Exception as ex:
        print(
            f"Failed to index knowledge base {request.id}, cid {request.cid}, exc: {ex}"
        )


async def _process_knowledge_base_indexing():
    semaphore = asyncio.Semaphore(MAX_CONCURRENT_INDEXING)
    while True:
        try:
            kb_indexing_requests = await repository.get_unindexed_knowledge_bases()
            for kb_indexing_request in kb_indexing_requests:
                if kb_indexing_request.id not in KB_INDEXING_TASKS:
                    print(
                        f"Indexing knowledge base {kb_indexing_request.id}, cid {kb_indexing_request.cid}"
                    )
                    task = asyncio.create_task(
                        _index_knowledgebase_function(
                            kb_indexing_request,
                            ipfs_repository,
                            kb_repository,
                            semaphore,
                        )
                    )
                    KB_INDEXING_TASKS[kb_indexing_request.id] = task
            completed_tasks = [
                index for index, task in KB_INDEXING_TASKS.items() if task.done()
            ]
            for index in completed_tasks:
                try:
                    await KB_INDEXING_TASKS[index]
                except Exception as e:
                    print(
                        f"Task for kb indexing request {index} raised an exception: {e}"
                    )
                del KB_INDEXING_TASKS[index]
        except Exception as exc:
            print(f"Kb indexing loop raised an exception: {exc}")
        await asyncio.sleep(1)


async def _query_knowledge_base(
    request: KnowledgeBaseQuery,
    ipfs_repository: IpfsRepository,
    kb_repository: KnowledgeBaseRepository,
    semaphore: Semaphore,
):
    try:
        async with semaphore:
            query_result = await query_knowledge_base_use_case.execute(
                request, ipfs_repository, kb_repository
            )
            success = await repository.send_kb_query_response(
                request, query_result.documents, error_message=query_result.error
            )
            print(
                f"Knowledge base query {request.id} {'' if success else 'not '} answered, tx: {request.transaction_receipt}"
            )
    except Exception as ex:
        print(
            f"Failed to query knowledge base {request.id}, cid {request.index_cid}, exc: {ex}"
        )


async def _process_knowledge_base_queries():
    ipfs_repository = IpfsRepository()
    semaphore = asyncio.Semaphore(MAX_CONCURRENT_KB_QUERIES)
    while True:
        try:
            kb_queries = await repository.get_unanswered_kb_queries()
            for kb_query in kb_queries:
                if kb_query.id not in KB_QUERY_TASKS:
                    print(
                        f"Querying knowledge base {kb_query.id}, cid {kb_query.cid}, index_cid {kb_query.index_cid}"
                    )
                    task = asyncio.create_task(
                        _query_knowledge_base(
                            kb_query, ipfs_repository, kb_repository, semaphore
                        )
                    )
                    KB_QUERY_TASKS[kb_query.id] = task
            completed_tasks = [
                query for query, task in KB_QUERY_TASKS.items() if task.done()
            ]
            for index in completed_tasks:
                try:
                    await KB_QUERY_TASKS[index]
                except Exception as e:
                    print(f"Task for kb query {index} raised an exception: {e}")
                del KB_QUERY_TASKS[index]
        except Exception as exc:
            print(f"Kb query loop raised an exception: {exc}")
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
        print(
            f"Required module not found: {e}. FastAPI server will not start.",
            flush=True,
        )


async def main():
    tasks = [
        _answer_unanswered_chats(),
        _process_function_calls(),
        _process_knowledge_base_indexing(),
        _process_knowledge_base_queries(),
    ]

    if settings.SERVE_METRICS:
        print("Serving metrics", flush=True)
        tasks.append(_serve_metrics())

    print("Oracle started!")
    await asyncio.gather(*tasks)


if __name__ == "__main__":
    asyncio.run(main())
