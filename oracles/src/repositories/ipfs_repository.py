import aiohttp
import settings
from typing import Union

NFT_STORAGE_LINK_BASE = "https://{}.ipfs.nftstorage.link"


class IpfsRepository:
    async def read_file(self, cid: str, max_bytes: int = 0) -> bytes:
        async with aiohttp.ClientSession() as session:
            async with session.get(NFT_STORAGE_LINK_BASE.format(cid)) as response:
                response.raise_for_status()
                data = bytearray()
                while True:
                    chunk = await response.content.read(4096)
                    if not chunk:
                        break
                    data += chunk
                    if max_bytes > 0 and len(data) > max_bytes:
                        raise Exception(
                            f"File exceeded the maximum allowed size of {max_bytes} bytes."
                        )
                return data

    async def write_file(self, data: Union[str, bytes]) -> str:
        mime_type = (
            "text/plain" if isinstance(data, str) else "application/octet-stream"
        )
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://api.nft.storage/upload",
                headers={
                    "Authorization": f"Bearer {settings.NFT_STORAGE_API_KEY}",
                    "Content-Type": mime_type,
                },
                data=data,
            ) as response:
                response.raise_for_status()
                json_response = await response.json()
                return json_response.get("value").get("cid")


if __name__ == "__main__":
    import asyncio

    async def main():
        ipfs = IpfsRepository()
        print(await ipfs.write_file(bytes([1, 2, 3, 4, 5, 6, 7, 8, 9, 10])))

    asyncio.run(main())
