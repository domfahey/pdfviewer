#!/usr/bin/env python3
"""
Test Marker Application Script

Automatically applies appropriate pytest markers to test files based on:
- File naming conventions
- Function naming patterns
- Import analysis
- Test content analysis

This script helps categorize tests for better organization and selective execution.

Author: Dominic Fahey
License: MIT
"""

import ast
import re
from pathlib import Path
from typing import Dict, List, Set, Tuple
import argparse
import sys


class TestMarkerAnalyzer:
    """Analyzes test files and suggests appropriate markers."""
    
    MARKER_RULES = {
        # File-based rules
        'unit': {
            'file_patterns': [r'test_.*\.py$', r'.*_test\.py$'],
            'path_patterns': [r'tests/unit/', r'unit/'],
            'exclude_patterns': [r'integration', r'e2e', r'api']
        },
        'integration': {
            'file_patterns': [r'test_.*integration.*\.py$', r'integration.*test.*\.py$'],
            'path_patterns': [r'tests/integration/', r'integration/'],
            'function_patterns': [r'test_.*_integration', r'integration_test_.*']
        },
        'api': {
            'file_patterns': [r'test_.*api.*\.py$', r'api.*test.*\.py$'],
            'path_patterns': [r'tests/.*api/', r'api/'],
            'function_patterns': [r'test_.*_api', r'api_test_.*'],
            'imports': ['fastapi', 'httpx', 'requests', 'aiohttp']
        },
        'e2e': {
            'file_patterns': [r'test_.*e2e.*\.py$', r'e2e.*test.*\.py$'],
            'path_patterns': [r'tests/e2e/', r'e2e/', r'end_to_end/'],
            'function_patterns': [r'test_.*_e2e', r'e2e_test_.*']
        },
        'slow': {
            'function_patterns': [r'test_.*_slow', r'slow_test_.*', r'test_.*_performance'],
            'decorators': ['pytest.mark.slow', 'slow'],
            'keywords': ['sleep', 'time.sleep', 'await asyncio.sleep']
        },
        'fast': {
            'function_patterns': [r'test_.*_fast', r'fast_test_.*'],
            'exclude_keywords': ['sleep', 'time.sleep', 'requests.get', 'httpx']
        },
        'performance': {
            'function_patterns': [r'test_.*_performance', r'performance_test_.*', r'benchmark_.*'],
            'imports': ['pytest-benchmark', 'timeit', 'memory_profiler'],
            'decorators': ['pytest.mark.benchmark']
        },
        'pdf': {
            'function_patterns': [r'test_.*pdf.*', r'pdf.*test.*'],
            'imports': ['pypdf', 'PyPDF2', 'pdfplumber', 'fitz'],
            'keywords': ['pdf', 'document', 'page']
        },
        'upload': {
            'function_patterns': [r'test_.*upload.*', r'upload.*test.*'],
            'keywords': ['upload', 'file', 'multipart'],
            'imports': ['aiofiles', 'tempfile']
        },
        'search': {
            'function_patterns': [r'test_.*search.*', r'search.*test.*'],
            'keywords': ['search', 'query', 'find', 'filter']
        },
        'mock': {
            'imports': ['unittest.mock', 'pytest-mock', 'mock'],
            'keywords': ['mock', 'patch', 'MagicMock', 'Mock']
        },
        'async': {
            'function_patterns': [r'async def test_.*', r'test_.*_async'],
            'keywords': ['async def', 'await', 'asyncio'],
            'imports': ['asyncio', 'aiohttp', 'aiofiles']
        },
        'db': {
            'imports': ['sqlalchemy', 'databases', 'asyncpg', 'psycopg2'],
            'keywords': ['database', 'db', 'sql', 'query'],
            'function_patterns': [r'test_.*_db', r'db_test_.*']
        }
    }
    
    def __init__(self, test_directory: Path):
        self.test_directory = test_directory
        self.marker_suggestions = {}
    
    def analyze_file(self, file_path: Path) -> Dict[str, List[str]]:
        """Analyze a single test file and suggest markers."""
        suggestions = {
            'definite': [],    # High confidence markers
            'probable': [],    # Medium confidence markers
            'possible': []     # Low confidence markers
        }
        
        # Read file content
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            print(f"Error reading {file_path}: {e}")
            return suggestions
        
        # Parse AST for detailed analysis
        try:
            tree = ast.parse(content)
            imports = self.extract_imports(tree)
            functions = self.extract_test_functions(tree)
        except SyntaxError as e:
            print(f"Syntax error in {file_path}: {e}")
            return suggestions
        
        # Apply marker rules
        for marker, rules in self.MARKER_RULES.items():
            confidence = self.evaluate_marker_confidence(
                file_path, content, imports, functions, rules
            )
            
            if confidence >= 0.8:
                suggestions['definite'].append(marker)
            elif confidence >= 0.5:
                suggestions['probable'].append(marker)
            elif confidence >= 0.2:
                suggestions['possible'].append(marker)
        
        return suggestions
    
    def extract_imports(self, tree: ast.AST) -> Set[str]:
        """Extract all import statements from AST."""
        imports = set()
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.add(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.add(node.module)
                    for alias in node.names:
                        imports.add(f"{node.module}.{alias.name}")
        
        return imports
    
    def extract_test_functions(self, tree: ast.AST) -> List[Dict]:
        """Extract test function information from AST."""
        functions = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name.startswith('test_'):
                func_info = {
                    'name': node.name,
                    'is_async': isinstance(node, ast.AsyncFunctionDef),
                    'decorators': [self.get_decorator_name(d) for d in node.decorator_list],
                    'docstring': ast.get_docstring(node) or ''
                }
                functions.append(func_info)
        
        return functions
    
    def get_decorator_name(self, decorator) -> str:
        """Extract decorator name from AST node."""
        if isinstance(decorator, ast.Name):
            return decorator.id
        elif isinstance(decorator, ast.Attribute):
            return f"{decorator.value.id}.{decorator.attr}" if hasattr(decorator.value, 'id') else decorator.attr
        return str(decorator)
    
    def evaluate_marker_confidence(
        self, 
        file_path: Path, 
        content: str, 
        imports: Set[str], 
        functions: List[Dict], 
        rules: Dict
    ) -> float:
        """Evaluate confidence level for a specific marker based on rules."""
        confidence = 0.0
        total_weight = 0.0
        
        # File pattern matching
        if 'file_patterns' in rules:
            weight = 0.3
            total_weight += weight
            for pattern in rules['file_patterns']:
                if re.search(pattern, file_path.name, re.IGNORECASE):
                    confidence += weight
                    break
        
        # Path pattern matching
        if 'path_patterns' in rules:
            weight = 0.4
            total_weight += weight
            path_str = str(file_path)
            for pattern in rules['path_patterns']:
                if re.search(pattern, path_str, re.IGNORECASE):
                    confidence += weight
                    break
        
        # Exclude patterns (negative confidence)
        if 'exclude_patterns' in rules:
            path_str = str(file_path)
            for pattern in rules['exclude_patterns']:
                if re.search(pattern, path_str, re.IGNORECASE):
                    confidence -= 0.5
        
        # Function pattern matching
        if 'function_patterns' in rules:
            weight = 0.2
            total_weight += weight
            for func in functions:
                for pattern in rules['function_patterns']:
                    if re.search(pattern, func['name'], re.IGNORECASE):
                        confidence += weight
                        break
        
        # Import matching
        if 'imports' in rules:
            weight = 0.3
            total_weight += weight
            for import_rule in rules['imports']:
                for imp in imports:
                    if import_rule.lower() in imp.lower():
                        confidence += weight
                        break
        
        # Keyword matching in content
        if 'keywords' in rules:
            weight = 0.2
            total_weight += weight
            content_lower = content.lower()
            for keyword in rules['keywords']:
                if keyword.lower() in content_lower:
                    confidence += weight / len(rules['keywords'])
        
        # Exclude keywords (negative confidence)
        if 'exclude_keywords' in rules:
            content_lower = content.lower()
            for keyword in rules['exclude_keywords']:
                if keyword.lower() in content_lower:
                    confidence -= 0.3
        
        # Decorator matching
        if 'decorators' in rules:
            weight = 0.4
            total_weight += weight
            for func in functions:
                for decorator_rule in rules['decorators']:
                    for decorator in func['decorators']:
                        if decorator_rule.lower() in decorator.lower():
                            confidence += weight
                            break
        
        # Normalize confidence
        return confidence / max(total_weight, 1.0) if total_weight > 0 else 0.0
    
    def generate_marker_suggestions(self) -> Dict[Path, Dict]:
        """Generate marker suggestions for all test files."""
        suggestions = {}
        
        # Find all test files
        test_files = list(self.test_directory.rglob("test_*.py"))
        test_files.extend(list(self.test_directory.rglob("*_test.py")))
        
        for test_file in test_files:
            file_suggestions = self.analyze_file(test_file)
            if any(file_suggestions.values()):
                suggestions[test_file] = file_suggestions
        
        return suggestions
    
    def apply_markers_to_file(self, file_path: Path, markers: List[str], dry_run: bool = True) -> bool:
        """Apply markers to a test file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            print(f"Error reading {file_path}: {e}")
            return False
        
        # Check if file already has markers
        if 'pytest.mark.' in content:
            print(f"  {file_path.name} already has markers, skipping...")
            return False
        
        # Parse the file to find test functions
        try:
            tree = ast.parse(content)
        except SyntaxError as e:
            print(f"  Syntax error in {file_path}: {e}")
            return False
        
        # Generate marker imports
        marker_imports = self.generate_marker_imports(markers)
        
        # Find insertion points and apply markers
        lines = content.split('\\n')
        modified_lines = []
        
        # Add imports after existing imports
        import_added = False
        for i, line in enumerate(lines):
            modified_lines.append(line)
            
            # Add marker imports after the last import
            if not import_added and (line.startswith('import ') or line.startswith('from ')) and \\
               (i == len(lines) - 1 or not (lines[i + 1].startswith('import ') or lines[i + 1].startswith('from '))):
                if marker_imports:
                    modified_lines.extend(['', marker_imports, ''])
                import_added = True
        
        if not import_added and marker_imports:
            modified_lines.insert(0, marker_imports)
            modified_lines.insert(1, '')
        
        # Apply markers to test functions
        final_lines = []
        i = 0
        while i < len(modified_lines):
            line = modified_lines[i]
            
            # Check if this is a test function definition
            if re.match(r'^(async )?def test_', line.strip()):
                # Add markers before the function
                for marker in markers:
                    final_lines.append(f"@pytest.mark.{marker}")
                
            final_lines.append(line)
            i += 1
        
        # Write the modified content
        if not dry_run:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write('\\n'.join(final_lines))
                print(f"  ✅ Applied markers to {file_path.name}")
                return True
            except Exception as e:
                print(f"  ❌ Error writing to {file_path}: {e}")
                return False
        else:
            print(f"  📋 Would apply markers {markers} to {file_path.name}")
            return True
    
    def generate_marker_imports(self, markers: List[str]) -> str:
        """Generate the import statement for pytest markers."""
        if not markers:
            return ""
        return "import pytest"
    
    def run_analysis(self, apply_markers: bool = False, dry_run: bool = True, 
                     confidence_threshold: str = 'probable') -> None:
        """Run the complete marker analysis and application process."""
        print(f"Analyzing test files in: {self.test_directory}")
        print(f"Confidence threshold: {confidence_threshold}")
        print()
        
        suggestions = self.generate_marker_suggestions()
        
        if not suggestions:
            print("No test files found or no marker suggestions generated.")
            return
        
        # Display suggestions
        for file_path, file_suggestions in suggestions.items():
            rel_path = file_path.relative_to(self.test_directory)
            print(f"📁 {rel_path}")
            
            markers_to_apply = []
            
            if file_suggestions['definite']:
                print(f"  ✅ Definite: {', '.join(file_suggestions['definite'])}")
                markers_to_apply.extend(file_suggestions['definite'])
            
            if file_suggestions['probable'] and confidence_threshold in ['probable', 'possible']:
                print(f"  🔶 Probable: {', '.join(file_suggestions['probable'])}")
                if confidence_threshold in ['probable', 'possible']:
                    markers_to_apply.extend(file_suggestions['probable'])
            
            if file_suggestions['possible'] and confidence_threshold == 'possible':
                print(f"  ❓ Possible: {', '.join(file_suggestions['possible'])}")
                if confidence_threshold == 'possible':
                    markers_to_apply.extend(file_suggestions['possible'])
            
            # Apply markers if requested
            if apply_markers and markers_to_apply:
                self.apply_markers_to_file(file_path, list(set(markers_to_apply)), dry_run)
            
            print()


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Analyze test files and suggest/apply pytest markers"
    )
    parser.add_argument(
        "test_directory", 
        type=Path, 
        help="Directory containing test files"
    )
    parser.add_argument(
        "--apply", 
        action="store_true", 
        help="Apply suggested markers to files"
    )
    parser.add_argument(
        "--no-dry-run", 
        action="store_true", 
        help="Actually modify files (use with --apply)"
    )
    parser.add_argument(
        "--confidence", 
        choices=['definite', 'probable', 'possible'],
        default='probable',
        help="Minimum confidence level for marker application"
    )
    
    args = parser.parse_args()
    
    if not args.test_directory.exists():
        print(f"Error: Test directory {args.test_directory} does not exist")
        sys.exit(1)
    
    analyzer = TestMarkerAnalyzer(args.test_directory)
    analyzer.run_analysis(
        apply_markers=args.apply,
        dry_run=not args.no_dry_run,
        confidence_threshold=args.confidence
    )


if __name__ == "__main__":
    main()