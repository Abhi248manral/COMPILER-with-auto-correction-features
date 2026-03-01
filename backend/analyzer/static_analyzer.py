"""
Static Analyzer - Detects runtime and logic errors through code analysis
"""
import re
from typing import List, Dict

class StaticAnalyzer:
    def __init__(self):
        self.warnings = []
    
    def analyze(self, code: str) -> List[Dict]:
        """Run all static analysis checks"""
        self.warnings = []
        lines = code.split('\n')
        
        # Run various checks
        self._check_divide_by_zero(lines)
        self._check_null_dereference(lines)
        self._check_array_bounds(lines, code)
        self._check_uninitialized_vars(lines)
        self._check_infinite_loops(lines)
        self._check_missing_return(lines, code)
        self._check_buffer_overflow(lines)
        
        return self.warnings
    
    def _check_divide_by_zero(self, lines):
        """Detect potential division by zero"""
        for i, line in enumerate(lines):
            # Check for /0 or %0
            if re.search(r'[/%]\s*0\s*[;)]', line):
                self.warnings.append({
                    'line': i + 1,
                    'type': 'divide_by_zero',
                    'severity': 'error',
                    'message': 'Division by zero detected',
                    'fixable': True
                })
    
    def _check_null_dereference(self, lines):
        """Detect potential null pointer dereference"""
        for i, line in enumerate(lines):
            # Check for pointer usage without null check
            # Pattern: *ptr or ptr-> without if check nearby
            if re.search(r'\*\w+\s*[=;]|\w+\s*->', line):
                # Check if there's a NULL check in previous 3 lines
                has_null_check = False
                for j in range(max(0, i-3), i):
                    if 'NULL' in lines[j] or '!=' in lines[j]:
                        has_null_check = True
                        break
                
                if not has_null_check and 'malloc' not in line:
                    self.warnings.append({
                        'line': i + 1,
                        'type': 'null_dereference',
                        'severity': 'warning',
                        'message': 'Potential null pointer dereference - add NULL check',
                        'fixable': True
                    })
    
    def _check_array_bounds(self, lines, code):
        """Detect array access out of bounds"""
        # Find array declarations
        array_pattern = r'(\w+)\s*\[\s*(\d+)\s*\]'
        arrays = {}
        
        for i, line in enumerate(lines):
            match = re.search(array_pattern, line)
            if match:
                arrays[match.group(1)] = int(match.group(2))
        
        # Check array access
        for i, line in enumerate(lines):
            for arr_name, arr_size in arrays.items():
                # Check for hardcoded index >= size
                access_pattern = rf'{arr_name}\s*\[\s*(\d+)\s*\]'
                match = re.search(access_pattern, line)
                if match:
                    index = int(match.group(1))
                    if index >= arr_size:
                        self.warnings.append({
                            'line': i + 1,
                            'type': 'array_out_of_bounds',
                            'severity': 'error',
                            'message': f'Array {arr_name}[{index}] out of bounds (size={arr_size})',
                            'fixable': False
                        })
    
    def _check_uninitialized_vars(self, lines):
        """Detect use of uninitialized variables"""
        declared_vars = set()
        initialized_vars = set()
        
        for i, line in enumerate(lines):
            # Find declarations
            decl_match = re.findall(r'\b(int|char|float|double)\s+(\w+)', line)
            for _, var_name in decl_match:
                declared_vars.add(var_name)
                # Check if initialized
                if '=' in line and var_name in line:
                    initialized_vars.add(var_name)
            
            # Check usage of uninitialized vars
            for var in declared_vars - initialized_vars:
                # Simple check: var used on right side of =
                if re.search(rf'=\s*.*\b{var}\b', line):
                    self.warnings.append({
                        'line': i + 1,
                        'type': 'uninitialized_variable',
                        'severity': 'warning',
                        'message': f'Variable "{var}" may be used uninitialized',
                        'fixable': True
                    })
    
    def _check_infinite_loops(self, lines):
        """Detect potential infinite loops"""
        for i, line in enumerate(lines):
            if re.search(r'while\s*\(\s*1\s*\)', line):
                # Check if there's a break in next 10 lines
                has_break = any('break' in lines[j] for j in range(i, min(i+10, len(lines))))
                if not has_break:
                    self.warnings.append({
                        'line': i + 1,
                        'type': 'infinite_loop',
                        'severity': 'warning',
                        'message': 'Potential infinite loop detected (while(1) without break)',
                        'fixable': False
                    })
    
    def _check_missing_return(self, lines, code):
        """Check if non-void functions always return"""
        # Find function definitions
        func_pattern = r'(int|float|double|char)\s+(\w+)\s*\([^)]*\)\s*\{'
        
        for i, line in enumerate(lines):
            match = re.search(func_pattern, line)
            if match and match.group(1) != 'void':
                func_name = match.group(2)
                # Find function end (simplified - just search for matching })
                # Check if there's a return statement
                func_lines = []
                brace_count = 0
                for j in range(i, len(lines)):
                    func_lines.append(lines[j])
                    brace_count += lines[j].count('{') - lines[j].count('}')
                    if brace_count == 0 and j > i:
                        break
                
                has_return = any('return' in fl for fl in func_lines)
                if not has_return:
                    self.warnings.append({
                        'line': i + 1,
                        'type': 'missing_return',
                        'severity': 'error',
                        'message': f'Function "{func_name}" does not return a value',
                        'fixable': True
                    })
    
    def _check_buffer_overflow(self, lines):
        """Detect potential buffer overflow from strcpy, gets, etc."""
        dangerous_functions = ['gets', 'strcpy', 'strcat', 'sprintf']
        
        for i, line in enumerate(lines):
            for func in dangerous_functions:
                if func in line:
                    self.warnings.append({
                        'line': i + 1,
                        'type': 'buffer_overflow',
                        'severity': 'warning',
                        'message': f'Unsafe function "{func}" may cause buffer overflow',
                        'fixable': True
                    })

static_analyzer = StaticAnalyzer()
