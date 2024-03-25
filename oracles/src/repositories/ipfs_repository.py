import aiohttp
import settings

NFT_STORAGE_LINK_BASE = "https://{}.ipfs.nftstorage.link"


class IpfsRepository:
    async def read_file(self, cid: str) -> str:
        async with aiohttp.ClientSession() as session:
            async with session.get(NFT_STORAGE_LINK_BASE.format(cid)) as response:
                response.raise_for_status()
                return await response.text()

    async def write_file(self, data: str) -> None:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://api.nft.storage/upload",
                headers={
                    "Authorization": f"Bearer {settings.NFT_STORAGE_API_KEY}",
                    "Content-Type": "text/plain",
                },
                data=data,
            ) as response:
                response.raise_for_status()
                json_response = await response.json()
                return json_response.get("value").get("cid")
