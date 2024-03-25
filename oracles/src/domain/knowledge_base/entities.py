from typing import Dict
from dataclasses import dataclass


@dataclass
class Document:
    page_content: str
    metadata: Dict
