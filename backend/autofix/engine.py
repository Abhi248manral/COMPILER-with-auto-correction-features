"""
AutoFix Engine — Language-aware fix routing.
Loads the appropriate rule set based on the target language.

REFACTORED: Now supports C, C++, Python, Java, HTML, CSS via get_fix_engine(language).
"""
from .rules import (
    MissingSemicolonRule, KeywordTypoRule, UnclosedStringRule,
    UnbalancedBracketRule, MissingIncludeRule, MissingReturnTypeRule
)
from .advanced_rules import (
    TypeMismatchRule, DivideByZeroRule, NullCheckRule,
    UninitializedVarRule, MissingReturnRule, BufferOverflowRule,
    UndefinedFunctionRule
)


class AutoFixEngine:
    def __init__(self, rules=None):
        self.rules = rules or []

    def apply_fixes(self, code: str, errors: list):
        """
        Attempts to fix the code based on the provided errors.
        Returns: (fixed_code, applied_fixes_list)
        """
        if not errors:
            return code, []

        lines = code.split('\n')
        applied_fixes = []
        modified_lines = set()

        for err in errors:
            row = err['start_point'][0]
            if row in modified_lines:
                continue

            for rule in self.rules:
                try:
                    new_line, desc = rule.check_and_fix(lines, err)
                    if new_line is not None:
                        if row < len(lines):
                            lines[row] = new_line
                        modified_lines.add(row)
                        applied_fixes.append({
                            "line": row + 1,
                            "rule": rule.__class__.__name__,
                            "description": desc,
                            "before": code.split('\n')[row].strip() if row < len(code.split('\n')) else "",
                            "after": new_line.strip()
                        })
                        break
                except Exception:
                    continue

        fixed_code = '\n'.join(lines)
        return fixed_code, applied_fixes


def _build_c_rules():
    return [
        KeywordTypoRule(),
        MissingSemicolonRule(),
        UnclosedStringRule(),
        MissingIncludeRule(),
        TypeMismatchRule(),
        DivideByZeroRule(),
        NullCheckRule(),
        UninitializedVarRule(),
        BufferOverflowRule(),
        MissingReturnTypeRule(),
        MissingReturnRule(),
        UndefinedFunctionRule(),
        UnbalancedBracketRule()
    ]


def _build_cpp_rules():
    # C++ shares all C rules (GCC error format is similar)
    return _build_c_rules()


def _build_python_rules():
    from .lang_rules.python_rules import (
        PythonMissingColonRule, PythonKeywordTypoRule,
        PythonIndentationRule, PythonUnbalancedParenRule
    )
    return [
        PythonKeywordTypoRule(),
        PythonMissingColonRule(),
        PythonIndentationRule(),
        PythonUnbalancedParenRule()
    ]


def _build_java_rules():
    from .lang_rules.java_rules import (
        JavaMissingSemicolonRule, JavaKeywordTypoRule,
        JavaUnbalancedBraceRule, JavaMissingImportRule
    )
    return [
        JavaKeywordTypoRule(),
        JavaMissingSemicolonRule(),
        JavaUnbalancedBraceRule(),
        JavaMissingImportRule()
    ]


def _build_html_rules():
    from .lang_rules.web_rules import HTMLUnclosedTagRule, HTMLMissingAttributeQuotesRule
    return [
        HTMLUnclosedTagRule(),
        HTMLMissingAttributeQuotesRule()
    ]


def _build_css_rules():
    from .lang_rules.web_rules import CSSMissingSemicolonRule, CSSUnbalancedBraceRule
    return [
        CSSMissingSemicolonRule(),
        CSSUnbalancedBraceRule()
    ]


_RULE_BUILDERS = {
    "c": _build_c_rules,
    "cpp": _build_cpp_rules,
    "python": _build_python_rules,
    "java": _build_java_rules,
    "html": _build_html_rules,
    "css": _build_css_rules,
}


def get_fix_engine(language: str = "c") -> AutoFixEngine:
    """Factory: returns an AutoFixEngine configured for the given language."""
    builder = _RULE_BUILDERS.get(language, _build_c_rules)
    return AutoFixEngine(rules=builder())


# Backward compatibility
fix_engine = AutoFixEngine(rules=_build_c_rules())
