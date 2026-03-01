"""
C++ Language Handler — Compile with g++, execute binary.

FIXED: Added compile_only(), runtime error classification, structured responses,
and warnings extraction.
"""
import os
from .base import LanguageHandler
from .c_handler import _classify_runtime_exit, _is_linker_error
from backend.compiler.gcc_error_parser import gcc_error_parser


class CppHandler(LanguageHandler):
    async def compile_only(self, code: str) -> dict:
        """Compile C++ code WITHOUT executing it."""
        session_dir = self._create_session_dir()
        source = os.path.join(session_dir, "main.cpp")
        exe = os.path.join(session_dir, "main.exe" if os.name == 'nt' else "main")

        try:
            with open(source, "w", encoding="utf-8") as f:
                f.write(code)

            stdout, stderr, rc = await self._run_process(
                ["g++", source, "-o", exe, "-std=c++17"],
                timeout=self.COMPILE_TIMEOUT
            )

            warnings_list = gcc_error_parser.extract_warnings(stderr)
            warnings_text = gcc_error_parser.format_warnings_text(stderr)

            if rc != 0:
                status = "linker_error" if _is_linker_error(stderr) else "compile_error"
                return {
                    "stdout": "", "stderr": stderr, "success": False,
                    "language": "cpp", "status": status, "exitCode": rc,
                    "signal": "", "message": stderr.strip(),
                    "warnings": warnings_text, "warnings_list": warnings_list
                }
            return {
                "stdout": "", "stderr": "", "success": True,
                "language": "cpp", "status": "success", "exitCode": 0,
                "signal": "", "message": "Compilation successful",
                "warnings": warnings_text, "warnings_list": warnings_list
            }
        except Exception as e:
            return {
                "stdout": "", "stderr": str(e), "success": False,
                "language": "cpp", "status": "compile_error", "exitCode": -1,
                "signal": "", "message": f"Compile system error: {e}",
                "warnings": "", "warnings_list": []
            }
        finally:
            self._cleanup(session_dir)

    async def execute(self, code: str) -> dict:
        """Compile and execute C++ code with full error classification."""
        session_dir = self._create_session_dir()
        source = os.path.join(session_dir, "main.cpp")
        exe = os.path.join(session_dir, "main.exe" if os.name == 'nt' else "main")

        try:
            with open(source, "w", encoding="utf-8") as f:
                f.write(code)

            # 1. Compile
            stdout, stderr, rc = await self._run_process(
                ["g++", source, "-o", exe, "-std=c++17"],
                timeout=self.COMPILE_TIMEOUT
            )

            warnings_list = gcc_error_parser.extract_warnings(stderr)
            warnings_text = gcc_error_parser.format_warnings_text(stderr)

            if rc != 0:
                status = "linker_error" if _is_linker_error(stderr) else "compile_error"
                if status == "linker_error":
                    friendly_msg = gcc_error_parser.build_linker_message(stderr)
                else:
                    friendly_msg = stderr.strip()
                return {
                    "stdout": "", "stderr": stderr, "success": False,
                    "language": "cpp", "status": status, "exitCode": rc,
                    "signal": "", "message": friendly_msg,
                    "warnings": warnings_text, "warnings_list": warnings_list
                }

            # 2. Execute
            stdout, stderr, rc = await self._run_process(
                [exe],
                timeout=self.EXECUTE_TIMEOUT,
                cwd=session_dir
            )
            status, signal_name, message = _classify_runtime_exit(rc, stderr)
            return {
                "stdout": stdout, "stderr": stderr,
                "success": rc == 0, "language": "cpp",
                "status": status, "exitCode": rc,
                "signal": signal_name, "message": message,
                "warnings": warnings_text, "warnings_list": warnings_list
            }
        except Exception as e:
            return {
                "stdout": "", "stderr": str(e), "success": False,
                "language": "cpp", "status": "runtime_error", "exitCode": -1,
                "signal": "", "message": f"System error: {e}",
                "warnings": "", "warnings_list": []
            }
        finally:
            self._cleanup(session_dir)

    def get_language_name(self):
        return "cpp"

