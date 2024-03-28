from typing import Dict
from typing import List
from dataclasses import dataclass


@dataclass
class Document:
    page_content: str
    metadata: Dict


@dataclass
class KnowledgeBaseIndexingResult:
    index_cid: str
    error: str


@dataclass
class KnowledgeBaseQueryResult:
    documents: List[str]
    error: str
