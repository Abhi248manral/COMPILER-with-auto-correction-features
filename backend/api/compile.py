"""
Compile API Router — Multi-language compilation endpoint.
Fully async, non-blocking, with language routing and autofix pipeline.

FIXED:
  - Global try/except on /compile endpoint — NEVER drops the connection
  - Autofix pipeline uses compile_only() — never runs dangerous code during detection
  - Structured response with status, exitCode, signal, message fields
"""
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
import logging
import traceback

logger = logging.getLogger(__name__)

router = APIRouter()

# ── Language Handler Registry ────────────────────────────────────────
from backend.languages.c_handler import CHandler
from backend.languages.cpp_handler import CppHandler
from backend.languages.python_handler import PythonHandler
from backend.languages.java_handler import JavaHandler
from backend.languages.web_handler import HTMLHandler, CSSHandler

LANGUAGE_HANDLERS = {
    "c": CHandler(),
    "cpp": CppHandler(),
    "python": PythonHandler(),
    "java": JavaHandler(),
    "html": HTMLHandler(),
    "css": CSSHandler(),
}

# ── Request / Response Models ────────────────────────────────────────
class CompileRequest(BaseModel):
    code: str
    language: str = "c"
    autofix: bool = True

class CompileResponse(BaseModel):
    success: bool
    language: str
    original_code: str
    fixed_code: str
    final_compile_output: str
    original_errors: list = []
    fixes_applied: list = []
    preview: Optional[str] = None
    status: str = "success"
    warnings: str = ""
    warnings_list: list = []
    exitCode: int = 0
    signal: str = ""
    message: str = ""


# ── Autofix Pipeline (for compiled languages) ────────────────────────
async def _run_autofix_pipeline(code: str, language: str) -> tuple:
    """
    Multi-pass autofix for C/C++.
    Returns (fixed_code, all_fixes, last_errors).
    FIXED: Uses compile_only() instead of execute() to avoid running dangerous code.
    """
    from backend.autofix.engine import get_fix_engine

    engine = get_fix_engine(language)
    all_fixes = []
    last_errors = []
    MAX_ITERATIONS = 3

    for _ in range(MAX_ITERATIONS):
        current_errors = []

        # Only use tree-sitter parsing for C (it's C-specific)
        if language == "c":
            try:
                from backend.parser.tree_sitter_c import c_parser
                tree = c_parser.parse(code)
                syntax_errors = c_parser.get_errors(tree)
                current_errors.extend(syntax_errors)
            except Exception:
                pass

        # For C/C++, compile-only to detect errors (NEVER execute during autofix)
        if language in ("c", "cpp"):
            handler = LANGUAGE_HANDLERS[language]
            try:
                result = await handler.compile_only(code)
            except Exception:
                result = {"success": True, "stderr": ""}

            # SHORT-CIRCUIT: linker errors can't be auto-fixed (missing definitions)
            if result.get("status") == "linker_error":
                logger.info("Autofix pipeline: linker error detected, skipping autofix")
                break

            if not result["success"] and result.get("stderr"):
                from backend.compiler.gcc_error_parser import gcc_error_parser
                gcc_errors = gcc_error_parser.parse_gcc_output(result["stderr"])
                for e in gcc_errors:
                    current_errors.append({
                        'line': e['line'],
                        'start_point': (e['line'] - 1, 0),
                        'end_point': (e['line'] - 1, 10),
                        'text': '',
                        'type': e['type'],
                        'message': e['message']
                    })

        # Deduplicate
        unique_errors = []
        seen = set()
        for e in current_errors:
            key = (e.get('line', e.get('start_point', (0,))[0]), e.get('type'), e.get('message', ''))
            if key not in seen:
                seen.add(key)
                unique_errors.append(e)

        last_errors = unique_errors

        if unique_errors:
            try:
                new_code, applied = engine.apply_fixes(code, unique_errors)
            except Exception:
                break
            if new_code != code:
                code = new_code
                all_fixes.extend(applied)
            else:
                break
        else:
            break

    return code, all_fixes, last_errors


