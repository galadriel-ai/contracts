from typing import Optional

from src.repositories.ipfs_repository import IpfsRepository
from src.domain.storage.entities import UploadToGCPRequest
from src.domain.storage import upload_to_gcp_use_case


async def execute(ipfs_url: str, repository: IpfsRepository) -> Optional[str]:
    cid = await _parse_cid(ipfs_url)
    ipfs_file = await repository.read_file(cid)
    request = UploadToGCPRequest(
        destination=f"ipfs_cache/{cid}",
        data=bytes(ipfs_file.data),
        content_type=ipfs_file.content_type,
        check_existence=True,
    )
    return await upload_to_gcp_use_case.execute(request)


async def _parse_cid(ipfs_url: str) -> str:
    return ipfs_url.split("/")[-1]


if __name__ == "__main__":
    import asyncio

    async def main():
        cid = await _parse_cid("ipfs://QmXZv1")
        print(cid)

    asyncio.run(main())
