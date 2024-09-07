import asyncio
from asyncio import Semaphore

from src.entities import LangchainKnowledgeBaseIndexingRequest
from src.domain.langchain_knowledge_base import index_knowledge_base_use_case
from src.repositories.filesystem_repository import FileSystemRepository
from src.repositories.langchain_knowledge_base_repository import LangchainKnowledgeBaseRepository
from src.repositories.web3.langchain_knowledge_base_repository import Web3LangchainKnowledgeBaseRepository

LANGCHAIN_KB_INDEXING_TASKS = {}
MAX_CONCURRENT_INDEXING = 5


async def execute(
    repository: Web3LangchainKnowledgeBaseRepository,
    filesystem_repository: FileSystemRepository,
    langchain_kb_repository: LangchainKnowledgeBaseRepository,
):
    semaphore = asyncio.Semaphore(MAX_CONCURRENT_INDEXING)
    while True:
        try:
            langchain_kb_indexing_requests = await repository.get_unindexed_knowledge_bases()
            for kb_indexing_request in langchain_kb_indexing_requests:
                if kb_indexing_request.id not in LANGCHAIN_KB_INDEXING_TASKS:
                    print(
                        f"Indexing Langchain knowledge base {kb_indexing_request.id}, key {kb_indexing_request.key}"
                    )
                    task = asyncio.create_task(
                        _index_knowledgebase_function(
                            kb_indexing_request,
                            repository,
                            filesystem_repository,
                            langchain_kb_repository,
                            semaphore,
                        )
                    )
                    LANGCHAIN_KB_INDEXING_TASKS[kb_indexing_request.id] = task
            completed_tasks = [
                index for index, task in LANGCHAIN_KB_INDEXING_TASKS.items() if task.done()
            ]
            for index in completed_tasks:
                try:
                    await LANGCHAIN_KB_INDEXING_TASKS[index]
                except Exception as e:
                    print(
                        f"Task for langchain kb indexing request {index} raised an exception: {e}"
                    )
                del LANGCHAIN_KB_INDEXING_TASKS[index]
        except Exception as exc:
            print(f"Langchain Kb indexing loop raised an exception: {exc}")
        await asyncio.sleep(1)


async def _index_knowledgebase_function(
    request: LangchainKnowledgeBaseIndexingRequest,
    repository: Web3LangchainKnowledgeBaseRepository,
    filesystem_repository: FileSystemRepository,
    kb_repository: LangchainKnowledgeBaseRepository,
    semaphore: Semaphore,
):
    try:
        async with semaphore:
            indexing_result = await index_knowledge_base_use_case.execute(
                request, filesystem_repository, kb_repository
            )
            success = await repository.send_kb_indexing_response(
                request,
                error_message=indexing_result.error,
            )
            print(
                f"Langchain Knowledge base indexing {request.id} {'' if success else 'not '} indexed, tx: {request.transaction_receipt}"
            )
    except Exception as ex:
        print(
            f"Failed to index Langchain knowledge base {request.id}, cid {request.cid}, exc: {ex}"
        )
