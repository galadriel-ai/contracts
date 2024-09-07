import anyio
import settings
from typing import Union, Optional
import os


class FileSystemRepository:
    async def read_file(self, key: str, max_bytes: int = 0) -> Optional[str]:

        if os.path.isfile(f"{settings.FILESYSTEM_PATH}/{key}"):
            async with await anyio.open_file(f"{settings.FILESYSTEM_PATH}/{key}", "r") as file:
                content = await file.read()
                return content
        return None
        
    async def read_binary_file(self, key: str, max_bytes: int = 0) -> Optional[bytes]:
        if os.path.isfile(f"{settings.FILESYSTEM_PATH}/{key}"):
            async with await anyio.open_file(f"{settings.FILESYSTEM_PATH}/{key}", "rb") as file:
                content = await file.read()
                return content
        return None

    async def write_file(self, data: Union[str, bytes], key: str):
        async with await anyio.open_file(f"{settings.FILESYSTEM_PATH}/{key}", "wb") as file:
            await file.write(data)

if __name__ == "__main__":
    import asyncio

    async def main():
        file_system = FileSystemRepository()
        with open("../assets/testing.txt", "rb") as file:
            data = file.read()
            await file_system.write_file(data, key="testing.txt")
        file = await file_system.read_file(key="testing.txt")
        print(data)

    asyncio.run(main())
