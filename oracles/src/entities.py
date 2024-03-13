from typing import List
from typing import Optional
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
