import pytest

from src.domain.tools.image_generation import generate_image_use_case


@pytest.mark.asyncio
async def test_generate_image_use_case():
    query = "white horse"
    result = await generate_image_use_case.execute(query)
    assert len(result.url) > 0
    assert result.error == ""
