import aiohttp
import settings
from typing import Union

from src.domain.storage.entities import IpfsFile

PINATA_LINK_BASE = "https://galadriel.mypinata.cloud/ipfs/{}"


class IpfsRepository:
    async def read_file(self, cid: str, max_bytes: int = 0) -> IpfsFile:
        async with aiohttp.ClientSession() as session:
            headers = {"x-pinata-gateway-token": settings.PINATA_GATEWAY_TOKEN}
            async with session.get(
                PINATA_LINK_BASE.format(cid), headers=headers
            ) as response:
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
                return IpfsFile(
                    cid=cid,
                    data=data,
                    content_type=response.headers.get("Content-Type"),
                )

    async def write_file(self, data: Union[str, bytes]) -> str:
        mime_type = (
            "text/plain" if isinstance(data, str) else "application/octet-stream"
        )
        form_data = aiohttp.FormData()
        form_data.add_field("file", data, filename="file", content_type=mime_type)
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://api.pinata.cloud/pinning/pinFileToIPFS",
                headers={
                    "Authorization": f"Bearer {settings.PINATA_API_JWT}",
                },
                data=form_data,
            ) as response:
                response.raise_for_status()
                json_response = await response.json()
                return json_response.get("IpfsHash")


if __name__ == "__main__":
    import asyncio

    async def main():
        ipfs = IpfsRepository()
        with open("../stack.jpg", "rb") as file:
            image_bytes = file.read()
            cid = await ipfs.write_file(image_bytes)
        assert cid is not None
        file = await ipfs.read_file(cid)
        assert file.cid == cid
        assert file.content_type == "image/jpeg"
        assert file.data == image_bytes

    asyncio.run(main())
