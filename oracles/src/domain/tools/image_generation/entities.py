from dataclasses import dataclass


@dataclass
class ImageGenerationResult:
    url: str
    error: str
