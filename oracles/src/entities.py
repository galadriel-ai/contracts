from enum import Enum
from typing import Dict
from typing import List
from typing import Literal
from typing import Optional
from dataclasses import dataclass
from typing import Union
from openai.types.chat import ChatCompletion
from openai.types.chat import ChatCompletionToolParam

ALLOWED_FUNCTION_NAMES = ["image_generation", "web_search"]

OpenAiModelType = Literal["gpt-4-turbo-preview", "gpt-3.5-turbo-1106"]


class PromptType(str, Enum):
    DEFAULT = "default"
    OPENAI = "OpenAI"


PromptTypeLiteral = Literal[PromptType.DEFAULT, PromptType.OPENAI]

OpenaiToolChoiceType = Optional[Literal["none", "auto"]]


@dataclass
class OpenAiConfig:
    model: OpenAiModelType
    frequency_penalty: Optional[float]
    logit_bias: Optional[Dict]
    max_tokens: Optional[str]
    presence_penalty: Optional[float]
    response_format: Optional[Union[str, Dict]]
    seed: Optional[int]
    stop: Optional[str]
    temperature: Optional[float]
    tools: Optional[List[ChatCompletionToolParam]]
    tool_choice: OpenaiToolChoiceType
    user: Optional[str]


@dataclass
class Chat:
    id: int
    callback_id: int
    is_processed: bool
    prompt_type: PromptTypeLiteral
    config: Optional[Union[OpenAiConfig]]
    messages: List[dict]
    response: Optional[Union[str, ChatCompletion]] = None
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
