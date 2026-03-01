import re
from .edit_distance import levenshtein_distance

C_KEYWORDS = {
    "auto", "break", "case", "char", "const", "continue", "default", "do",
    "double", "else", "enum", "extern", "float", "for", "goto", "if",
    "int", "long", "register", "return", "short", "signed", "sizeof", "static",
    "struct", "switch", "typedef", "union", "unsigned", "void", "volatile", "while"
}

COMMON_FUNCTIONS = {
    "printf", "scanf", "malloc", "free", "strlen", "strcpy", "strcmp",
    "main", "exit", "fopen", "fclose", "fprintf", "fscanf"
}

class AutoFixRule:
    def check_and_fix(self, code_lines, error_node):
        """
        Returns (fixed_line_content, fix_description) or (None, None)
        """
        raise NotImplementedError

class MissingSemicolonRule(AutoFixRule):
    def check_and_fix(self, code_lines, error_node):
        row, col = error_node['end_point']
        if row >= len(code_lines):
            return None, None
            
        line = code_lines[row]
        stripped = line.strip()
        
        # Don't add semicolons to preprocessor directives, braces, or already-terminated lines
        if (stripped.startswith('#') or stripped.endswith(';') or 
            stripped.endswith('{') or stripped.endswith('}') or 
            stripped.endswith(',')  or not stripped):
            return None, None
        
        # Add semicolon if line looks like a statement
        if (stripped.endswith(')') or stripped[-1].isalnum() or 
            stripped.endswith(']') or stripped.endswith('"')):
            new_line = line.rstrip() + ';\n'
            return new_line, "Added missing semicolon"
                
        return None, None

class KeywordTypoRule(AutoFixRule):
    def check_and_fix(self, code_lines, error_node):
        row, col = error_node['start_point']
        error_text = error_node['text'].strip()
        
        if not error_text or len(error_text) < 2:
            return None, None

        # Check against C keywords
        best_match = None
        min_dist = 3
        
        for kw in C_KEYWORDS:
            dist = levenshtein_distance(error_text, kw)
            if dist <= 2 and dist < min_dist:
                min_dist = dist
                best_match = kw
                
        if best_match and best_match != error_text:
            line = code_lines[row]
            start_col = error_node['start_point'][1]
            end_col = error_node['end_point'][1]
            
            segment = line[start_col:end_col]
            if segment.strip() == error_text:
                new_line = line[:start_col] + best_match + line[end_col:]
                return new_line, f"Fixed typo: '{error_text}' -> '{best_match}'"
        
        return None, None

class UnbalancedBracketRule(AutoFixRule):
    def check_and_fix(self, code_lines, error_node):
        # Count all brackets in the code
        all_code = '\n'.join(code_lines)
        
        open_curly = all_code.count('{')
        close_curly = all_code.count('}')
        open_paren = all_code.count('(')
        close_paren = all_code.count(')')
        open_square = all_code.count('[')
        close_square = all_code.count(']')
        
        # If we're missing closing brackets, try to add them at the end
        row = error_node['end_point'][0]
        
        if row >= len(code_lines) - 2:  # Near end of file
            fix_applied = False
            fixes = []
            
            if open_curly > close_curly:
                # Add missing closing braces
                for i in range(open_curly - close_curly):
                    code_lines.append('}\n')
                    fixes.append('}')
                fix_applied = True
                
            if open_paren > close_paren:
                line = code_lines[row]
                new_line = line.rstrip() + ')' * (open_paren - close_paren) + '\n'
                code_lines[row] = new_line
                fixes.append(')' * (open_paren - close_paren))
                fix_applied = True
                
            if fix_applied:
                return code_lines[row] if row < len(code_lines) else None, f"Added missing brackets: {' '.join(fixes)}"
        
        return None, None

class UnclosedStringRule(AutoFixRule):
    def check_and_fix(self, code_lines, error_node):
        row, col = error_node['start_point']
        if row >= len(code_lines):
            return None, None
            
        line = code_lines[row]
        
        # Count quotes (ignoring escaped quotes)
        clean_line = re.sub(r'\\"', '', line)
        
        if clean_line.count('"') % 2 != 0:
            new_line = line.rstrip() + '"\n'
            return new_line, "Closed unclosed string literal"
            
        if clean_line.count("'") % 2 != 0 and '"' not in clean_line:
            new_line = line.rstrip() + "'\n"
            return new_line, "Closed unclosed character literal"
              
        return None, None

class MissingIncludeRule(AutoFixRule):
    """Detects undefined functions and adds appropriate #include"""
    
    INCLUDE_MAP = {
        'printf': '#include <stdio.h>',
        'scanf': '#include <stdio.h>',
        'malloc': '#include <stdlib.h>',
        'free': '#include <stdlib.h>',
        'strlen': '#include <string.h>',
        'strcpy': '#include <string.h>',
        'strcmp': '#include <string.h>',
    }
    
    def check_and_fix(self, code_lines, error_node):
        # Check if error text contains an undefined function name
        error_text = error_node.get('text', '').strip()
        
        for func, include in self.INCLUDE_MAP.items():
            if func in error_text:
                # Check if include already exists
                has_include = any(include in line for line in code_lines)
                
                if not has_include:
                    # Find first non-empty line to insert after
                    insert_pos = 0
                    for i, line in enumerate(code_lines):
                        if line.strip().startswith('#include'):
                            insert_pos = i + 1
                    
                    code_lines.insert(insert_pos, include + '\n')
                    return include + '\n', f"Added missing include for {func}"
        
        return None, None

class MissingReturnTypeRule(AutoFixRule):
    """Fixes functions missing return type (assumes int)"""
    
    def check_and_fix(self, code_lines, error_node):
        row = error_node['start_point'][0]
        if row >= len(code_lines):
            return None, None
            
        line = code_lines[row]
        
        # Check if line looks like function definition without return type
        # Pattern: functionName(...) {
        if re.match(r'^\s*\w+\s*\([^)]*\)\s*\{', line):
            # Check if it's missing a type
            if not any(kw in line for kw in ['int', 'void', 'float', 'double', 'char']):
                new_line = 'int ' + line.lstrip()
                return new_line, "Added missing return type (int)"
        
        return None, None
