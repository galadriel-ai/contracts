from typing import List
from typing import Optional
from dataclasses import field
from dataclasses import dataclass


@dataclass
class Chat:
    id: int
    callback_id: int
    is_processed: bool
    messages: List[dict]
    response: Optional[str] = None
    error_message: Optional[str] = None
    transaction_receipt: dict = None


@dataclass
class FunctionCall:
    id: int
    callback_id: int
    is_processed: bool
    function_type: str
    function_input: str
    response: Optional[str] = None
    error_message: Optional[str] = None
    transaction_receipt: dict = None


@dataclass
class KnowledgeBaseIndexingRequest:
    id: int
    cid: str
    is_processed: bool
    index_cid: Optional[str] = None
    transaction_receipt: dict = None


@dataclass
class KnowledgeBaseQuery:
    id: int
    callback_id: int
    is_processed: bool
    index_cid: str
    query: str
    documents: List[str] = field(default_factory=list)
    error_message: Optional[str] = None
    transaction_receipt: dict = None
