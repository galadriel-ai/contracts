import json
from typing import List
from src.domain.knowledge_base.entities import Document


def deserialize_documents(documents: bytes) -> List[Document]:
    documents_str = documents.decode("utf-8")
    docs_dicts = json.loads(documents_str)
    return [
        Document(page_content=doc["page_content"], metadata=doc["metadata"])
        for doc in docs_dicts
    ]
