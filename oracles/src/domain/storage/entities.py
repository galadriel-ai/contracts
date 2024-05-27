from typing import Optional
from dataclasses import dataclass


@dataclass
class UploadToGCPRequest:
    destination: str
    data: bytes | str
    content_type: str
    check_existence: bool = False


@dataclass
class IpfsFile:
    cid: str
    data: bytes
    content_type: Optional[str] = None
