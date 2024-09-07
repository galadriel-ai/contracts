from typing import Any, Callable, Dict, List, Optional, Union
from langchain_core.documents import Document
from langchain_community.vectorstores import FAISS

# Custom FAISS to include score in the metadata of the documents
class CustomFAISS(FAISS):
    def max_marginal_relevance_search_by_vector(
        self,
        embedding: List[float],
        k: int = 4,
        fetch_k: int = 20,
        lambda_mult: float = 0.5,
        filter: Optional[Union[Callable, Dict[str, Any]]] = None,
        **kwargs: Any,
    ) -> List[Document]:
        
        docs_and_scores = self.max_marginal_relevance_search_with_score_by_vector(
            embedding, k=k, fetch_k=fetch_k, lambda_mult=lambda_mult, filter=filter, **kwargs
        )

        [doc_.metadata.update({'score': score}) for doc_, score in docs_and_scores]

        return [doc for doc, _ in docs_and_scores]
    
    def similarity_search(
        self,
        query: str,
        k: int = 4,
        filter: Optional[Union[Callable, Dict[str, Any]]] = None,
        fetch_k: int = 20,
        **kwargs: Any,
    ) -> List[Document]:
        
        docs_and_scores = self.similarity_search_with_score(
            query, k, filter=filter, fetch_k=fetch_k, **kwargs
        )

        [doc_.metadata.update({'score': score}) for doc_, score in docs_and_scores]
        
        return [doc for doc, _ in docs_and_scores]