import json
import requests
import settings
from typing import List
from langchain.schema import Document


def execute(documents: List[Document]) -> str:
    serialized_data = _serialize_documents(documents)
    response = requests.post(
        "https://api.nft.storage/upload",
        headers={
            "Authorization": f"Bearer {settings.STORAGE_KEY}",
            "Content-Type": "text/plain",
        },
        data=serialized_data,
    )
    response.raise_for_status()
    return response.json().get("value").get("cid")


def _serialize_documents(documents: List[Document]) -> str:
    docs_dict = [
        {"page_content": doc.page_content, "metadata": doc.metadata}
        for doc in documents
    ]
    return json.dumps(docs_dict)
