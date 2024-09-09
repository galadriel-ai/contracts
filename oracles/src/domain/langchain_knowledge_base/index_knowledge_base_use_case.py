from src.entities import LangchainKnowledgeBaseIndexingRequest
from src.domain.langchain_knowledge_base.entities import LangchainKnowledgeBaseIndexingResult
from src.repositories.filesystem_repository import FileSystemRepository
from src.repositories.langchain_knowledge_base_repository import LangchainKnowledgeBaseRepository
import settings

async def execute(
    request: LangchainKnowledgeBaseIndexingRequest,
    file_repository: FileSystemRepository,
    kb_repository: LangchainKnowledgeBaseRepository,
) -> LangchainKnowledgeBaseIndexingRequest:
    try:
        content = await file_repository.read_file(
            request.key, settings.KNOWLEDGE_BASE_MAX_SIZE_BYTES
        )

        if content is None:
            raise FileNotFoundError(filename=request.key)
        
        await kb_repository.create(
            request.key, content, request.owner
        )
        index = await kb_repository.serialize()
        await file_repository.write_file(index, key="index")
        return LangchainKnowledgeBaseIndexingResult(
            error="",
        )
    except Exception as e:
        print(e, flush=True)
        return LangchainKnowledgeBaseIndexingResult(
            error=str(e),
        )
