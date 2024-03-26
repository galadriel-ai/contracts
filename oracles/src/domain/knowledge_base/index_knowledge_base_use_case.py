from typing import List
from typing import Optional
from src.entities import KnowledgeBaseIndexingRequest
from src.domain.knowledge_base.entities import KnowledgeBaseIndexingResult
from src.repositories.ipfs_repository import IpfsRepository
from src.domain.knowledge_base.utils import deserialize_documents
from src.repositories.knowledge_base_repository import KnowledgeBaseRepository


async def execute(
    request: KnowledgeBaseIndexingRequest,
    ipfs_repository: IpfsRepository,
    kb_repository: KnowledgeBaseRepository,
) -> KnowledgeBaseIndexingResult:
    try:
        documents_str = await ipfs_repository.read_file(request.cid)
        await kb_repository.create(request.cid, deserialize_documents(documents_str))
        index = await kb_repository.serialize(request.cid)
        index_cid = await ipfs_repository.write_file(index)
        return index_cid
    except Exception as e:
        print(e)
        return KnowledgeBaseIndexingResult(
            index_cid="",
            error=str(e),
        )
