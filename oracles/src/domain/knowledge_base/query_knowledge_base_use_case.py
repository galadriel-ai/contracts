from typing import List
from src.entities import KnowledgeBaseQuery
from src.domain.knowledge_base.entities import Document
from src.domain.knowledge_base.entities import KnowledgeBaseQueryResult
from src.repositories.ipfs_repository import IpfsRepository
from src.domain.knowledge_base.utils import deserialize_documents
from src.repositories.knowledge_base_repository import KnowledgeBaseRepository


async def execute(
    request: KnowledgeBaseQuery,
    ipfs_repository: IpfsRepository,
    kb_repository: KnowledgeBaseRepository,
) -> KnowledgeBaseQueryResult:
    try:
        if not await kb_repository.exists(request.cid):
            documents_str = await ipfs_repository.read_file(request.cid)
            documents = deserialize_documents(documents_str)
            index = await ipfs_repository.read_file(request.index_cid)
            await kb_repository.deserialize(
                request.cid, documents=documents, data=index
            )
        documents = await kb_repository.query(request.cid, request.query)
        return KnowledgeBaseQueryResult(documents=documents, error="")
    except Exception as e:
        print(e)
        return KnowledgeBaseQueryResult(documents=[], error=str(e))


if __name__ == "__main__":
    import asyncio

    async def main():
        query = KnowledgeBaseQuery(
            id=1,
            callback_id=1,
            is_processed=False,
            cid="bafkreic2ft2wzozti3kpyilyjk4f5peirzdia7phmvicva6bfdwtjkx5ny",
            index_cid="bafkreihgkrl7udanqbvkcig46xgp2dzj2mo5qidyvxmj7gga4vt5mdcu5m",
            query="What was the color of the car?",
        )
        ipfs_repository = IpfsRepository()
        kb_repository = KnowledgeBaseRepository()
        print(await execute(query, ipfs_repository, kb_repository))
        for i in range(100):
            print(await execute(query, ipfs_repository, kb_repository))

    asyncio.run(main())