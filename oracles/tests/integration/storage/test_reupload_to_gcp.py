import pytest

from src.domain.storage import reupload_url_to_gcp_use_case


@pytest.mark.asyncio
async def test_reupload_url_to_gcp_use_case():
    download_url = "https://picsum.photos/200/200"
    result = await reupload_url_to_gcp_use_case.execute(download_url)
    assert len(result) > 0
