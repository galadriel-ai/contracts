import settings
from typing import Optional
from google.cloud import storage
from google.oauth2 import service_account
from src.domain.storage.entities import UploadToGCPRequest

KEY_PATH = "/app/sidekik.json"


async def execute(request: UploadToGCPRequest) -> Optional[str]:
    storage_client = _get_storage_client()
    bucket = storage_client.bucket(settings.GCS_BUCKET_NAME)
    blob = bucket.blob(request.destination)

    if request.check_existence and blob.exists():
        return f"https://storage.googleapis.com/{settings.GCS_BUCKET_NAME}/{request.destination}"

    blob.upload_from_string(request.data, content_type=request.content_type)
    return f"https://storage.googleapis.com/{settings.GCS_BUCKET_NAME}/{request.destination}"


def _get_storage_client() -> storage.Client:
    credentials = service_account.Credentials.from_service_account_file(KEY_PATH)
    return storage.Client(
        project="sidekik-ai",
        credentials=credentials,
    )
