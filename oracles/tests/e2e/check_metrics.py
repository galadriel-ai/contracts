import json


def check_metrics(metrics: dict):
    assert "transactions_sent" in metrics, "transactions_sent key is missing"
    assert "errors" in metrics, "errors key is missing"
    assert len(metrics.keys()) == 27, "metrics.json should have 27 keys"
    assert metrics["errors"] == 0, "errors should be 0"
    assert metrics["transactions_sent"] == 14, "transactions_sent should be 14"
    assert metrics["chats_count"] == 9, "chats_count should be 9"
    assert metrics["chats_read"] == 9, "chats_read should be 9"
    assert metrics["chats_answered"] == 9, "chats_answered should be 9"
    assert (
        metrics["chats_configuration_errors"] == 0
    ), "chats_configuration_errors should be 0"
    assert (
        metrics["chats_history_read_errors"] == 0
    ), "chats_history_read_errors should be 0"
    assert metrics["chats_write_errors"] == 0, "chats_write_errors should be 0"
    assert metrics["chats_marked_as_done"] == 9, "chats_marked_as_done should be 9"
    assert metrics["functions_count"] == 3, "functions_count should be 3"
    assert metrics["functions_read"] == 3, "functions_read should be 3"
    assert metrics["functions_answered"] == 3, "functions_answered should be 3"
    assert metrics["functions_read_errors"] == 0, "functions_read_errors should be 0"
    assert metrics["functions_write_errors"] == 0, "functions_write_errors should be 0"
    assert metrics["functions_marked_as_done"] == 3, "functions_marked_as_done should be 3"
    assert (
        metrics["knowledgebase_index_count"] == 1
    ), "knowledgebase_index_count should be 1"
    assert (
        metrics["knowledgebase_index_read"] == 1
    ), "knowledgebase_index_read should be 1"
    assert (
        metrics["knowledgebase_index_answered"] == 1
    ), "knowledgebase_index_answered should be 1"
    assert (
        metrics["knowledgebase_index_read_errors"] == 0
    ), "knowledgebase_index_read_errors should be 0"
    assert (
        metrics["knowledgebase_index_write_errors"] == 0
    ), "knowledgebase_index_write_errors should be 0"
    assert (
        metrics["knowledgebase_index_marked_as_done"] == 1
    ), "knowledgebase_index_marked_as_done should be 1"
    assert (
        metrics["knowledgebase_query_count"] == 1
    ), "knowledgebase_query_count should be 1"
    assert (
        metrics["knowledgebase_query_read"] == 1
    ), "knowledgebase_query_read should be 1"
    assert (
        metrics["knowledgebase_query_answered"] == 1
    ), "knowledgebase_query_answered should be 1"
    assert (
        metrics["knowledgebase_query_read_errors"] == 0
    ), "knowledgebase_query_read_errors should be 0"
    assert (
        metrics["knowledgebase_query_write_errors"] == 0
    ), "knowledgebase_query_write_errors should be 0"
    assert (
        metrics["knowledgebase_query_marked_as_done"] == 1
    ), "knowledgebase_query_marked_as_done should be 1"
    print("Metrics validation passed.")


if __name__ == "__main__":
    with open("metrics.json", "r") as f:
        metrics = json.load(f)
        check_metrics(metrics)
