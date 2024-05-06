import re
import asyncio
import settings
from e2b_code_interpreter import CodeInterpreter
from src.domain.tools.code_interpreter.entities import PythonInterpreterResult


async def _interpret_code(code: str) -> PythonInterpreterResult:
    try:

        def interpret_sync():
            with CodeInterpreter(api_key=settings.E2B_API_KEY) as code_interpreter:
                exec = code_interpreter.notebook.exec_cell(code)
                stdout = "".join(exec.logs.stdout)
                stderr = "".join(exec.logs.stderr)
                if exec.error and len(stderr) == 0:
                    stderr = exec.error.traceback_raw
                return PythonInterpreterResult(
                    output=stdout,
                    error=stderr,
                    exit_code=len(stderr),
                )

        return await asyncio.to_thread(interpret_sync)
    except Exception as e:
        return PythonInterpreterResult(output="", error=str(e), exit_code=1)


async def _strip_markdown_code(md_string: str) -> str:
    stripped_string = re.sub(r"^`{1,3}.*?\n", "", md_string, flags=re.DOTALL)
    stripped_string = re.sub(r"`{1,3}$", "", stripped_string)
    return stripped_string


async def execute(code: str) -> PythonInterpreterResult:
    clean_code = await _strip_markdown_code(code)
    return await _interpret_code(clean_code)


if __name__ == "__main__":
    print(asyncio.run(execute("print(2 + 2)")))
