import json
import settings
import chromadb
from chromadb.utils import embedding_functions
from typing import List, Any, Tuple, Dict
from src.domain.knowledge_base.entities import Document


class KnowledgeBaseRepository:
    def __init__(self):
        self.settings = settings
        self.chroma_client = chromadb.Client()

    async def create(self, name: str, documents: List[Document]):
        collection: chromadb.Collection = self.chroma_client.create_collection(
            name=name,
            embedding_function=embedding_functions.OpenAIEmbeddingFunction(
                api_key=settings.OPEN_AI_API_KEY, model_name="text-embedding-3-small"
            ),
        )
        ids, metadatas, documents = self._format_collection(documents)
        collection.add(
            ids=ids,
            metadatas=metadatas,
            documents=documents,
        )

    async def serialize(self, name: str) -> Any:
        collection = self.chroma_client.get_collection(name=name)
        result = collection.get(include=["embeddings", "documents", "metadatas"])
        return json.dumps(result)

    async def deserialize(self, name: str, data: Any):
        data = json.loads(data)
        try:
            self.chroma_client.delete_collection(name=name)
        except:
            pass
        chroma_collection: chromadb.Collection = self.chroma_client.create_collection(
            name=name,
            embedding_function=embedding_functions.OpenAIEmbeddingFunction(
                api_key=settings.OPEN_AI_API_KEY, model_name="text-embedding-3-small"
            ),
        )
        chroma_collection.add(
            ids=data["ids"],
            metadatas=data["metadatas"],
            documents=data["documents"],
            embeddings=data["embeddings"],
        )

    async def query(self, name: str, query: str) -> List[str]:
        collection = self.chroma_client.get_collection(
            name=name,
            embedding_function=embedding_functions.OpenAIEmbeddingFunction(
                api_key=settings.OPEN_AI_API_KEY, model_name="text-embedding-3-small"
            )
        )
        response = collection.query(
            n_results=3,
            query_texts=[query],
        )
        return response.get("documents")[0] or []

    async def exists(self, name: str) -> bool:
        try:
            self.chroma_client.get_collection(name=name)
            return True
        except ValueError:
            return False

    def _format_collection(
        self, collection_input: List[Document]
    ) -> Tuple[List[str], List[Dict], List[str]]:
        ids: List[str] = []
        metadatas: List[Dict] = []
        documents: List[str] = []
        for i, document in enumerate(collection_input):
            ids.append(str(i))
            metadatas.append(document.metadata)
            documents.append(document.page_content)
        return ids, metadatas, documents
