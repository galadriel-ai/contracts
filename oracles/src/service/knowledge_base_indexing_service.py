import asyncio
from asyncio import Semaphore

from src.entities import KnowledgeBaseIndexingRequest
from src.domain.knowledge_base import index_knowledge_base_use_case
from src.repositories.ipfs_repository import IpfsRepository
from src.repositories.knowledge_base_repository import KnowledgeBaseRepository
from src.repositories.web3.knowledge_base_repository import Web3KnowledgeBaseRepository

KB_INDEXING_TASKS = {}
MAX_CONCURRENT_INDEXING = 5


async def execute(
    repository: Web3KnowledgeBaseRepository,
    ipfs_repository: IpfsRepository,
    kb_repository: KnowledgeBaseRepository,
):
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
                            repository,
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


async def _index_knowledgebase_function(
    request: KnowledgeBaseIndexingRequest,
    repository: Web3KnowledgeBaseRepository,
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
