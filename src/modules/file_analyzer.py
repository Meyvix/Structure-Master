"""
Stracture-Master - File Analyzer Module
Analyzes files for various metrics and properties.
"""

import re
from pathlib import Path
from typing import Dict, Any, List, Optional, Set
from dataclasses import dataclass, field

from ..config import Config
from .logger import Logger


@dataclass
class FileAnalysis:
    """Analysis results for a file."""
    path: str
    lines_of_code: int = 0
    blank_lines: int = 0
    comment_lines: int = 0
    total_lines: int = 0
    complexity: int = 0
    language: str = ''
    todos: List[str] = field(default_factory=list)
    fixmes: List[str] = field(default_factory=list)
    imports: List[str] = field(default_factory=list)
    functions: List[str] = field(default_factory=list)
    classes: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'path': self.path,
            'lines_of_code': self.lines_of_code,
            'blank_lines': self.blank_lines,
            'comment_lines': self.comment_lines,
            'total_lines': self.total_lines,
            'complexity': self.complexity,
            'language': self.language,
            'todos': self.todos,
            'fixmes': self.fixmes,
            'imports_count': len(self.imports),
            'functions_count': len(self.functions),
            'classes_count': len(self.classes),
        }


class FileAnalyzer:
    """
    Analyzes code files for metrics.
    """
    
    # Language detection by extension
    LANGUAGE_MAP = {
        '.py': 'python',
        '.js': 'javascript',
        '.ts': 'typescript',
        '.jsx': 'javascript',
        '.tsx': 'typescript',
        '.java': 'java',
        '.c': 'c',
        '.cpp': 'cpp',
        '.h': 'c',
        '.hpp': 'cpp',
        '.cs': 'csharp',
        '.go': 'go',
        '.rs': 'rust',
        '.rb': 'ruby',
        '.php': 'php',
        '.swift': 'swift',
        '.kt': 'kotlin',
        '.scala': 'scala',
        '.html': 'html',
        '.css': 'css',
        '.scss': 'scss',
        '.vue': 'vue',
        '.sql': 'sql',
    }
    
    # Comment patterns by language
    COMMENT_PATTERNS = {
        'python': (r'#.*$', None, r'"""[\s\S]*?"""', r"'''[\s\S]*?'''"),
        'javascript': (r'//.*$', r'/\*[\s\S]*?\*/', None, None),
        'typescript': (r'//.*$', r'/\*[\s\S]*?\*/', None, None),
        'java': (r'//.*$', r'/\*[\s\S]*?\*/', None, None),
        'c': (r'//.*$', r'/\*[\s\S]*?\*/', None, None),
        'cpp': (r'//.*$', r'/\*[\s\S]*?\*/', None, None),
        'csharp': (r'//.*$', r'/\*[\s\S]*?\*/', None, None),
        'go': (r'//.*$', r'/\*[\s\S]*?\*/', None, None),
        'rust': (r'//.*$', r'/\*[\s\S]*?\*/', None, None),
        'ruby': (r'#.*$', r'=begin[\s\S]*?=end', None, None),
        'php': (r'//.*$|#.*$', r'/\*[\s\S]*?\*/', None, None),
        'html': (None, r'<!--[\s\S]*?-->', None, None),
        'css': (None, r'/\*[\s\S]*?\*/', None, None),
        'scss': (r'//.*$', r'/\*[\s\S]*?\*/', None, None),
        'sql': (r'--.*$', r'/\*[\s\S]*?\*/', None, None),
    }
    
    # Function/class patterns
    FUNCTION_PATTERNS = {
        'python': r'^\s*def\s+(\w+)',
        'javascript': r'(?:function\s+(\w+)|(\w+)\s*[=:]\s*(?:async\s+)?function|\bconst\s+(\w+)\s*=\s*(?:async\s+)?\()',
        'typescript': r'(?:function\s+(\w+)|(\w+)\s*[=:]\s*(?:async\s+)?function|\bconst\s+(\w+)\s*=\s*(?:async\s+)?\()',
        'java': r'(?:public|private|protected|static)*\s+(?:\w+\s+)?(\w+)\s*\(',
        'go': r'func\s+(?:\(\w+\s+\*?\w+\)\s+)?(\w+)',
        'rust': r'fn\s+(\w+)',
        'php': r'function\s+(\w+)',
        'ruby': r'def\s+(\w+)',
    }
    
    CLASS_PATTERNS = {
        'python': r'^\s*class\s+(\w+)',
        'javascript': r'class\s+(\w+)',
        'typescript': r'(?:class|interface)\s+(\w+)',
        'java': r'(?:class|interface|enum)\s+(\w+)',
        'csharp': r'(?:class|interface|struct)\s+(\w+)',
        'php': r'class\s+(\w+)',
        'ruby': r'class\s+(\w+)',
    }
    
    IMPORT_PATTERNS = {
        'python': r'(?:from\s+[\w.]+\s+)?import\s+[\w.,\s]+',
        'javascript': r'(?:import|require)\s*[({]?[\w\s,*{}]+[)}]?\s*(?:from)?\s*[\'"][\w./@-]+[\'"]',
        'typescript': r'(?:import|require)\s*[({]?[\w\s,*{}]+[)}]?\s*(?:from)?\s*[\'"][\w./@-]+[\'"]',
        'java': r'import\s+[\w.*]+;',
        'go': r'import\s+(?:\(\s*[\s\S]*?\)|"[\w/.-]+")',
        'rust': r'use\s+[\w:]+',
        'php': r'(?:use|require|include)(?:_once)?\s+[\w\\]+',
    }
    
    def __init__(self):
        """Initialize file analyzer."""
        self.logger = Logger.get_instance()
    
    def analyze_file(self, filepath: Path) -> FileAnalysis:
        """
        Analyze a single file.
        
        Args:
            filepath: Path to file
            
        Returns:
            FileAnalysis result
        """
        filepath = Path(filepath)
        analysis = FileAnalysis(path=str(filepath))
        
        if not filepath.exists() or not filepath.is_file():
            return analysis
        
        # Detect language
        ext = filepath.suffix.lower()
        analysis.language = self.LANGUAGE_MAP.get(ext, 'unknown')
        
        # Read content
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                lines = content.split('\n')
        except Exception:
            return analysis
        
        analysis.total_lines = len(lines)
        
        # Count lines
        for line in lines:
            stripped = line.strip()
            if not stripped:
                analysis.blank_lines += 1
            elif self._is_comment_line(stripped, analysis.language):
                analysis.comment_lines += 1
            else:
                analysis.lines_of_code += 1
        
        # Find TODOs and FIXMEs
        analysis.todos = re.findall(r'(?i)TODO[:\s]*(.*?)(?:\n|$)', content)
        analysis.fixmes = re.findall(r'(?i)FIXME[:\s]*(.*?)(?:\n|$)', content)
        
        # Find functions and classes
        if analysis.language in self.FUNCTION_PATTERNS:
            pattern = self.FUNCTION_PATTERNS[analysis.language]
            matches = re.findall(pattern, content, re.MULTILINE)
            analysis.functions = [m if isinstance(m, str) else next((x for x in m if x), '') for m in matches]
        
        if analysis.language in self.CLASS_PATTERNS:
            pattern = self.CLASS_PATTERNS[analysis.language]
            analysis.classes = re.findall(pattern, content, re.MULTILINE)
        
        # Find imports
        if analysis.language in self.IMPORT_PATTERNS:
            pattern = self.IMPORT_PATTERNS[analysis.language]
            analysis.imports = re.findall(pattern, content)
        
        # Calculate complexity (simplified cyclomatic complexity)
        analysis.complexity = self._calculate_complexity(content, analysis.language)
        
        return analysis
    
    def analyze_directory(self, path: Path, 
                         extensions: Optional[Set[str]] = None) -> Dict[str, Any]:
        """
        Analyze all code files in a directory.
        
        Args:
            path: Directory path
            extensions: File extensions to analyze (default: all known)
            
        Returns:
            Summary statistics
        """
        path = Path(path)
        extensions = extensions or set(self.LANGUAGE_MAP.keys())
        
        results = {
            'files': [],
            'totals': {
                'files': 0,
                'lines_of_code': 0,
                'blank_lines': 0,
                'comment_lines': 0,
                'total_lines': 0,
                'todos': 0,
                'fixmes': 0,
                'functions': 0,
                'classes': 0,
            },
            'by_language': {},
        }
        
        for filepath in path.rglob('*'):
            if filepath.is_file() and filepath.suffix.lower() in extensions:
                analysis = self.analyze_file(filepath)
                results['files'].append(analysis.to_dict())
                
                # Update totals
                results['totals']['files'] += 1
                results['totals']['lines_of_code'] += analysis.lines_of_code
                results['totals']['blank_lines'] += analysis.blank_lines
                results['totals']['comment_lines'] += analysis.comment_lines
                results['totals']['total_lines'] += analysis.total_lines
                results['totals']['todos'] += len(analysis.todos)
                results['totals']['fixmes'] += len(analysis.fixmes)
                results['totals']['functions'] += len(analysis.functions)
                results['totals']['classes'] += len(analysis.classes)
                
                # Update by language
                lang = analysis.language
                if lang not in results['by_language']:
                    results['by_language'][lang] = {
                        'files': 0,
                        'lines_of_code': 0,
                    }
                results['by_language'][lang]['files'] += 1
                results['by_language'][lang]['lines_of_code'] += analysis.lines_of_code
        
        return results
    
    def _is_comment_line(self, line: str, language: str) -> bool:
        """Check if a line is a comment."""
        patterns = self.COMMENT_PATTERNS.get(language, (None, None, None, None))
        single_line_pattern = patterns[0]
        
        if single_line_pattern:
            if re.match(single_line_pattern, line):
                return True
        
        # Simple heuristic for comment starts
        common_comment_starts = ['#', '//', '/*', '*', '<!--', '--']
        return any(line.startswith(start) for start in common_comment_starts)
    
    def _calculate_complexity(self, content: str, language: str) -> int:
        """
        Calculate simplified cyclomatic complexity.
        Counts decision points: if, else, elif, for, while, case, catch, &&, ||
        """
        complexity = 1  # Base complexity
        
        # Decision keywords
        keywords = [
            r'\bif\b', r'\belse\b', r'\belif\b', r'\bfor\b', r'\bwhile\b',
            r'\bcase\b', r'\bcatch\b', r'\bexcept\b', r'\b\?\s*:', r'&&', r'\|\|',
        ]
        
        for pattern in keywords:
            complexity += len(re.findall(pattern, content))
        
        return complexity


# Create singleton instance
file_analyzer = FileAnalyzer()
