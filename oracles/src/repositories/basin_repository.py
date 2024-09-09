import anyio
import settings
from typing import Union, Optional
import os
import subprocess
import tempfile


class BasinRepository:
    def __init__(self):
        self.env_var = {
            "NETWORK": settings.OBJECTSTORE_NETWORK,
            "PRIVATE_KEY": settings.OBJECTSTORE_PRIVATE_KEY,
            "PATH": os.environ["PATH"]
        }
        self.objectstore_address = settings.OBJECTSTORE_ADDRESS

    async def read_file(self, key: str, max_bytes: int = 0) -> Optional[str]:
        try:
            content = subprocess.check_output(["adm", "os", "get", "--address", self.objectstore_address , key], env=self.env_var, stderr=subprocess.STDOUT).decode('utf-8')
            return content
        except subprocess.CalledProcessError as e:
            return None
                
    async def read_binary_file(self, key: str, max_bytes: int = 0) -> Optional[bytes]:
        try:
            content = subprocess.check_output(["adm", "os", "get", "--address", self.objectstore_address , key], env=self.env_var, stderr=subprocess.STDOUT)
            return content
        except subprocess.CalledProcessError as e:
            return None

    async def write_file(self, data: Union[str, bytes], key: str):
        temp_file = tempfile.NamedTemporaryFile(delete=False)
        try:
            if isinstance(data, str):
                data = data.encode()
            temp_file.write(data)
            temp_file.flush()
            subprocess.call(["adm", "os", "add", "--address", self.objectstore_address, "--key", "abcd2.txt", temp_file.name], env=self.env_var)
        finally:
            temp_file.close()
            os.unlink(temp_file.name)

if __name__ == "__main__":
    import asyncio

    async def main():
        file_system = BasinRepository()
        with open("../assets/testing.txt", "rb") as file:
            data = file.read()
            await file_system.write_file(data, key="testing.txt")
        file = await file_system.read_file(key="testing.txt")
        print(data)

    asyncio.run(main())
