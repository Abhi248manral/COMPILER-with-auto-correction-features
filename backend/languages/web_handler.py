"""
HTML/CSS Handler — Validates syntax, returns validation report.
No compilation or execution — purely validation-based.
"""
import re
from .base import LanguageHandler


class HTMLHandler(LanguageHandler):
    async def execute(self, code: str) -> dict:
        errors = self._validate_html(code)
        if errors:
            return {
                "stdout": "",
                "stderr": "HTML Validation Issues:\n" + "\n".join(f"  • {e}" for e in errors),
                "success": False,
                "language": "html",
                "preview": code  # Still return code for preview even with warnings
            }
        return {
            "stdout": "✅ HTML is valid! No issues detected.",
            "stderr": "",
            "success": True,
            "language": "html",
            "preview": code
        }

    def _validate_html(self, code: str) -> list:
        errors = []
        # Check for unclosed tags
        open_tags = re.findall(r'<(\w+)[^/]*?>', code)
        close_tags = re.findall(r'</(\w+)>', code)
        void_elements = {'br', 'hr', 'img', 'input', 'meta', 'link', 'area', 'base', 'col', 'embed', 'source', 'track', 'wbr'}

        tag_stack = []
        for tag in open_tags:
            tag_lower = tag.lower()
            if tag_lower not in void_elements:
                tag_stack.append(tag_lower)

        for tag in close_tags:
            tag_lower = tag.lower()
            if tag_lower in tag_stack:
                tag_stack.remove(tag_lower)

        for tag in tag_stack:
            errors.append(f"Unclosed <{tag}> tag")

        # Check for missing quotes in attributes
        unquoted = re.findall(r'(\w+)=([^\s"\'>][^\s>]*)', code)
        for attr, val in unquoted:
            if not val.startswith('"') and not val.startswith("'"):
                errors.append(f'Attribute "{attr}" value should be quoted')

        # Check for missing doctype
        if code.strip() and '<!DOCTYPE' not in code.upper() and '<html' in code.lower():
            errors.append("Missing <!DOCTYPE html> declaration")

        return errors

    def get_language_name(self):
        return "html"


class CSSHandler(LanguageHandler):
    async def execute(self, code: str) -> dict:
        errors = self._validate_css(code)
        if errors:
            return {
                "stdout": "",
                "stderr": "CSS Validation Issues:\n" + "\n".join(f"  • {e}" for e in errors),
                "success": False,
                "language": "css",
                "preview": f"<style>{code}</style><p>Preview with applied styles</p>"
            }
        return {
            "stdout": "✅ CSS is valid! No issues detected.",
            "stderr": "",
            "success": True,
            "language": "css",
            "preview": f"<style>{code}</style><p>Preview with applied styles</p>"
        }

    def _validate_css(self, code: str) -> list:
        errors = []

        # Check balanced braces
        if code.count('{') != code.count('}'):
            diff = code.count('{') - code.count('}')
            if diff > 0:
                errors.append(f"Missing {diff} closing brace(s) '}}' ")
            else:
                errors.append(f"Extra {-diff} closing brace(s) '}}' ")

        # Check for missing semicolons in property declarations
        lines = code.split('\n')
        for i, line in enumerate(lines):
            stripped = line.strip()
            if ':' in stripped and not stripped.endswith('{') and not stripped.endswith('}') and not stripped.startswith('/*') and not stripped.startswith('//'):
                if not stripped.endswith(';') and not stripped.endswith(','):
                    errors.append(f"Line {i+1}: Missing semicolon after property declaration")

        # Check for common property typos
        common_props = {
            'colr': 'color', 'backgroud': 'background', 'widht': 'width',
            'heigth': 'height', 'margn': 'margin', 'paddig': 'padding',
            'fonr-size': 'font-size', 'dispaly': 'display', 'positon': 'position'
        }
        for typo, correct in common_props.items():
            if typo in code.lower():
                errors.append(f'Possible typo: "{typo}" → did you mean "{correct}"?')

        return errors

    def get_language_name(self):
        return "css"
