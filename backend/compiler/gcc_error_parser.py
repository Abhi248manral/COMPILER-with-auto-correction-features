"""
GCC Error Parser - Extracts and categorizes GCC compiler errors
and linker errors (undefined reference, etc.).
"""
import re
import logging

logger = logging.getLogger(__name__)

class GCCErrorParser:
    def __init__(self):
        self.error_patterns = {
            'type_mismatch': r"incompatible types|cannot convert|invalid conversion|makes integer from pointer|makes pointer from integer",
            'undefined_function': r"implicit declaration of function|undefined reference to",
            'undefined_variable': r"'(\w+)' undeclared",
            'missing_semicolon': r"expected ';'",
            'wrong_return': r"return with no value|return with a value",
            'array_bounds': r"array subscript|out of bounds",
        }
    
    def parse_gcc_output(self, gcc_output):
        """Parse GCC error messages and extract structured errors"""
        errors = []
        lines = gcc_output.split('\n')
        
        for line in lines:
            # Extract line number and error message
            # Format: file.c:10:5: error: message
            match = re.match(r'.*?:(\d+):(\d+):\s*(error|warning):\s*(.+)', line)
            if match:
                line_num = int(match.group(1))
                col_num = int(match.group(2))
                severity = match.group(3)
                message = match.group(4)
                
                # Categorize error
                error_type = self._categorize_error(message)
                
                errors.append({
                    'line': line_num,
                    'column': col_num,
                    'severity': severity,
                    'message': message,
                    'type': error_type
                })
        
        return errors
    
    def _categorize_error(self, message):
        """Categorize error based on message"""
        for error_type, pattern in self.error_patterns.items():
            if re.search(pattern, message, re.IGNORECASE):
                return error_type
        return 'unknown'

    def extract_warnings(self, gcc_output):
        """
        Extract only warning messages from GCC output.
        Returns a list of dicts: [{"line": int, "message": str, "type": str}]
        """
        all_items = self.parse_gcc_output(gcc_output)
        warnings = []
        for item in all_items:
            if item.get("severity") == "warning":
                warnings.append({
                    "line": item["line"],
                    "column": item.get("column", 0),
                    "message": item["message"],
                    "type": item["type"],
                })
        return warnings

    def format_warnings_text(self, gcc_output):
        """
        Build a human-readable warnings summary from GCC output.
        Returns empty string if no warnings.
        """
        warnings = self.extract_warnings(gcc_output)
        if not warnings:
            return ""
        parts = []
        for w in warnings:
            parts.append(f"Line {w['line']}: warning: {w['message']}")
        return "\n".join(parts)

    def parse_linker_output(self, stderr):
        """
        Parse linker error output and extract undefined symbol names.
        Returns a list of dicts with 'symbol' and 'message' keys.
        """
        results = []
        # Match: undefined reference to `funcName'
        for match in re.finditer(r"undefined reference to [`']([^`']+)['`]", stderr):
            symbol = match.group(1)
            results.append({
                "symbol": symbol,
                "message": f"Function '{symbol}' declared but not defined."
            })
            logger.info("Linker error: undefined reference to '%s'", symbol)

        # If we found no specific symbols but stderr looks like a linker error
        if not results and ("ld returned" in stderr or "collect2" in stderr):
            results.append({
                "symbol": "unknown",
                "message": "Linker error: unresolved symbols."
            })
            logger.info("Linker error detected (no specific symbol extracted)")

        return results

    def build_linker_message(self, stderr):
        """
        Build a user-friendly message from linker error stderr.
        Returns a concise string like:
          "Function 'undeclaredFunction' declared but not defined."
        """
        parsed = self.parse_linker_output(stderr)
        if parsed:
            return "; ".join(p["message"] for p in parsed)
        return "Linker error: unresolved symbols."

gcc_error_parser = GCCErrorParser()
