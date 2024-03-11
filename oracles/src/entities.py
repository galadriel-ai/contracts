from typing import Optional
from dataclasses import dataclass


@dataclass
class Chat:
    id: int
    callback_id: int
    is_processed: bool
    messages: dict
    response: Optional[str] = None


@dataclass
class FunctionCall:
    id: int
    callback_id: int
    is_processed: bool
    function_type: str
    function_input: str
    response: Optional[str] = None
