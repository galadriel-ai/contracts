from dataclasses import dataclass
from typing import Optional, List
from typing import Union

from openai.types.chat import ChatCompletion
from groq.types.chat import ChatCompletion as GroqChatCompletion


@dataclass
class LLMResult:
    chat_completion: Optional[Union[str, ChatCompletion, GroqChatCompletion]]
    system_prompt: dict[str, Union[str, List[dict[str, str]]]]
    num_documents: int
    error: str
