import asyncio
from asyncio import Semaphore

from src.entities import LangchainKnowledgeBaseQuery
from src.domain.langchain_knowledge_base import query_knowledge_base_use_case
# from src.repositories.filesystem_repository import FileSystemRepository
from src.repositories.basin_repository import BasinRepository
from src.repositories.langchain_knowledge_base_repository import LangchainKnowledgeBaseRepository
from src.repositories.web3.langchain_knowledge_base_repository import Web3LangchainKnowledgeBaseRepository

LANGCHAIN_KB_QUERY_TASKS = {}
MAX_CONCURRENT_KB_QUERIES = 5


async def execute(
    repository: Web3LangchainKnowledgeBaseRepository,
    # filesystem_repository: FileSystemRepository,
    basin_repository: BasinRepository,
    kb_repository: LangchainKnowledgeBaseRepository,
):
    semaphore = asyncio.Semaphore(MAX_CONCURRENT_KB_QUERIES)
    while True:
        try:
            kb_queries = await repository.get_unanswered_kb_queries()
            for kb_query in kb_queries:
                if kb_query.id not in LANGCHAIN_KB_QUERY_TASKS:
                    print(
                        f"Querying langchain knowledge base {kb_query.id} for {kb_query.query} with {kb_query.num_documents} documents"
                    )
                    task = asyncio.create_task(
                        _query_knowledge_base(
                            kb_query,
                            repository,
                            # filesystem_repository,
                            basin_repository,
                            kb_repository,
                            semaphore,
                        )
                    )
                    LANGCHAIN_KB_QUERY_TASKS[kb_query.id] = task
            completed_tasks = [
                query for query, task in LANGCHAIN_KB_QUERY_TASKS.items() if task.done()
            ]
            for index in completed_tasks:
                try:
                    await LANGCHAIN_KB_QUERY_TASKS[index]
                except Exception as e:
                    print(f"Task for langchain kb query {index} raised an exception: {e}")
                del LANGCHAIN_KB_QUERY_TASKS[index]
        except Exception as exc:
            print(f"langchain Kb query loop raised an exception: {exc}")
        await asyncio.sleep(1)


async def _query_knowledge_base(
    request: LangchainKnowledgeBaseQuery,
    repository: Web3LangchainKnowledgeBaseRepository,
    # filesystem_repository: FileSystemRepository,
    basin_repository: BasinRepository,
    kb_repository: LangchainKnowledgeBaseRepository,
    semaphore: Semaphore,
):
    try:
        async with semaphore:
            # query_result = await query_knowledge_base_use_case.execute(
            #     request, filesystem_repository, kb_repository
            # )
            query_result = await query_knowledge_base_use_case.execute(
                request, basin_repository, kb_repository
            )
            success = await repository.send_kb_query_response(
                request, query_result.documents, error_message=query_result.error
            )
            print(
                f"Langchain Knowledge base query {request.id} {'' if success else 'not '} answered, tx: {request.transaction_receipt}"
            )
    except Exception as ex:
        print(
            f"Failed to query knowledge base {request.id}, exc: {ex}"
        )
