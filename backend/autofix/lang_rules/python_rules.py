"""
Python Auto-Fix Rules — Fixes common Python syntax errors.
"""
import re
from backend.autofix.rules import AutoFixRule
from backend.autofix.edit_distance import levenshtein_distance

PYTHON_KEYWORDS = {
    "False", "None", "True", "and", "as", "assert", "async", "await",
    "break", "class", "continue", "def", "del", "elif", "else", "except",
    "finally", "for", "from", "global", "if", "import", "in", "is",
    "lambda", "nonlocal", "not", "or", "pass", "raise", "return", "try",
    "while", "with", "yield", "print", "range", "len", "int", "str",
    "float", "list", "dict", "set", "tuple", "input", "type", "open"
}


class PythonMissingColonRule(AutoFixRule):
    """Add missing colon after if/for/while/def/class/elif/else/try/except/finally."""
    COLON_KEYWORDS = ['if', 'for', 'while', 'def', 'class', 'elif', 'else', 'try', 'except', 'finally', 'with']

    def check_and_fix(self, code_lines, error_node):
        row = error_node.get('line', error_node['start_point'][0] + 1) - 1
        if row >= len(code_lines):
            return None, None
        line = code_lines[row]
        stripped = line.rstrip()

        for kw in self.COLON_KEYWORDS:
            pattern = rf'^\s*{kw}\b'
            if re.match(pattern, stripped) and not stripped.endswith(':') and not stripped.endswith('\\'):
                new_line = stripped + ':\n'
                return new_line, f"Added missing colon after '{kw}'"
        return None, None


class PythonKeywordTypoRule(AutoFixRule):
    """Fix keyword typos using edit distance against Python keywords."""
    def check_and_fix(self, code_lines, error_node):
        row = error_node['start_point'][0]
        if row >= len(code_lines):
            return None, None

        error_text = error_node.get('text', '').strip()
        if not error_text or len(error_text) < 2:
            return None, None

        best_match = None
        min_dist = 3
        for kw in PYTHON_KEYWORDS:
            dist = levenshtein_distance(error_text.lower(), kw.lower())
            if dist <= 2 and dist < min_dist:
                min_dist = dist
                best_match = kw

        if best_match and best_match != error_text:
            line = code_lines[row]
            new_line = line.replace(error_text, best_match, 1)
            if new_line != line:
                return new_line, f"Fixed typo: '{error_text}' → '{best_match}'"
        return None, None


class PythonIndentationRule(AutoFixRule):
    """Fix mixed tabs/spaces — normalize to 4 spaces."""
    def check_and_fix(self, code_lines, error_node):
        row = error_node['start_point'][0]
        if row >= len(code_lines):
            return None, None
        line = code_lines[row]
        if '\t' in line:
            new_line = line.replace('\t', '    ')
            return new_line, "Replaced tabs with 4 spaces"
        return None, None


class PythonUnbalancedParenRule(AutoFixRule):
    """Fix unbalanced parentheses in Python code."""
    def check_and_fix(self, code_lines, error_node):
        row = error_node['start_point'][0]
        if row >= len(code_lines):
            return None, None
        line = code_lines[row]
        open_p = line.count('(')
        close_p = line.count(')')
        if open_p > close_p:
            new_line = line.rstrip() + ')' * (open_p - close_p) + '\n'
            return new_line, f"Added {open_p - close_p} missing closing parenthesis"
        return None, None
