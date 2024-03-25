import json
from typing import List
from typing import Optional
from src.entities import KnowledgeBaseIndexingRequest
from src.domain.knowledge_base.entities import Document
from src.repositories.ipfs_repository import IpfsRepository
from src.repositories.knowledge_base_repository import KnowledgeBaseRepository


async def execute(
    request: KnowledgeBaseIndexingRequest,
    ipfs_repository: IpfsRepository,
    kb_repository: KnowledgeBaseRepository,
) -> Optional[str]:
    documents_str = await ipfs_repository.read_file(request.cid)
    await kb_repository.create(request.cid, _get_documents(documents_str))
    index = await kb_repository.serialize(request.cid)
    index_cid = await ipfs_repository.write_file(index)
    return index_cid


def _get_documents(documents_str: str) -> List[Document]:
    documents = json.loads(documents_str)
    return [
        Document(page_content=doc["page_content"], metadata=doc["metadata"])
        for doc in documents
    ]
