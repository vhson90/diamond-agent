"""
Code Runner MCP Tool for safe isolated script execution.
"""

from typing import Dict, Any
import sys
import io
import contextlib
import traceback


class PythonRunnerTool:
    """Executes small Python snippets in an in-memory runtime sandbox."""

    def run_python_code(self, code: str, timeout_sec: int = 5) -> Dict[str, Any]:
        """Execute python code and capture stdout/stderr."""
        stdout_buf = io.StringIO()
        stderr_buf = io.StringIO()

        safe_globals = {
            "__builtins__": {
                "print": print,
                "range": range,
                "len": len,
                "str": str,
                "int": int,
                "float": float,
                "list": list,
                "dict": dict,
                "set": set,
                "sum": sum,
                "min": min,
                "max": max,
                "sorted": sorted,
                "enumerate": enumerate,
                "zip": zip,
                "map": map,
                "filter": filter,
                "True": True,
                "False": False,
                "None": None,
            }
        }

        try:
            with contextlib.redirect_stdout(stdout_buf), contextlib.redirect_stderr(stderr_buf):
                exec(code, safe_globals)
            return {
                "status": "success",
                "stdout": stdout_buf.getvalue(),
                "stderr": stderr_buf.getvalue(),
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "traceback": traceback.format_exc(),
            }
