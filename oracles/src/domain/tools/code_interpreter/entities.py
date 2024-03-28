from dataclasses import dataclass


@dataclass
class PythonInterpreterResult:
    stdout: str
    stderr: str
    exit_code: int
