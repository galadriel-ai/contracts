import pytest

from src.repositories.oracle_repository import OracleRepository


@pytest.mark.asyncio
async def test_oracle_repository():
    oracle_repository = OracleRepository()
    chats = await oracle_repository.get_unanswered_chats()
    assert chats is not None
    functions = await oracle_repository.get_unanswered_function_calls()
    assert functions is not None
    kb_indexing_requests = await oracle_repository.get_unindexed_knowledge_bases()
    assert kb_indexing_requests is not None
    kb_queries = await oracle_repository.get_unanswered_kb_queries()
    assert kb_queries is not None
