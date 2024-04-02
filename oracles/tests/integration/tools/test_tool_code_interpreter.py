import pytest
from src.domain.tools.code_interpreter import python_interpreter_use_case
from src.domain.tools.code_interpreter.entities import PythonInterpreterResult


def _format_json_output(stdout: str, stderr: str) -> str:
    return f'{{"stdout": "{stdout}", "stderr": "{stderr}"}}'


@pytest.mark.asyncio
async def test_python_interpreter_success():
    code = "print('Hello world')"
    result = await python_interpreter_use_case.execute(code)
    assert result == PythonInterpreterResult(
        output=_format_json_output("Hello world\\n", ""),
        error="",
        exit_code=0,
    )
