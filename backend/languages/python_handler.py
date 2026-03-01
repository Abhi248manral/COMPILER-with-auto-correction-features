"""
Python Language Handler — Interpreted execution, no compile step.
"""
import os
import sys
from .base import LanguageHandler


class PythonHandler(LanguageHandler):
    async def execute(self, code: str) -> dict:
        session_dir = self._create_session_dir()
        source = os.path.join(session_dir, "main.py")

        try:
            with open(source, "w", encoding="utf-8") as f:
                f.write(code)

            # Direct execution via python interpreter
            python_exe = sys.executable  # Use the same Python running the server
            stdout, stderr, rc = await self._run_process(
                [python_exe, "-u", source],
                timeout=self.EXECUTE_TIMEOUT,
                cwd=session_dir
            )
            return {
                "stdout": stdout,
                "stderr": stderr,
                "success": rc == 0,
                "language": "python"
            }
        finally:
            self._cleanup(session_dir)

    def get_language_name(self):
        return "python"
