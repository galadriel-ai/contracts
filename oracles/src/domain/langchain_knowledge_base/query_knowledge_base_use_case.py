import settings
from typing import List

from src.entities import LangchainKnowledgeBaseQuery
from langchain_core.documents import Document
from src.domain.langchain_knowledge_base.entities import LangchainKnowledgeBaseQueryResult
from src.repositories.filesystem_repository import FileSystemRepository
from src.repositories.langchain_knowledge_base_repository import LangchainKnowledgeBaseRepository


async def execute(
    request: LangchainKnowledgeBaseQuery,
    filesystem_repository: FileSystemRepository,
    kb_repository: LangchainKnowledgeBaseRepository,
) -> LangchainKnowledgeBaseQueryResult:
    try:
        documents: List[Document] = await kb_repository.query(query=request.query, k=request.num_documents)
        print(f"Found {len(documents)} documents", flush=True)
        for docs in documents:
            print(f'content: {docs.page_content}, metadata: {docs.metadata}', flush=True)
        document_map_list = [
            {
                "text": doc.page_content,
                "score": doc.metadata["score"],
                "owner": doc.metadata["owner"],
            }
            for doc in documents
        ]
        return LangchainKnowledgeBaseQueryResult(documents=document_map_list, error="")
    except Exception as e:
        print(e, flush=True)
        return LangchainKnowledgeBaseQueryResult(documents=[], error=str(e))


if __name__ == "__main__":
    import asyncio

    async def main():
        query = LangchainKnowledgeBaseQuery(
            id=1,
            callback_id=1,
            is_processed=False,
            query="What was the color of the car?",
            num_documents=1
        )
        filesystem_repository = FileSystemRepository()
        kb_repository = LangchainKnowledgeBaseRepository()
        print(await execute(query, filesystem_repository, kb_repository))
        for i in range(100):
            print(await execute(query, filesystem_repository, kb_repository))

    asyncio.run(main())
