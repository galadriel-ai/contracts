from typing import Optional
from dataclasses import dataclass


@dataclass
class Chat:
    id: int
    callback_id: int
    is_processed: bool
    messages: dict
    response: Optional[str] = None
