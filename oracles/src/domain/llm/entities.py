from dataclasses import dataclass
from typing import Optional
from typing import Union

from openai.types.chat import ChatCompletion


@dataclass
class LLMResult:
    chat_completion: Optional[Union[str, ChatCompletion]]
    error: str
