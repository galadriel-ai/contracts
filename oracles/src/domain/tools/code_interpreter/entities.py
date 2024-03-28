from dataclasses import dataclass


@dataclass
class PythonInterpreterResult:
    output: str
    error: str
    exit_code: int