def _simple_error_detect(code: str, language: str) -> list:
    """
    Lightweight error detection for Python/Java/HTML/CSS (no external compiler needed).
    Returns list of error dicts for the autofix engine.
    """
    errors = []
    lines = code.split('\n')

    if language == "python":
        for i, line in enumerate(lines):
            stripped = line.rstrip()
            # Missing colon
            import re
            for kw in ['if', 'for', 'while', 'def', 'class', 'elif', 'else', 'try', 'except', 'finally', 'with']:
                if re.match(rf'^\s*{kw}\b', stripped) and not stripped.endswith(':') and not stripped.endswith('\\'):
                    errors.append({
                        'line': i + 1, 'start_point': (i, 0), 'end_point': (i, len(stripped)),
                        'text': stripped, 'type': 'missing_colon',
                        'message': f"Missing colon after '{kw}'"
                    })
            # Unbalanced parens
            if line.count('(') > line.count(')'):
                errors.append({
                    'line': i + 1, 'start_point': (i, 0), 'end_point': (i, len(stripped)),
                    'text': stripped, 'type': 'unbalanced_paren',
                    'message': 'Unbalanced parentheses'
                })
            # Mixed tabs/spaces
            if '\t' in line and '    ' in line:
                errors.append({
                    'line': i + 1, 'start_point': (i, 0), 'end_point': (i, len(line)),
                    'text': line, 'type': 'indentation',
                    'message': 'Mixed tabs and spaces'
                })

    elif language == "java":
        for i, line in enumerate(lines):
            stripped = line.strip()
            if (stripped and ':' not in stripped and
                    not stripped.startswith('//') and not stripped.startswith('/*') and
                    not stripped.startswith('*') and not stripped.startswith('import') and
                    not stripped.startswith('package') and
                    not stripped.endswith(';') and not stripped.endswith('{') and
                    not stripped.endswith('}') and not stripped.endswith(',') and
                    not stripped.endswith('(') and
                    (stripped.endswith(')') or (stripped and stripped[-1].isalnum()))):
                errors.append({
                    'line': i + 1, 'start_point': (i, 0), 'end_point': (i, len(stripped)),
                    'text': stripped, 'type': 'missing_semicolon',
                    'message': 'Missing semicolon'
                })

    elif language == "html":
        import re
        all_code = '\n'.join(lines)
        open_tags = re.findall(r'<(\w+)[^/]*?>', all_code)
        close_tags = re.findall(r'</(\w+)>', all_code)
        void_elements = {'br', 'hr', 'img', 'input', 'meta', 'link', 'area', 'base', 'col', 'embed', 'source', 'track', 'wbr'}
        tag_stack = [t.lower() for t in open_tags if t.lower() not in void_elements]
        for t in close_tags:
            if t.lower() in tag_stack:
                tag_stack.remove(t.lower())
        for tag in tag_stack:
            errors.append({
                'line': len(lines), 'start_point': (len(lines) - 1, 0), 'end_point': (len(lines) - 1, 10),
                'text': '', 'type': 'unclosed_tag',
                'message': f'Unclosed <{tag}> tag'
            })

    elif language == "css":
        all_code = '\n'.join(lines)
        if all_code.count('{') != all_code.count('}'):
            errors.append({
                'line': len(lines), 'start_point': (len(lines) - 1, 0), 'end_point': (len(lines) - 1, 10),
                'text': '', 'type': 'unbalanced_brace',
                'message': 'Unbalanced braces'
            })
        for i, line in enumerate(lines):
            stripped = line.strip()
            if (':' in stripped and not stripped.endswith(';') and
                    not stripped.endswith('{') and not stripped.endswith('}') and
                    not stripped.startswith('/*') and not stripped.startswith('//')):
                errors.append({
                    'line': i + 1, 'start_point': (i, 0), 'end_point': (i, len(stripped)),
                    'text': stripped, 'type': 'missing_semicolon',
                    'message': 'Missing semicolon in CSS declaration'
                })

    return errors


def _build_error_output(result: dict) -> str:
    """Build a human-readable output string from a handler result."""
    status = result.get("status", "")
    stdout = result.get("stdout", "")
    stderr = result.get("stderr", "")
    message = result.get("message", "")
    signal = result.get("signal", "")

    parts = []
    # Show warnings first if present
    warnings = result.get("warnings", "")
    if warnings:
        parts.append("⚠️ Warnings:")
        parts.append(warnings)
        parts.append("")  # blank line separator

    if status == "compile_error":
        parts.append("⚠️ Compilation Error:")
        if stderr:
            parts.append(stderr)
    elif status == "linker_error":
        parts.append("🔗 Linker Error:")
        if stderr:
            parts.append(stderr)
    elif status == "runtime_error":
        parts.append("💥 Runtime Error:")
        if signal:
            parts.append(f"Signal: {signal}")
        if message:
            parts.append(message)
        if stderr:
            parts.append(stderr)
        if stdout:
            parts.append(f"\nPartial output before crash:\n{stdout}")
    elif status == "timeout_error":
        parts.append("⏱ Execution Timed Out")
        if message:
            parts.append(message)
    elif status == "success":
        return stdout
    else:
        # Fallback
        if stderr:
            parts.append(stderr)
        if stdout:
            parts.append(stdout)

    return "\n".join(parts) if parts else (stderr or stdout or message or "Unknown error")


