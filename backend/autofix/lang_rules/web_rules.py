"""
HTML/CSS Auto-Fix Rules — Validates and fixes common web markup errors.
"""
import re
from backend.autofix.rules import AutoFixRule


class HTMLUnclosedTagRule(AutoFixRule):
    """Fix unclosed HTML tags by appending closing tags."""
    VOID_ELEMENTS = {'br', 'hr', 'img', 'input', 'meta', 'link', 'area',
                     'base', 'col', 'embed', 'source', 'track', 'wbr'}

    def check_and_fix(self, code_lines, error_node):
        all_code = '\n'.join(code_lines)
        open_tags = re.findall(r'<(\w+)[^/]*?>', all_code)
        close_tags = re.findall(r'</(\w+)>', all_code)

        tag_stack = []
        for tag in open_tags:
            if tag.lower() not in self.VOID_ELEMENTS:
                tag_stack.append(tag.lower())
        for tag in close_tags:
            if tag.lower() in tag_stack:
                tag_stack.remove(tag.lower())

        if tag_stack:
            # Add closing tags in reverse order
            added = []
            for tag in reversed(tag_stack):
                code_lines.append(f'</{tag}>\n')
                added.append(f'</{tag}>')
            return code_lines[-1], f"Added missing closing tag(s): {', '.join(added)}"
        return None, None


class HTMLMissingAttributeQuotesRule(AutoFixRule):
    """Add quotes around unquoted HTML attribute values."""
    def check_and_fix(self, code_lines, error_node):
        row = error_node['start_point'][0]
        if row >= len(code_lines):
            return None, None
        line = code_lines[row]
        # Match attr=value without quotes (but not already quoted)
        new_line = re.sub(r'(\w+)=([^\s"\'>][^\s>]*)', r'\1="\2"', line)
        if new_line != line:
            return new_line, "Added quotes around unquoted attribute values"
        return None, None


class CSSMissingSemicolonRule(AutoFixRule):
    """Fix missing semicolons in CSS property declarations."""
    def check_and_fix(self, code_lines, error_node):
        row = error_node['start_point'][0]
        if row >= len(code_lines):
            return None, None
        line = code_lines[row]
        stripped = line.strip()
        if (':' in stripped and
                not stripped.endswith(';') and
                not stripped.endswith('{') and
                not stripped.endswith('}') and
                not stripped.startswith('/*') and
                not stripped.startswith('//')):
            new_line = line.rstrip() + ';\n'
            return new_line, "Added missing semicolon in CSS declaration"
        return None, None


class CSSUnbalancedBraceRule(AutoFixRule):
    """Fix unbalanced braces in CSS."""
    def check_and_fix(self, code_lines, error_node):
        all_code = '\n'.join(code_lines)
        open_b = all_code.count('{')
        close_b = all_code.count('}')
        if open_b > close_b:
            for _ in range(open_b - close_b):
                code_lines.append('}\n')
            return code_lines[-1], f"Added {open_b - close_b} missing closing brace(s)"
        return None, None
