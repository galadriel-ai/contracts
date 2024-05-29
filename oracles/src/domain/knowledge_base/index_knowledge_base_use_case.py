import settings
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
        documents_file = await ipfs_repository.read_file(
            request.cid, settings.KNOWLEDGE_BASE_MAX_SIZE_BYTES
        )
        await kb_repository.create(
            request.cid, deserialize_documents(documents_file.data)
        )
        index = await kb_repository.serialize(request.cid)
        index_cid = await ipfs_repository.write_file(index)
        return KnowledgeBaseIndexingResult(
            index_cid=index_cid,
            error="",
        )
    except Exception as e:
        print(e, flush=True)
        return KnowledgeBaseIndexingResult(
            index_cid="",
            error=str(e),
        )
