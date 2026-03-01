import subprocess
import logging
import os
import re
import time
from backend.utils.temp_files import temp_manager

logger = logging.getLogger(__name__)

# Linker error keywords (same logic as c_handler._is_linker_error)
_LINKER_KEYWORDS = [
    "undefined reference to",
    "ld returned",
    "linker command failed",
    "collect2: error",
    "unresolved external symbol",
    "LNK2019",
    "LNK1120",
]


def _is_linker_error(stderr):
    """Check if stderr contains linker error indicators."""
    stderr_lower = stderr.lower()
    return any(kw.lower() in stderr_lower for kw in _LINKER_KEYWORDS)


def _build_linker_message(stderr):
    """Build a user-friendly linker error message."""
    symbols = re.findall(r"undefined reference to [`']([^`']+)['`]", stderr)
    if symbols:
        parts = [f"Function '{s}' declared but not defined." for s in symbols]
        return "; ".join(parts)
    return "Linker error: unresolved symbols."


class GCCRunner:
    def run(self, code: str, language="c"):
        """
        Compiles and runs the C code.
        Returns: {
            "stdout": str,
            "stderr": str,
            "success": bool,
            "status": str,       # "success" | "compile_error" | "linker_error" | "runtime_error" | "timeout_error"
            "exitCode": int,
            "message": str
        }
        """
        session_dir = temp_manager.create_session_dir()
        source_file = os.path.join(session_dir, "main.c")
        exe_file = os.path.join(session_dir, "main.exe" if os.name == 'nt' else "main")
        
        try:
            # 1. Write Code
            with open(source_file, "w", encoding="utf-8") as f:
                f.write(code)
            
            # 2. Compile
            compile_cmd = ["gcc", source_file, "-o", exe_file]
            logger.info("Compiling: %s", " ".join(compile_cmd))
            compile_proc = subprocess.run(compile_cmd, capture_output=True, text=True, timeout=5)
            
            if compile_proc.returncode != 0:
                combined_stderr = (compile_proc.stderr + "\n" + compile_proc.stdout).strip()
                if _is_linker_error(combined_stderr):
                    status = "linker_error"
                    message = _build_linker_message(combined_stderr)
                    logger.info("Linker error detected: %s", message)
                else:
                    status = "compile_error"
                    message = combined_stderr
                    logger.info("Compile error detected")
                return {
                    "stdout": "",
                    "stderr": combined_stderr,
                    "success": False,
                    "status": status,
                    "exitCode": compile_proc.returncode,
                    "message": message
                }
            
            # 3. Execute
            logger.info("Executing: %s", exe_file)
            try:
                run_proc = subprocess.run([exe_file], capture_output=True, text=True, timeout=2)
                success = run_proc.returncode == 0
                status = "success" if success else "runtime_error"
                logger.info("Execution finished: exitCode=%s", run_proc.returncode)
                return {
                    "stdout": run_proc.stdout,
                    "stderr": run_proc.stderr,
                    "success": success,
                    "status": status,
                    "exitCode": run_proc.returncode,
                    "message": "" if success else (run_proc.stderr.strip() or f"Process exited with code {run_proc.returncode}")
                }
            except subprocess.TimeoutExpired:
                logger.warning("Execution timed out (2s limit)")
                return {
                    "stdout": "",
                    "stderr": "Execution Timed Out (Limit: 2s)",
                    "success": False,
                    "status": "timeout_error",
                    "exitCode": -999,
                    "message": "Execution timed out (limit: 2 seconds)"
                }
                
        except Exception as e:
            logger.error("System error in GCCRunner.run: %s", e, exc_info=True)
            return {
                "stdout": "",
                "stderr": f"System Error: {str(e)}",
                "success": False,
                "status": "runtime_error",
                "exitCode": -1,
                "message": f"System error: {str(e)}"
            }
        finally:
            temp_manager.cleanup(session_dir)

gcc_runner = GCCRunner()
