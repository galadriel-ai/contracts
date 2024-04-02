import pytest

from src.domain.tools.search import web_search_use_case


@pytest.mark.asyncio
async def test_web_search_use_case():
    query = "test"
    result = await web_search_use_case.execute(query)
    assert len(result.result) > 0
    assert result.error == ""
