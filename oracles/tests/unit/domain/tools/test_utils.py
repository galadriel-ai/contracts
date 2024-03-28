from src.domain.tools import utils


def test_tool_input_not_formats_plain_str():
    assert utils.format_tool_input("asd") == "asd"
    assert utils.format_tool_input("") == ""
    assert utils.format_tool_input("{ something") == "{ something"


def test_tool_input_formats_valid_json():
    assert utils.format_tool_input("{\"query\": \"asd\"}") == "asd"
    assert utils.format_tool_input("{\"asd\": \"asd\"}") == "asd"
