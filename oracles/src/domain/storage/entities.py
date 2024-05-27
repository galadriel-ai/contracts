from dataclasses import dataclass


@dataclass
class UploadToGCPRequest:
    destination: str
    data: bytes | str
    content_type: str
