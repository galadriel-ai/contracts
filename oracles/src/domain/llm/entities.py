from dataclasses import dataclass
from typing import Optional
from typing import Union

from openai.types.chat import ChatCompletion
from groq.types.chat import ChatCompletion as GroqChatCompletion


@dataclass
class LLMResult:
    chat_completion: Optional[Union[str, ChatCompletion, GroqChatCompletion]]
    error: str
