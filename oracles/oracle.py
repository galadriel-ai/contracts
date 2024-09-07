import asyncio
import json
from typing import Optional

import settings

from src.repositories.filesystem_repository import FileSystemRepository
from src.repositories.ipfs_repository import IpfsRepository
from src.repositories.web3.chat_repository import Web3ChatRepository
from src.repositories.web3.function_repository import Web3FunctionRepository
from src.repositories.web3.langchain_knowledge_base_repository import Web3LangchainKnowledgeBaseRepository
from src.repositories.langchain_knowledge_base_repository import LangchainKnowledgeBaseRepository
from src.service import chat_service
from src.service import functions_service
from src.service import langchain_knowledge_base_indexing_service
from src.service import langchain_knowledge_base_query_service

web3_chat_repository = Web3ChatRepository()
web3_function_repository = Web3FunctionRepository()
web3_langchain_kb_repository = Web3LangchainKnowledgeBaseRepository()

repositories = [web3_chat_repository, web3_function_repository, web3_langchain_kb_repository]

async def collect_and_save_metrics():
    while True:
        metrics = {
            "transactions_sent": 0,
            "errors": 0,
        }

        for repo in repositories:
            repo_metrics = repo.get_metrics().copy()
            metrics["transactions_sent"] += repo_metrics.pop(
                "transactions_sent", 0
            )
            metrics["errors"] += repo_metrics.pop("errors", 0)
            metrics.update(repo_metrics)

        with open("metrics.json", "w") as f:
            json.dump(metrics, f)

        print("Metrics saved to file.")
        await asyncio.sleep(10)

async def main():
    filesystem_repository = FileSystemRepository()
    ipfs_repository = IpfsRepository()

    # Load index from file 'index' if it exists
    index_data: Optional[bytes] = await filesystem_repository.read_binary_file("index", settings.KNOWLEDGE_BASE_MAX_SIZE_BYTES)
    if index_data is not None:
        print("index file exists!")
    else:
        print("Warning! index does not exists creating new index")
    langchain_kb_repository = LangchainKnowledgeBaseRepository(index_data=index_data)

    tasks = [
        chat_service.execute(web3_chat_repository, ipfs_repository, langchain_kb_repository),
        functions_service.execute(web3_function_repository),
        langchain_knowledge_base_indexing_service.execute(
            web3_langchain_kb_repository, filesystem_repository, langchain_kb_repository
        ),
        langchain_knowledge_base_query_service.execute(
            web3_langchain_kb_repository, filesystem_repository, langchain_kb_repository
        ),
        collect_and_save_metrics(),
    ]

    print("Oracle started!")
    await asyncio.gather(*tasks)


if __name__ == "__main__":
    asyncio.run(main())
