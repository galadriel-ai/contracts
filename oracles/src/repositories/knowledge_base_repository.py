import faiss
import backoff
import settings
import numpy as np
from io import BytesIO
from openai import AsyncOpenAI
from openai import RateLimitError
from typing import List, Any, Tuple, Dict
from src.domain.knowledge_base.entities import Document

BATCH_SIZE = 2048


class KnowledgeBaseRepository:
    def __init__(self):
        self.openai_client = AsyncOpenAI(
            api_key=settings.OPEN_AI_API_KEY,
        )
        self.indexes = {}
        self.document_stores = {}

    async def create(self, name: str, documents: List[Document]):
        embeddings = []
        for i in range(0, len(documents), BATCH_SIZE):
            print(i)
            batch = [
                document.page_content for document in documents[i : i + BATCH_SIZE]
            ]
            batch_embeddings = await self._create_embedding(batch)
            embeddings.extend(batch_embeddings)
        dimension = len(embeddings[0])
        np_embeddings = np.array(embeddings).astype("float32")
        index = faiss.IndexFlatL2(dimension)
        index.add(np_embeddings)
        self.indexes[name] = index
        self.document_stores[name] = documents

    async def serialize(self, name: str) -> bytes:
        index = self.indexes[name]
        np_index = faiss.serialize_index(index)
        bytes_container = BytesIO()
        np.save(bytes_container, np_index)
        return bytes_container.getvalue()

    async def deserialize(self, name: str, documents: List[Document], data: bytes):
        bytes_container = BytesIO(data)
        np_index = np.load(bytes_container)
        index = faiss.deserialize_index(np_index)
        self.indexes[name] = index
        self.document_stores[name] = documents

    async def query(self, name: str, query: str, k: int = 1) -> List[str]:
        index = self.indexes[name]
        doc_store = self.document_stores[name]
        query_embedding = await self._create_embedding([query])
        query_vector = np.array([query_embedding[0]]).astype("float32")
        _, indexes = index.search(query_vector, k)
        results = [doc_store[indexes[0][i]] for i in range(len(indexes[0]))]
        return results

    async def exists(self, name: str) -> bool:
        try:
            self.indexes[name]
            self.document_stores[name]
            return True
        except KeyError:
            return False

    @backoff.on_exception(backoff.expo, RateLimitError, max_tries=3)
    async def _create_embedding(self, texts: List[str]) -> List[float]:
        response = await self.openai_client.embeddings.create(
            input=texts, model="text-embedding-3-small"
        )
        embeddings = [data.embedding for data in response.data]
        return embeddings

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
