from typing import Optional

from src.repositories.ipfs_repository import IpfsRepository
from src.domain.storage.entities import UploadToGCPRequest
from src.domain.storage import upload_to_gcp_use_case

KEY_PATH = "/app/sidekik.json"


async def execute(ipfs_url: str, repository: IpfsRepository) -> Optional[str]:
    try:
        cid = await _parse_cid(ipfs_url)
        ipfs_file = repository.read_file(cid)
        request = UploadToGCPRequest(
            destination=cid, data=ipfs_file.data, content_type=ipfs_file.content_type
        )
        upload_to_gcp_use_case.execute(request)
    except Exception as e:
        print(e)
        return None


async def _parse_cid(ipfs_url: str) -> str:
    return ipfs_url.split("/")[-1]


if __name__ == "__main__":
    import asyncio

    async def main():
        cid = await _parse_cid("ipfs://QmXZv1")
        print(cid)

    asyncio.run(main())
