from dataclasses import dataclass
from typing import List

@dataclass
class LangchainKnowledgeBaseIndexingResult:
    error: str

@dataclass
class LangchainKnowledgeBaseQueryResult:
    documents: List[str]
    error: str
