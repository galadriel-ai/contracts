import re
import json
import base64
import aiohttp
import settings
from src.domain.tools.code_interpreter.entities import PythonInterpreterResult


async def _interpret_code(code: str) -> PythonInterpreterResult:
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://exec.bearly.ai/v1/interpreter",
                headers={
                    "Authorization": settings.BEARLY_API_KEY,
                },
                json={
                    "fileContents": code,
                    "inputFiles": [],
                    "outputDir": "output/",
                    "outputAsLinks": True,
                },
            ) as response:
                response.raise_for_status()
                data = await response.json()
                stdout = base64.b64decode(data["stdoutBasesixtyfour"]).decode() if data["stdoutBasesixtyfour"] else ""
                stderr = base64.b64decode(data["stderrBasesixtyfour"]).decode() if data["stderrBasesixtyfour"] else ""
                output = json.dumps({"stdout": stdout, "stderr": stderr})
                return PythonInterpreterResult(
                    output=output,
                    error="",
                    exit_code=data["exitCode"],
                )
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
    import asyncio

    print(asyncio.run(execute("print(2 + 2)")))
