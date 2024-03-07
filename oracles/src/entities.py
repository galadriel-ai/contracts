from typing import Optional
from dataclasses import dataclass


@dataclass
class PromptAndResponse:
    id: int
    prompt: str
    callback_id: int
    # Not actually needed here, contract handles it
    callback_address: str
    is_processed: bool
    response: Optional[str] = None
