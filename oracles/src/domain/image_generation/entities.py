from dataclasses import dataclass


@dataclass
class ImageGenerationResult:
    prompt: str
    url: str
