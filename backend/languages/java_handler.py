"""
Java Language Handler — Compile with javac, execute with java.
Extracts class name from source code for proper execution.
"""
import os
import re
from .base import LanguageHandler


class JavaHandler(LanguageHandler):
    def _extract_class_name(self, code: str) -> str:
        """Extract the public class name from Java source code."""
        match = re.search(r'public\s+class\s+(\w+)', code)
        if match:
            return match.group(1)
        # Fallback: look for any class
        match = re.search(r'class\s+(\w+)', code)
        if match:
            return match.group(1)
        return "Main"

    async def execute(self, code: str) -> dict:
        session_dir = self._create_session_dir()
        class_name = self._extract_class_name(code)
        source = os.path.join(session_dir, f"{class_name}.java")

        try:
            with open(source, "w", encoding="utf-8") as f:
                f.write(code)

            # 1. Compile
            stdout, stderr, rc = await self._run_process(
                ["javac", source],
                timeout=self.COMPILE_TIMEOUT,
                cwd=session_dir
            )
            if rc != 0:
                return {"stdout": "", "stderr": stderr, "success": False, "language": "java"}

            # 2. Execute
            stdout, stderr, rc = await self._run_process(
                ["java", "-cp", session_dir, class_name],
                timeout=self.EXECUTE_TIMEOUT,
                cwd=session_dir
            )
            return {
                "stdout": stdout,
                "stderr": stderr,
                "success": rc == 0,
                "language": "java"
            }
        finally:
            self._cleanup(session_dir)

    def get_language_name(self):
        return "java"
