from dataclasses import dataclass


@dataclass
class WebSearchResult:
    result: str
    error: str
