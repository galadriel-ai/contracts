import asyncio
from asyncio import Semaphore

from src.entities import KnowledgeBaseQuery
from src.domain.knowledge_base import query_knowledge_base_use_case
from src.repositories.ipfs_repository import IpfsRepository
from src.repositories.knowledge_base_repository import KnowledgeBaseRepository
from src.repositories.web3.knowledge_base_repository import Web3KnowledgeBaseRepository

KB_QUERY_TASKS = {}
MAX_CONCURRENT_KB_QUERIES = 5


async def execute(
    repository: Web3KnowledgeBaseRepository,
    ipfs_repository: IpfsRepository,
    kb_repository: KnowledgeBaseRepository,
):
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
                            kb_query,
                            repository,
                            ipfs_repository,
                            kb_repository,
                            semaphore,
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


async def _query_knowledge_base(
    request: KnowledgeBaseQuery,
    repository: Web3KnowledgeBaseRepository,
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
