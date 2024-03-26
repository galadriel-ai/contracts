import json


def format_tool_input(tool_input: str) -> str:
    formatted_input = tool_input
    if formatted_input.startswith("{"):
        try:
            parsed = json.loads(formatted_input)
            formatted_input = parsed[list(parsed.keys())[0]]
        except:
            pass
    return formatted_input
