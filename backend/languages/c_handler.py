"""
C Language Handler — Compile with gcc, execute binary.

FIXED: Added compile_only(), runtime error classification (segfault, div-by-zero),
exit code / signal / status reporting, and linker error detection.
"""
import logging
import os
import sys
from .base import LanguageHandler
from backend.compiler.gcc_error_parser import gcc_error_parser

logger = logging.getLogger(__name__)


# Windows-specific exit codes for crashes
_WINDOWS_CRASH_CODES = {
    0xC0000005: ("SIGSEGV", "Segmentation fault (access violation)"),
    0xC0000094: ("SIGFPE",  "Floating point exception (division by zero)"),
    0xC00000FD: ("SIGSEGV", "Stack overflow"),
    0xC0000409: ("SIGABRT", "Stack buffer overrun detected"),
    0x80000003: ("SIGTRAP", "Breakpoint / debug trap"),
}

# Unix signal numbers
_UNIX_SIGNALS = {
    -11: ("SIGSEGV", "Segmentation fault"),
    -8:  ("SIGFPE",  "Floating point exception (division by zero)"),
    -6:  ("SIGABRT", "Aborted"),
    -9:  ("SIGKILL", "Killed"),
    -4:  ("SIGILL",  "Illegal instruction"),
    -7:  ("SIGBUS",  "Bus error"),
}


def _classify_runtime_exit(returncode, stderr):
    """Classify a runtime crash from exit code and stderr."""
    if returncode == 0:
        return "success", "", "Program executed successfully"

    # Windows: exit codes are unsigned 32-bit values for crashes
    if sys.platform == "win32":
        # Convert signed to unsigned for matching
        unsigned_code = returncode & 0xFFFFFFFF
        if unsigned_code in _WINDOWS_CRASH_CODES:
            signal_name, description = _WINDOWS_CRASH_CODES[unsigned_code]
            return "runtime_error", signal_name, description

    # Unix: negative return codes indicate signals
    if returncode < 0 and returncode in _UNIX_SIGNALS:
        signal_name, description = _UNIX_SIGNALS[returncode]
        return "runtime_error", signal_name, description

    # Timeout sentinel
    if returncode == -999:
        return "timeout_error", "", "Execution timed out"

    # Generic non-zero exit
    msg = stderr.strip() if stderr.strip() else f"Process exited with code {returncode}"
    return "runtime_error", "", msg


def _is_linker_error(stderr):
    """Check if stderr contains linker errors (undefined reference, etc.)."""
    linker_keywords = [
        "undefined reference to",
        "ld returned",
        "linker command failed",
        "collect2: error",
        "unresolved external symbol",
        "LNK2019",  # MSVC linker
        "LNK1120",  # MSVC linker
    ]
    stderr_lower = stderr.lower()
    is_linker = any(kw.lower() in stderr_lower for kw in linker_keywords)
    if is_linker:
        logger.info("Linker error detected in stderr")
    return is_linker


class CHandler(LanguageHandler):
    async def compile_only(self, code: str) -> dict:
        logger.info("CHandler.compile_only() invoked")
        """
        Compile code WITHOUT executing it.
        Used by the autofix pipeline for safe error detection.
        """
        session_dir = self._create_session_dir()
        source = os.path.join(session_dir, "main.c")
        exe = os.path.join(session_dir, "main.exe" if os.name == 'nt' else "main")

        try:
            with open(source, "w", encoding="utf-8") as f:
                f.write(code)

            stdout, stderr, rc = await self._run_process(
                ["gcc", source, "-o", exe, "-lm"],
                timeout=self.COMPILE_TIMEOUT
            )

            # Extract warnings from stderr (present even if build succeeds or fails)
            warnings_list = gcc_error_parser.extract_warnings(stderr)
            warnings_text = gcc_error_parser.format_warnings_text(stderr)

            if rc != 0:
                status = "linker_error" if _is_linker_error(stderr) else "compile_error"
                return {
                    "stdout": "", "stderr": stderr, "success": False,
                    "language": "c", "status": status, "exitCode": rc,
                    "signal": "", "message": stderr.strip(),
                    "warnings": warnings_text, "warnings_list": warnings_list
                }

            return {
                "stdout": "", "stderr": "", "success": True,
                "language": "c", "status": "success", "exitCode": 0,
                "signal": "", "message": "Compilation successful",
                "warnings": warnings_text, "warnings_list": warnings_list
            }
        except Exception as e:
            return {
                "stdout": "", "stderr": str(e), "success": False,
                "language": "c", "status": "compile_error", "exitCode": -1,
                "signal": "", "message": f"Compile system error: {e}",
                "warnings": "", "warnings_list": []
            }
        finally:
            self._cleanup(session_dir)

    async def execute(self, code: str) -> dict:
        """Compile and execute C code with full error classification."""
        logger.info("CHandler.execute() invoked")
        session_dir = self._create_session_dir()
        source = os.path.join(session_dir, "main.c")
        exe = os.path.join(session_dir, "main.exe" if os.name == 'nt' else "main")

        try:
            with open(source, "w", encoding="utf-8") as f:
                f.write(code)

            # 1. Compile
            stdout, stderr, rc = await self._run_process(
                ["gcc", source, "-o", exe, "-lm"],
                timeout=self.COMPILE_TIMEOUT
            )

            # Extract warnings from compile stderr
            warnings_list = gcc_error_parser.extract_warnings(stderr)
            warnings_text = gcc_error_parser.format_warnings_text(stderr)

            if rc != 0:
                status = "linker_error" if _is_linker_error(stderr) else "compile_error"
                logger.info("Compilation failed: status=%s, exitCode=%s", status, rc)
                # Build user-friendly message for linker errors
                if status == "linker_error":
                    friendly_msg = gcc_error_parser.build_linker_message(stderr)
                else:
                    friendly_msg = stderr.strip()
                return {
                    "stdout": "", "stderr": stderr, "success": False,
                    "language": "c", "status": status, "exitCode": rc,
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
            logger.info("Execution result: status=%s, signal=%s, exitCode=%s", status, signal_name, rc)

            return {
                "stdout": stdout,
                "stderr": stderr,
                "success": rc == 0,
                "language": "c",
                "status": status,
                "exitCode": rc,
                "signal": signal_name,
                "message": message,
                "warnings": warnings_text, "warnings_list": warnings_list
            }
        except Exception as e:
            return {
                "stdout": "", "stderr": str(e), "success": False,
                "language": "c", "status": "runtime_error", "exitCode": -1,
                "signal": "", "message": f"System error: {e}",
                "warnings": "", "warnings_list": []
            }
        finally:
            self._cleanup(session_dir)

    def get_language_name(self):
        return "c"
