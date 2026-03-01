"""
Base Language Handler — Abstract interface for all language backends.
Each language handler implements compile/execute with async subprocess management.

FIXED: Added Windows crash-dialog suppression, compile-only mode, and signal capture.
"""
import asyncio
import logging
import os
import sys
import tempfile
import shutil
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class LanguageHandler(ABC):
    """Abstract base class for all language execution handlers."""

    COMPILE_TIMEOUT = 10  # seconds
    EXECUTE_TIMEOUT = 5   # seconds

    def __init__(self):
        self.base_dir = os.path.join(tempfile.gettempdir(), "online_compiler_sessions")
        os.makedirs(self.base_dir, exist_ok=True)

    def _create_session_dir(self):
        return tempfile.mkdtemp(dir=self.base_dir)

    def _cleanup(self, path):
        try:
            if os.path.isdir(path):
                shutil.rmtree(path, ignore_errors=True)
            elif os.path.exists(path):
                os.remove(path)
        except Exception:
            pass

    @staticmethod
    def _get_subprocess_kwargs():
        """
        Returns platform-specific kwargs for subprocess creation.
        On Windows, suppresses the WER crash dialog so child processes that
        segfault or divide-by-zero terminate immediately instead of hanging.
        """
        kwargs = {}
        if sys.platform == "win32":
            import ctypes
            # SEM_NOGPFAULTERRORBOX | SEM_FAILCRITICALERRORS | SEM_NOOPENFILEERRORBOX
            SEM_NOGPFAULTERRORBOX = 0x0002
            SEM_FAILCRITICALERRORS = 0x0001
            SEM_NOOPENFILEERRORBOX = 0x8000
            try:
                ctypes.windll.kernel32.SetErrorMode(
                    SEM_NOGPFAULTERRORBOX | SEM_FAILCRITICALERRORS | SEM_NOOPENFILEERRORBOX
                )
            except Exception:
                pass
            # CREATE_NO_WINDOW prevents console pop-ups for child processes
            CREATE_NO_WINDOW = 0x08000000
            kwargs["creationflags"] = CREATE_NO_WINDOW
        return kwargs

    async def _run_process(self, cmd, timeout, cwd=None, stdin_data=None):
        """
        Run a subprocess asynchronously with timeout.
        Returns (stdout, stderr, returncode).
        Handles Windows crash dialogs, timeouts, and all exceptions.
        """
        try:
            logger.info("Running subprocess: %s (timeout=%ss)", ' '.join(str(c) for c in cmd), timeout)
            extra_kwargs = self._get_subprocess_kwargs()
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                stdin=asyncio.subprocess.PIPE if stdin_data else None,
                cwd=cwd,
                **extra_kwargs
            )
            try:
                stdout, stderr = await asyncio.wait_for(
                    proc.communicate(input=stdin_data.encode() if stdin_data else None),
                    timeout=timeout
                )
                logger.info("Subprocess exited with code %s", proc.returncode)
                if proc.returncode != 0:
                    logger.debug("Subprocess stderr: %s", stderr.decode(errors='replace')[:500])
                return stdout.decode(errors='replace'), stderr.decode(errors='replace'), proc.returncode
            except asyncio.TimeoutError:
                logger.warning("Subprocess timed out after %ss, killing process", timeout)
                # Kill the process tree on timeout
                try:
                    proc.kill()
                    await proc.wait()
                except Exception:
                    pass
                return "", f"⏱ Timed out after {timeout}s", -999  # special code for timeout
        except FileNotFoundError as e:
            logger.error("Tool not found: %s", e.filename)
            return "", f"Tool not found: {e.filename}. Make sure the compiler/interpreter is installed and on PATH.", -1
        except PermissionError as e:
            logger.error("Permission denied: %s", e)
            return "", f"Permission denied: {str(e)}", -1
        except OSError as e:
            logger.error("OS error running process: %s", e)
            return "", f"OS error running process: {str(e)}", -1
        except Exception as e:
            logger.error("Unexpected error running process: %s", e, exc_info=True)
            return "", f"System error: {str(e)}", -1

    @abstractmethod
    async def execute(self, code: str) -> dict:
        """
        Compile and/or execute the code.
        Must return: {
            "stdout": str,
            "stderr": str,
            "success": bool,
            "language": str,
            "status": str,       # "success" | "compile_error" | "linker_error" | "runtime_error" | "timeout_error"
            "exitCode": int,
            "signal": str,
            "message": str
        }
        """
        pass

    async def compile_only(self, code: str) -> dict:
        """
        Compile code WITHOUT executing it. Used by the autofix pipeline
        for safe error detection. Subclasses should override for compiled languages.
        Default: falls back to execute().
        """
        return await self.execute(code)

    @abstractmethod
    def get_language_name(self) -> str:
        pass
