from typing import List
from src.entities import KnowledgeBaseQuery
from src.domain.knowledge_base.entities import Document
from src.repositories.ipfs_repository import IpfsRepository
from src.repositories.knowledge_base_repository import KnowledgeBaseRepository


async def execute(
    request: KnowledgeBaseQuery,
    ipfs_repository: IpfsRepository,
    kb_repository: KnowledgeBaseRepository,
) -> List[Document]:
    try:
        index = await ipfs_repository.read_file(request.index_cid)
        await kb_repository.deserialize(request.index_cid, index)
        return await kb_repository.query(request.index_cid, request.query)
    except Exception as e:
        print(e)
        return []
