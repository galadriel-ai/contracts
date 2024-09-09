from typing import Optional
from langchain.indexes import index
from langchain_core.documents import Document
from langchain.indexes import SQLRecordManager
from src.domain.vector_store.custom_faiss import CustomFAISS
from langchain_community.embeddings import HuggingFaceBgeEmbeddings
from langchain_community.docstore import InMemoryDocstore
from langchain_experimental.text_splitter import SemanticChunker
from langchain_groq import ChatGroq
from langchain.retrievers import ContextualCompressionRetriever
from langchain.retrievers.multi_query import MultiQueryRetriever
from langchain.retrievers.document_compressors import LLMChainExtractor, EmbeddingsFilter
from langchain.retrievers.document_compressors import DocumentCompressorPipeline
from langchain_community.document_transformers import EmbeddingsRedundantFilter


from typing import List
import faiss

class LangchainKnowledgeBaseRepository:
    def __init__(self, index_data: Optional[bytes]):
        # Embeddings
        embeddings_model_name = "BAAI/bge-small-en"
        embeddings_model_kwargs = {"device": "cpu"}
        embeddings_encode_kwargs = {"normalize_embeddings": True}
        self.embeddings = HuggingFaceBgeEmbeddings(
            model_name=embeddings_model_name, 
            model_kwargs=embeddings_model_kwargs, 
            encode_kwargs=embeddings_encode_kwargs
        )

        # Vector Store
        index = faiss.IndexFlatL2(len(self.embeddings.embed_query("hello world")))
        self.vector_store = CustomFAISS(
            embedding_function=self.embeddings,
            index=index,
            docstore=InMemoryDocstore(),
            index_to_docstore_id={},
        )
        if index_data:
            print("Index exists: deserializing vector store from existing index")
            self.vector_store = self.vector_store.deserialize_from_bytes(index_data, self.embeddings, allow_dangerous_deserialization=True)

        # Record Manager
        collection_name = "knowledge_base"
        namespace = f"faiss/{collection_name}"
        self.record_manager = SQLRecordManager(
            namespace, db_url="sqlite:///record_manager_cache.sql"
        )
        self.record_manager.create_schema()

        # Text Splitter
        self.text_splitter = SemanticChunker(self.embeddings)

        self.llm = ChatGroq(temperature=0)
        
        # Compressor Pipeline
        compressor = LLMChainExtractor.from_llm(self.llm)
        redundant_filter = EmbeddingsRedundantFilter(embeddings=self.embeddings)
        relevant_filter = EmbeddingsFilter(embeddings=self.embeddings, similarity_threshold=0.75)
        self.compressor_pipeline = DocumentCompressorPipeline(
            transformers=[redundant_filter, relevant_filter, compressor], 
        )
        


    async def create(self, name: str, content: str, owner: str):
        print("creating document", name, content, owner)
        docs = self.text_splitter.create_documents([content], metadatas=[{"source": name, "owner": owner}])
        print("length of docs created by text splitter",len(docs))
        index(
            docs_source=docs,
            vector_store=self.vector_store, 
            record_manager=self.record_manager, 
            cleanup='incremental', 
            source_id_key='source'
        )


    async def serialize(self) -> bytes:
        return self.vector_store.serialize_to_bytes()

    async def deserialize(self, data: bytes, embeddings: HuggingFaceBgeEmbeddings):
        self.vector_store.deserialize_from_bytes(data, embeddings)

    async def query(self, query: str, k: int = 1) -> List[Document]:
        retriever = MultiQueryRetriever.from_llm(retriever=self.vector_store.as_retriever(search_kwargs={"k": k}), llm=self.llm)
        compression_retriever = ContextualCompressionRetriever(
            base_compressor=self.compressor_pipeline, base_retriever=retriever
        )
        return compression_retriever.invoke(query)