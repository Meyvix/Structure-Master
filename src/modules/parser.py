"""
StructureMaster - Parser Module
Parses project structures from various input formats:
- JSON (nested or flat)
- Tree-like text format
- Clipboard content
- Direct text input
"""

import re
import json
from pathlib import Path
from typing import Dict, Any, List, Optional, Union, Tuple
from dataclasses import dataclass, field
from enum import Enum, auto

from .logger import Logger, logger


class InputFormat(Enum):
    """Supported input formats."""
    JSON_NESTED = auto()     # {"src": {"main.py": null, "utils": {"helper.py": null}}}
    JSON_FLAT = auto()       # ["src/main.py", "src/utils/helper.py"]
    TREE = auto()            # Tree-like text format with ├── └── etc.
    PLAIN = auto()           # Plain text with paths, one per line
    UNKNOWN = auto()


@dataclass
class ParseResult:
    """Result of parsing operation."""
    success: bool
    structure: Dict[str, Any] = field(default_factory=dict)
    format_detected: InputFormat = InputFormat.UNKNOWN
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    stats: Dict[str, int] = field(default_factory=dict)


class StructureParser:
    """
    Parses project structures from various input formats.
    """
    
    # Tree characters for detection
    TREE_CHARS = {'├', '└', '│', '─', '|', '+', '`', '-'}
    
    def __init__(self):
        """Initialize the parser."""
        self.logger = Logger.get_instance()
    
    def parse(self, input_data: Union[str, Path, Dict], 
              format_hint: Optional[InputFormat] = None) -> ParseResult:
        """
        Parse input data into a structure dictionary.
        
        Args:
            input_data: String content, file path, or dictionary
            format_hint: Optional hint about input format
            
        Returns:
            ParseResult with parsed structure
        """
        # Handle file path
        if isinstance(input_data, Path) or (isinstance(input_data, str) and 
                                            Path(input_data).exists()):
            return self.parse_file(Path(input_data), format_hint)
        
        # Handle dictionary (already parsed)
        if isinstance(input_data, dict):
            return ParseResult(
                success=True,
                structure=input_data,
                format_detected=InputFormat.JSON_NESTED,
                stats=self._calculate_stats(input_data)
            )
        
        # Handle string content
        if isinstance(input_data, str):
            return self.parse_string(input_data, format_hint)
        
        return ParseResult(
            success=False,
            errors=["Invalid input type"]
        )
    
    def parse_file(self, filepath: Path, 
                   format_hint: Optional[InputFormat] = None) -> ParseResult:
        """Parse structure from a file."""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Auto-detect format if not provided
            if format_hint is None:
                if filepath.suffix.lower() == '.json':
                    format_hint = InputFormat.JSON_NESTED
            
            return self.parse_string(content, format_hint)
            
        except FileNotFoundError:
            return ParseResult(
                success=False,
                errors=[f"File not found: {filepath}"]
            )
        except Exception as e:
            return ParseResult(
                success=False,
                errors=[f"Error reading file: {str(e)}"]
            )
    
    def parse_string(self, content: str, 
                     format_hint: Optional[InputFormat] = None) -> ParseResult:
        """Parse structure from string content."""
        content = content.strip()
        
        if not content:
            return ParseResult(
                success=False,
                errors=["Empty input"]
            )
        
        # Detect format if not provided
        if format_hint is None:
            format_hint = self._detect_format(content)
        
        self.logger.debug(f"Detected format: {format_hint.name}")
        
        # Parse based on format
        if format_hint in (InputFormat.JSON_NESTED, InputFormat.JSON_FLAT):
            return self._parse_json(content)
        elif format_hint == InputFormat.TREE:
            return self._parse_tree(content)
        elif format_hint == InputFormat.PLAIN:
            return self._parse_plain(content)
        else:
            # Try all parsers
            return self._parse_auto(content)
    
    def parse_clipboard(self) -> ParseResult:
        """Parse structure from clipboard content."""
        try:
            import pyperclip
            content = pyperclip.paste()
            if not content:
                return ParseResult(
                    success=False,
                    errors=["Clipboard is empty"]
                )
            return self.parse_string(content)
        except ImportError:
            return ParseResult(
                success=False,
                errors=["Clipboard support not available (install pyperclip)"]
            )
        except Exception as e:
            return ParseResult(
                success=False,
                errors=[f"Error reading clipboard: {str(e)}"]
            )
    
    def _detect_format(self, content: str) -> InputFormat:
        """Auto-detect the input format."""
        content = content.strip()
        
        # Check for JSON
        if content.startswith('{') or content.startswith('['):
            try:
                data = json.loads(content)
                if isinstance(data, list):
                    return InputFormat.JSON_FLAT
                elif isinstance(data, dict):
                    return InputFormat.JSON_NESTED
            except json.JSONDecodeError:
                pass
        
        # Check for tree format
        first_lines = content[:500]
        if any(c in first_lines for c in self.TREE_CHARS):
            return InputFormat.TREE
        
        # Default to plain text
        return InputFormat.PLAIN
    
    def _parse_json(self, content: str) -> ParseResult:
        """Parse JSON format."""
        try:
            data = json.loads(content)
            
            # Handle flat list of paths
            if isinstance(data, list):
                structure = self._paths_to_structure(data)
                format_detected = InputFormat.JSON_FLAT
            else:
                structure = self._normalize_structure(data)
                format_detected = InputFormat.JSON_NESTED
            
            return ParseResult(
                success=True,
                structure=structure,
                format_detected=format_detected,
                stats=self._calculate_stats(structure)
            )
            
        except json.JSONDecodeError as e:
            return ParseResult(
                success=False,
                errors=[f"Invalid JSON: {str(e)}"]
            )
    
    def _parse_tree(self, content: str) -> ParseResult:
        """Parse tree-like text format."""
        lines = content.split('\n')
        structure: Dict[str, Any] = {}
        errors: List[str] = []
        warnings: List[str] = []
        
        # Stack to track current path: [(indent_level, dict_ref)]
        stack: List[Tuple[int, Dict[str, Any]]] = [(-1, structure)]
        
        for line_num, line in enumerate(lines, 1):
            if not line.strip():
                continue
            
            # Calculate effective indent
            original_line = line
            
            # Remove tree characters and calculate indent
            # Pattern: spaces/tabs, then tree chars (├└│─|+-`), then spaces, then name
            match = re.match(r'^([\s│|]*)([\s├└─|+`\-]*)(.*)$', line)
            if not match:
                continue
            
            prefix, tree_part, name = match.groups()
            name = name.strip()
            
            if not name:
                continue
            
            # Calculate indent level based on prefix length
            indent = len(prefix) + len(tree_part)
            
            # Determine if it's a directory
            is_dir = name.endswith('/') or name.endswith('\\')
            if is_dir:
                name = name.rstrip('/\\')
            
            # Clean up the name
            name = self._clean_name(name)
            if not name:
                continue
            
            # Validate name
            if not self._is_valid_name(name):
                warnings.append(f"Line {line_num}: Potentially invalid name '{name}'")
            
            # Find correct parent level
            while len(stack) > 1 and stack[-1][0] >= indent:
                stack.pop()
            
            parent = stack[-1][1]
            
            # Add to structure
            if is_dir or self._looks_like_directory(name):
                parent[name] = {}
                stack.append((indent, parent[name]))
            else:
                parent[name] = None
        
        return ParseResult(
            success=True,
            structure=structure,
            format_detected=InputFormat.TREE,
            errors=errors,
            warnings=warnings,
            stats=self._calculate_stats(structure)
        )
    
    def _parse_plain(self, content: str) -> ParseResult:
        """Parse plain text format (one path per line)."""
        lines = content.strip().split('\n')
        paths = []
        errors = []
        
        for line_num, line in enumerate(lines, 1):
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            
            # Clean the path
            path = line.replace('\\', '/')
            if path:
                paths.append(path)
        
        structure = self._paths_to_structure(paths)
        
        return ParseResult(
            success=True,
            structure=structure,
            format_detected=InputFormat.PLAIN,
            errors=errors,
            stats=self._calculate_stats(structure)
        )
    
    def _parse_auto(self, content: str) -> ParseResult:
        """Try all parsers and return best result."""
        # Try JSON first
        result = self._parse_json(content)
        if result.success:
            return result
        
        # Try tree format
        result = self._parse_tree(content)
        if result.success and result.structure:
            return result
        
        # Try plain format
        result = self._parse_plain(content)
        if result.success and result.structure:
            return result
        
        return ParseResult(
            success=False,
            errors=["Could not parse input in any supported format"]
        )
    
    def _paths_to_structure(self, paths: List[str]) -> Dict[str, Any]:
        """Convert list of paths to nested structure dictionary."""
        structure: Dict[str, Any] = {}
        
        for path in paths:
            path = path.strip().replace('\\', '/')
            if not path:
                continue
            
            parts = [p for p in path.split('/') if p]
            current = structure
            
            for i, part in enumerate(parts):
                is_last = (i == len(parts) - 1)
                is_dir = path.endswith('/') and is_last
                
                if part not in current:
                    if is_last and not is_dir:
                        current[part] = None  # File
                    else:
                        current[part] = {}    # Directory
                
                if isinstance(current[part], dict):
                    current = current[part]
        
        return structure
    
    def _normalize_structure(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize and validate structure dictionary."""
        normalized: Dict[str, Any] = {}
        
        for key, value in data.items():
            key = str(key).strip()
            if not key:
                continue
            
            if isinstance(value, dict):
                normalized[key] = self._normalize_structure(value)
            elif value is None or value == '' or value == {}:
                normalized[key] = None
            else:
                # Treat other values as file content markers
                normalized[key] = None
        
        return normalized
    
    def _clean_name(self, name: str) -> str:
        """Clean up a file/folder name."""
        # Remove common tree characters that might be left
        name = re.sub(r'^[├└│─|+`\-\s]+', '', name)
        name = name.strip()
        return name
    
    def _is_valid_name(self, name: str) -> bool:
        """Check if a name is valid for file/folder."""
        if not name:
            return False
        invalid_chars = '<>:"|?*\x00'
        return not any(c in name for c in invalid_chars)
    
    def _looks_like_directory(self, name: str) -> bool:
        """Guess if a name is a directory based on pattern."""
        # No extension usually means directory
        if '.' not in name:
            return True
        # Some known directories with dots
        if name in ['.git', '.vscode', '.idea', '.github', '.config']:
            return True
        return False
    
    def _calculate_stats(self, structure: Dict[str, Any]) -> Dict[str, int]:
        """Calculate statistics for structure."""
        stats = {'files': 0, 'directories': 0, 'depth': 0}
        
        def count_recursive(struct: Dict[str, Any], depth: int = 1):
            stats['depth'] = max(stats['depth'], depth)
            for name, content in struct.items():
                if isinstance(content, dict):
                    stats['directories'] += 1
                    if content:  # Non-empty dict
                        count_recursive(content, depth + 1)
                else:
                    stats['files'] += 1
        
        count_recursive(structure)
        return stats
    
    def to_tree_string(self, structure: Dict[str, Any], 
                       prefix: str = '', show_files: bool = True) -> str:
        """Convert structure to tree-like string representation."""
        lines = []
        items = sorted(structure.items(), 
                      key=lambda x: (isinstance(x[1], dict) == False, x[0].lower()))
        
        for i, (name, content) in enumerate(items):
            is_last = (i == len(items) - 1)
            connector = '└── ' if is_last else '├── '
            
            if isinstance(content, dict):
                lines.append(f"{prefix}{connector}{name}/")
                if content:
                    extension = '    ' if is_last else '│   '
                    lines.append(self.to_tree_string(
                        content, prefix + extension, show_files
                    ))
            elif show_files:
                lines.append(f"{prefix}{connector}{name}")
        
        return '\n'.join(lines)
    
    def to_json(self, structure: Dict[str, Any], indent: int = 2) -> str:
        """Convert structure to JSON string."""
        return json.dumps(structure, indent=indent, ensure_ascii=False)
    
    def to_path_list(self, structure: Dict[str, Any], 
                     prefix: str = '') -> List[str]:
        """Convert structure to list of paths."""
        paths = []
        
        for name, content in structure.items():
            current_path = f"{prefix}/{name}" if prefix else name
            
            if isinstance(content, dict):
                paths.append(current_path + '/')
                paths.extend(self.to_path_list(content, current_path))
            else:
                paths.append(current_path)
        
        return paths


# Create singleton instance
parser = StructureParser()
