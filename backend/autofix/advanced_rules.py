"""
Advanced Auto-Fix Rules - Fixes for compile-time, runtime, and logic errors
"""
import re
from backend.autofix.rules import AutoFixRule

class TypeMismatchRule(AutoFixRule):
    """Fix type mismatches like int x = "hello" """
    def check_and_fix(self, code_lines, error_node):
        row = error_node['start_point'][0]
        if row >= len(code_lines): return None, None
        
        line = code_lines[row]
        if re.search(r'\bint\s+\w+\s*=\s*"', line):
            new_line = re.sub(r'\bint(\s+\w+\s*=\s*)"', r'char*\1"', line)
            if new_line != line:
                return new_line, "Fixed type mismatch: int -> char*"
        return None, None

class DivideByZeroRule(AutoFixRule):
    """Fix division by zero"""
    def check_and_fix(self, code_lines, error_node):
        row = error_node.get('line', error_node['start_point'][0]) - 1 if 'line' in error_node else error_node['start_point'][0]
        if row >= len(code_lines): return None, None
        
        line = code_lines[row]
        if re.search(r'[/%]\s*0\b', line):
            new_line = re.sub(r'/\s*0\b', '/ 1', line)
            new_line = re.sub(r'%\s*0\b', '% 1', new_line)
            return new_line, "Fixed divide by zero"
        return None, None

class NullCheckRule(AutoFixRule):
    """Add NULL checks for pointers - SAFE VERSION"""
    def check_and_fix(self, code_lines, error_node):
        row = error_node.get('line', error_node['start_point'][0]) - 1 if 'line' in error_node else error_node['start_point'][0]
        if row >= len(code_lines): return None, None
        
        line = code_lines[row]
        
        # SAFETY CHECK: Only apply if line is indented (inside function)
        if not line.startswith(' ') and not line.startswith('\t'):
            return None, None
            
        # Find pointer usage
        ptr_match = re.search(r'(\w+)\s*->', line)
        if not ptr_match: ptr_match = re.search(r'\*(\w+)', line)
        
        if ptr_match:
            ptr_name = ptr_match.group(1)
            indent = len(line) - len(line.lstrip())
            indent_str = line[:indent]
            
            # Check if we already have a check
            if row > 0 and f'if ({ptr_name}' in code_lines[row-1]:
                return None, None
            
            null_check = f'{indent_str}if ({ptr_name} == NULL) return 1; // Auto-check\n'
            
            # Add include if missing using simple check
            add_include = False
            if not any('#include <stdlib.h>' in l for l in code_lines) and \
               not any('#include <stddef.h>' in l for l in code_lines) and \
               not any('#include <stdio.h>' in l for l in code_lines):
                 add_include = True
            
            if add_include:
                code_lines.insert(0, '#include <stdlib.h>\n')
                code_lines.insert(row + 1, null_check) # Adjusted row
            else:
                code_lines.insert(row, null_check)

            return null_check, f"Added NULL check for '{ptr_name}'"
        return None, None

class ArrayBoundsRule(AutoFixRule):
    def check_and_fix(self, code_lines, error_node):
        return None, None

class UninitializedVarRule(AutoFixRule):
    """Initialize uninitialized variables - SAFE VERSION"""
    def check_and_fix(self, code_lines, error_node):
        row = error_node.get('line', error_node['start_point'][0]) - 1 if 'line' in error_node else error_node['start_point'][0]
        if row >= len(code_lines): return None, None
        
        line = code_lines[row]
        
        # Only fix declarations
        match = re.search(r'\b(int|float|double|char)\s+(\w+)\s*;', line)
        if match:
            var_type, var_name = match.groups()
            val = '0'
            if var_type == 'float': val = '0.0'
            if var_type == 'char': val = "'\\0'"
            
            new_line = re.sub(r'(\w+)\s*;', rf'\1 = {val};', line)
            return new_line, f"Initialized '{var_name}'"
        return None, None

class MissingReturnRule(AutoFixRule):
    """Add missing return statement - DISABLED FOR STABILITY"""
    def check_and_fix(self, code_lines, error_node):
        return None, None

class BufferOverflowRule(AutoFixRule):
    def check_and_fix(self, code_lines, error_node):
        return None, None # Disable for safety

class UndefinedFunctionRule(AutoFixRule):
    FUNCTION_INCLUDES = {
        'printf': '#include <stdio.h>',
        'scanf': '#include <stdio.h>',
        'malloc': '#include <stdlib.h>',
        'free': '#include <stdlib.h>',
        'strlen': '#include <string.h>',
        'strcpy': '#include <string.h>',
        'NULL': '#include <stdlib.h>',
    }
    
    def check_and_fix(self, code_lines, error_node):
        msg = error_node.get('message', '') + error_node.get('text', '')
        
        target = None
        for func in self.FUNCTION_INCLUDES:
            if func in msg:
                target = func
                break
        
        if target:
            inc = self.FUNCTION_INCLUDES[target]
            if not any(inc in line for line in code_lines):
                code_lines.insert(0, inc + '\n')
                return inc, f"Added {inc}"
        return None, None
