"""
Java Auto-Fix Rules — Fixes common Java syntax errors.
"""
import re
from backend.autofix.rules import AutoFixRule
from backend.autofix.edit_distance import levenshtein_distance

JAVA_KEYWORDS = {
    "abstract", "assert", "boolean", "break", "byte", "case", "catch", "char",
    "class", "const", "continue", "default", "do", "double", "else", "enum",
    "extends", "final", "finally", "float", "for", "goto", "if", "implements",
    "import", "instanceof", "int", "interface", "long", "native", "new",
    "package", "private", "protected", "public", "return", "short", "static",
    "strictfp", "super", "switch", "synchronized", "this", "throw", "throws",
    "transient", "try", "void", "volatile", "while", "String", "System"
}

JAVA_COMMON_CLASSES = {
    "System", "String", "Integer", "Double", "Float", "Boolean",
    "ArrayList", "HashMap", "Scanner", "Math", "Arrays", "Collections"
}


class JavaMissingSemicolonRule(AutoFixRule):
    """Add missing semicolons in Java code."""
    def check_and_fix(self, code_lines, error_node):
        row = error_node['start_point'][0]
        if row >= len(code_lines):
            return None, None
        line = code_lines[row]
        stripped = line.strip()

        if (stripped.startswith('#') or stripped.startswith('//') or
                stripped.startswith('/*') or stripped.startswith('*') or
                stripped.endswith(';') or stripped.endswith('{') or
                stripped.endswith('}') or stripped.endswith(',') or
                stripped.endswith(':') or not stripped):
            return None, None

        if (stripped.endswith(')') or stripped[-1].isalnum() or
                stripped.endswith(']') or stripped.endswith('"')):
            new_line = line.rstrip() + ';\n'
            return new_line, "Added missing semicolon"
        return None, None


class JavaKeywordTypoRule(AutoFixRule):
    """Fix keyword typos using edit distance against Java keywords."""
    def check_and_fix(self, code_lines, error_node):
        row = error_node['start_point'][0]
        if row >= len(code_lines):
            return None, None

        error_text = error_node.get('text', '').strip()
        if not error_text or len(error_text) < 2:
            return None, None

        all_words = JAVA_KEYWORDS | JAVA_COMMON_CLASSES
        best_match = None
        min_dist = 3
        for kw in all_words:
            dist = levenshtein_distance(error_text, kw)
            if dist <= 2 and dist < min_dist:
                min_dist = dist
                best_match = kw

        if best_match and best_match != error_text:
            line = code_lines[row]
            new_line = line.replace(error_text, best_match, 1)
            if new_line != line:
                return new_line, f"Fixed typo: '{error_text}' → '{best_match}'"
        return None, None


class JavaUnbalancedBraceRule(AutoFixRule):
    """Fix unbalanced braces in Java code."""
    def check_and_fix(self, code_lines, error_node):
        all_code = '\n'.join(code_lines)
        open_curly = all_code.count('{')
        close_curly = all_code.count('}')

        if open_curly > close_curly:
            row = error_node['end_point'][0]
            if row >= len(code_lines) - 2:
                for _ in range(open_curly - close_curly):
                    code_lines.append('}\n')
                return code_lines[-1], f"Added {open_curly - close_curly} missing closing brace(s)"
        return None, None


class JavaMissingImportRule(AutoFixRule):
    """Add missing imports for common Java classes."""
    IMPORT_MAP = {
        'Scanner': 'import java.util.Scanner;',
        'ArrayList': 'import java.util.ArrayList;',
        'HashMap': 'import java.util.HashMap;',
        'Arrays': 'import java.util.Arrays;',
        'Collections': 'import java.util.Collections;',
        'List': 'import java.util.List;',
        'Map': 'import java.util.Map;',
    }

    def check_and_fix(self, code_lines, error_node):
        error_text = error_node.get('text', '') + error_node.get('message', '')
        for cls, imp in self.IMPORT_MAP.items():
            if cls in error_text:
                if not any(imp in line for line in code_lines):
                    # Insert after package declaration or at top
                    insert_pos = 0
                    for i, line in enumerate(code_lines):
                        if line.strip().startswith('package') or line.strip().startswith('import'):
                            insert_pos = i + 1
                    code_lines.insert(insert_pos, imp + '\n')
                    return imp + '\n', f"Added missing import: {imp}"
        return None, None
