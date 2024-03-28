from dataclasses import dataclass


@dataclass
class KnowledgeBaseIndexingResponse:
    id: int
    is_processed: bool
    index_cid: str
    error: str
