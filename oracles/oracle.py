import asyncio
import settings
from src.domain.llm import generate_response_use_case
from src.domain.search import web_search_use_case
from src.domain.image_generation import generate_image_use_case
from src.domain.storage import reupload_to_gcp_use_case
from src.domain.knowledge_base import index_knowledge_base_use_case
from src.domain.knowledge_base import query_knowledge_base_use_case
from src.entities import Chat
from src.entities import FunctionCall
from src.entities import KnowledgeBaseIndexingRequest
from src.entities import KnowledgeBaseQuery
from src.repositories.ipfs_repository import IpfsRepository
from src.repositories.oracle_repository import OracleRepository
from src.repositories.knowledge_base_repository import KnowledgeBaseRepository

repository = OracleRepository()

CHAT_TASKS = {}
FUNCTION_TASKS = {}
KB_INDEXING_TASKS = {}
KB_QUERY_TASKS = {}


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
    while True:
        try:
            chats = await repository.get_unanswered_chats()
            for chat in chats:
                if chat.id not in CHAT_TASKS:
                    print(f"Answering chat {chat.id}")
                    task = asyncio.create_task(_answer_chat(chat))
                    CHAT_TASKS[chat.id] = task
            completed_tasks = [
                index for index, task in CHAT_TASKS.items() if task.done()
            ]
            for index in completed_tasks:
                try:
                    await CHAT_TASKS[index]
                except Exception as e:
                    print(f"Task for chat {index} raised an exception: {e}")
                del CHAT_TASKS[index]
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
                function_call, function_call.response, function_call.error_message
            )
            print(
                f"Function {function_call.id} {'' if success else 'not '}called, tx: {function_call.transaction_receipt}"
            )
    except Exception as ex:
        print(f"Failed to call function {function_call.id}, exc: {ex}")


async def _process_function_calls():
    while True:
        try:
            function_calls = await repository.get_unanswered_function_calls()
            for function_call in function_calls:
                if function_call.id not in FUNCTION_TASKS:
                    print(f"Calling function {function_call.id}")
                    task = asyncio.create_task(_call_function(function_call))
                    FUNCTION_TASKS[function_call.id] = task
            completed_tasks = [
                index for index, task in FUNCTION_TASKS.items() if task.done()
            ]
            for index in completed_tasks:
                try:
                    await FUNCTION_TASKS[index]
                except Exception as e:
                    print(f"Task for function {index} raised an exception: {e}")
                del FUNCTION_TASKS[index]
        except Exception as exc:
            print(f"Function loop raised an exception: {exc}")
        await asyncio.sleep(1)


async def _index_knowledgebase_function(
    request: KnowledgeBaseIndexingRequest,
    ipfs_repository: IpfsRepository,
    kb_repository: KnowledgeBaseRepository,
):
    try:
        error_message = ""
        index_cid = await index_knowledge_base_use_case.execute(
            request, ipfs_repository, kb_repository
        )
        success = await repository.send_kb_indexing_response(
            request, index_cid=index_cid, error_message=error_message
        )
        print(
            f"Knowledge base indexing {request.id} {'' if success else 'not '} indexed, tx: {request.transaction_receipt}"
        )
    except Exception as ex:
        print(
            f"Failed to index knowledge base {request.id}, cid {request.cid}, exc: {ex}"
        )


async def _process_knowledge_base_indexing():
    ipfs_repository = IpfsRepository()
    kb_repository = KnowledgeBaseRepository()

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
                            kb_indexing_request, ipfs_repository, kb_repository
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
    request: KnowledgeBaseQuery, ipfs_repository: IpfsRepository, kb_repository: KnowledgeBaseRepository
):
    try:
        error_message = ""
        documents = await query_knowledge_base_use_case.execute(
            request, ipfs_repository, kb_repository
        )
        print(documents)
        success = await repository.send_kb_query_response(
            request, documents, error_message=error_message
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
    kb_repository = KnowledgeBaseRepository()
    while True:
        try:
            kb_queries = await repository.get_unanswered_kb_queries()
            for kb_query in kb_queries:
                if kb_query.id not in KB_QUERY_TASKS:
                    print(f"Querying knowledge base {kb_query.id}, cid {kb_query.index_cid}")
                    task = asyncio.create_task(
                        _query_knowledge_base(kb_query, ipfs_repository, kb_repository)
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
        print(f"Required module not found: {e}. FastAPI server will not start.")


async def main():
    tasks = [
        _answer_unanswered_chats(),
        _process_function_calls(),
        _process_knowledge_base_indexing(),
        _process_knowledge_base_queries(),
    ]

    if settings.SERVE_METRICS:
        print("Serving metrics")
        tasks.append(_serve_metrics())

    await asyncio.gather(*tasks)


if __name__ == "__main__":
    asyncio.run(main())