# ── Main Compile Endpoint ────────────────────────────────────────────
@router.post("/compile")
async def compile_code(req: CompileRequest):
    """
    Main compile endpoint. GUARANTEED to return valid JSON — never crashes.
    Wraps all logic in try/except so the server never drops the connection.
    """
    try:
        code = req.code
        original_code = code
        language = req.language.lower()
        all_fixes = []
        errors = []

        # Validate language
        if language not in LANGUAGE_HANDLERS:
            return {
                "success": False,
                "language": language,
                "original_code": original_code,
                "fixed_code": code,
                "final_compile_output": f"Unsupported language: {language}. Supported: {', '.join(LANGUAGE_HANDLERS.keys())}",
                "original_errors": [],
                "fixes_applied": [],
                "status": "compile_error",
                "warnings": "",
                "warnings_list": [],
                "exitCode": -1,
                "signal": "",
                "message": f"Unsupported language: {language}"
            }

        handler = LANGUAGE_HANDLERS[language]

        # ── Step 1: Autofix (if enabled) ──
        if req.autofix:
            if language in ("c", "cpp"):
                # Full pipeline with GCC error parsing (compile-only, no execution)
                try:
                    code, all_fixes, errors = await _run_autofix_pipeline(code, language)
                except Exception as e:
                    # Autofix failed but we continue with original code
                    errors = [{"line": 0, "type": "autofix_error", "message": str(e)}]
            else:
                # Lightweight error detection + fix for other languages
                try:
                    from backend.autofix.engine import get_fix_engine
                    engine = get_fix_engine(language)
                    detected = _simple_error_detect(code, language)
                    errors = detected
                    if detected:
                        new_code, applied = engine.apply_fixes(code, detected)
                        if new_code != code:
                            code = new_code
                            all_fixes = applied
                except Exception:
                    pass  # Autofix failure is non-fatal

        # ── Step 2: Execute / Validate ──
        try:
            result = await handler.execute(code)
        except Exception as e:
            result = {
                "stdout": "",
                "stderr": str(e),
                "success": False,
                "language": language,
                "status": "runtime_error",
                "exitCode": -1,
                "signal": "",
                "message": f"Execution system error: {e}"
            }

        # Build the output string
        output = _build_error_output(result)

        # Enrich linker error message with user-friendly text
        result_message = result.get("message", "")
        result_status = result.get("status", "success" if result.get("success") else "compile_error")
        if result_status == "linker_error" and result.get("stderr"):
            from backend.compiler.gcc_error_parser import gcc_error_parser
            result_message = gcc_error_parser.build_linker_message(result["stderr"])
            logger.info("Linker error response: %s", result_message)

        return {
            "success": result.get("success", False),
            "language": language,
            "original_code": original_code,
            "fixed_code": code,
            "final_compile_output": output,
            "original_errors": errors,
            "fixes_applied": all_fixes,
            "preview": result.get("preview"),
            "status": result_status,
            "warnings": result.get("warnings", ""),
            "warnings_list": result.get("warnings_list", []),
            "exitCode": result.get("exitCode", 0),
            "signal": result.get("signal", ""),
            "message": result_message
        }

    except Exception as e:
        # ── ULTIMATE SAFETY NET ──────────────────────────────────────
        # This catch-all ensures the server NEVER drops the connection.
        return {
            "success": False,
            "language": getattr(req, 'language', 'unknown'),
            "original_code": getattr(req, 'code', ''),
            "fixed_code": getattr(req, 'code', ''),
            "final_compile_output": f"Internal server error: {str(e)}",
            "original_errors": [],
            "fixes_applied": [],
            "status": "compile_error",
            "warnings": "",
            "warnings_list": [],
            "exitCode": -1,
            "signal": "",
            "message": f"Internal server error: {str(e)}"
        }
