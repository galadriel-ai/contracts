import pytest

from src.repositories.ipfs_repository import IpfsRepository


@pytest.mark.asyncio
async def test_ipfs_repository():
    ipfs = IpfsRepository()
    cid = await ipfs.write_file(bytes([1, 2, 3, 4, 5, 6, 7, 8, 9, 10]))
    assert cid is not None
    data = await ipfs.read_file(cid)
    assert data == bytes([1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
