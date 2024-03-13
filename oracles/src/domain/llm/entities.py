from dataclasses import dataclass


@dataclass
class LLMResult:
    content: str
    error: str
