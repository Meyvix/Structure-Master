"""
StructureMaster - Validator Module
Validates project structures for correctness and consistency.
"""

import re
import os
from pathlib import Path
from typing import Dict, Any, List, Optional, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum, auto

from .logger import Logger


class ValidationLevel(Enum):
    """Validation issue severity levels."""
    INFO = auto()
    WARNING = auto()
    ERROR = auto()
    CRITICAL = auto()


@dataclass
class ValidationIssue:
    """Represents a single validation issue."""
    level: ValidationLevel
    message: str
    path: str = ''
    suggestion: str = ''
    
    def to_dict(self) -> Dict[str, str]:
        return {
            'level': self.level.name,
            'message': self.message,
            'path': self.path,
            'suggestion': self.suggestion,
        }


@dataclass
class ValidationResult:
    """Result of validation operation."""
    is_valid: bool
    issues: List[ValidationIssue] = field(default_factory=list)
    stats: Dict[str, int] = field(default_factory=lambda: {
        'total_items': 0,
        'files': 0,
        'directories': 0,
        'errors': 0,
        'warnings': 0,
    })
    
    @property
    def errors(self) -> List[ValidationIssue]:
        return [i for i in self.issues if i.level in 
                (ValidationLevel.ERROR, ValidationLevel.CRITICAL)]
    
    @property
    def warnings(self) -> List[ValidationIssue]:
        return [i for i in self.issues if i.level == ValidationLevel.WARNING]
    
    def add_issue(self, level: ValidationLevel, message: str, 
                  path: str = '', suggestion: str = '') -> None:
        """Add a validation issue."""
        self.issues.append(ValidationIssue(level, message, path, suggestion))
        if level in (ValidationLevel.ERROR, ValidationLevel.CRITICAL):
            self.stats['errors'] += 1
            self.is_valid = False
        elif level == ValidationLevel.WARNING:
            self.stats['warnings'] += 1


class StructureValidator:
    """
    Validates project structures for:
    - Valid file/folder names
    - Path consistency
    - Reserved names
    - Structure depth
    - Ignore patterns
    """
    
    # Invalid characters for different OSes
    WINDOWS_INVALID_CHARS = '<>:"|?*\x00'
    UNIX_INVALID_CHARS = '/\x00'
    
    # Reserved names on Windows
    WINDOWS_RESERVED_NAMES = {
        'CON', 'PRN', 'AUX', 'NUL',
        'COM1', 'COM2', 'COM3', 'COM4', 'COM5', 'COM6', 'COM7', 'COM8', 'COM9',
        'LPT1', 'LPT2', 'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9',
    }
    
    # Maximum path length
    MAX_PATH_LENGTH = 260  # Windows default
    MAX_NAME_LENGTH = 255  # Most filesystems
    MAX_DEPTH = 50         # Reasonable depth limit
    
    def __init__(self, ignore_patterns: Optional[List[str]] = None):
        """
        Initialize validator.
        
        Args:
            ignore_patterns: Patterns to ignore during validation
        """
        self.logger = Logger.get_instance()
        self.ignore_patterns = ignore_patterns or []
        self.is_windows = os.name == 'nt'
    
    def validate(self, structure: Dict[str, Any], 
                 output_path: Optional[Path] = None) -> ValidationResult:
        """
        Validate a structure dictionary.
        
        Args:
            structure: Structure dictionary to validate
            output_path: Optional output path for conflict detection
            
        Returns:
            ValidationResult with validation status and issues
        """
        result = ValidationResult(is_valid=True)
        
        if not structure:
            result.add_issue(
                ValidationLevel.ERROR,
                "Empty structure",
                suggestion="Provide at least one file or directory"
            )
            return result
        
        # Track all paths for duplicate detection
        all_paths: Set[str] = set()
        
        # Validate recursively
        self._validate_recursive(
            structure=structure,
            current_path='',
            result=result,
            all_paths=all_paths,
            depth=0
        )
        
        # Check for conflicts with output path
        if output_path and output_path.exists():
            self._check_output_conflicts(structure, output_path, result)
        
        return result
    
    def _validate_recursive(self, structure: Dict[str, Any], current_path: str,
                           result: ValidationResult, all_paths: Set[str],
                           depth: int) -> None:
        """Recursively validate structure."""
        
        # Check depth
        if depth > self.MAX_DEPTH:
            result.add_issue(
                ValidationLevel.ERROR,
                f"Maximum depth ({self.MAX_DEPTH}) exceeded",
                path=current_path,
                suggestion="Reduce nesting level"
            )
            return
        
        for name, content in structure.items():
            full_path = f"{current_path}/{name}" if current_path else name
            is_dir = isinstance(content, dict)
            
            # Update stats
            result.stats['total_items'] += 1
            if is_dir:
                result.stats['directories'] += 1
            else:
                result.stats['files'] += 1
            
            # Skip ignored paths
            if self._is_ignored(full_path):
                continue
            
            # Validate name
            self._validate_name(name, full_path, result)
            
            # Check for duplicate paths (case-insensitive on Windows)
            check_path = full_path.lower() if self.is_windows else full_path
            if check_path in all_paths:
                result.add_issue(
                    ValidationLevel.ERROR,
                    f"Duplicate path detected",
                    path=full_path,
                    suggestion="Remove duplicate entries"
                )
            else:
                all_paths.add(check_path)
            
            # Check path length
            if len(full_path) > self.MAX_PATH_LENGTH:
                result.add_issue(
                    ValidationLevel.ERROR,
                    f"Path exceeds maximum length ({self.MAX_PATH_LENGTH})",
                    path=full_path,
                    suggestion="Shorten path by renaming folders"
                )
            
            # Recursively validate directories
            if is_dir and content:
                self._validate_recursive(
                    content, full_path, result, all_paths, depth + 1
                )
    
    def _validate_name(self, name: str, path: str, 
                       result: ValidationResult) -> None:
        """Validate a single file/folder name."""
        
        # Check for empty name
        if not name or not name.strip():
            result.add_issue(
                ValidationLevel.ERROR,
                "Empty name",
                path=path,
                suggestion="Provide a valid name"
            )
            return
        
        # Check name length
        if len(name) > self.MAX_NAME_LENGTH:
            result.add_issue(
                ValidationLevel.ERROR,
                f"Name exceeds maximum length ({self.MAX_NAME_LENGTH})",
                path=path,
                suggestion="Shorten the name"
            )
        
        # Check for invalid characters
        invalid_chars = self.WINDOWS_INVALID_CHARS if self.is_windows else self.UNIX_INVALID_CHARS
        found_invalid = [c for c in name if c in invalid_chars]
        if found_invalid:
            result.add_issue(
                ValidationLevel.ERROR,
                f"Invalid characters: {found_invalid}",
                path=path,
                suggestion=f"Remove characters: {', '.join(repr(c) for c in found_invalid)}"
            )
        
        # Check for reserved names (Windows)
        if self.is_windows:
            base_name = name.split('.')[0].upper()
            if base_name in self.WINDOWS_RESERVED_NAMES:
                result.add_issue(
                    ValidationLevel.ERROR,
                    f"Reserved name on Windows: {base_name}",
                    path=path,
                    suggestion="Use a different name"
                )
        
        # Check for leading/trailing spaces or dots
        if name != name.strip():
            result.add_issue(
                ValidationLevel.WARNING,
                "Name has leading or trailing whitespace",
                path=path,
                suggestion="Remove whitespace"
            )
        
        if name.endswith('.') and not name.startswith('.'):
            result.add_issue(
                ValidationLevel.WARNING,
                "Name ends with a dot",
                path=path,
                suggestion="Remove trailing dot"
            )
        
        # Check for potentially problematic names
        if name in ('.', '..'):
            result.add_issue(
                ValidationLevel.ERROR,
                "Invalid directory reference",
                path=path,
                suggestion="Remove '.' or '..' entries"
            )
        
        # Check for hidden files (info only)
        if name.startswith('.') and len(name) > 1:
            result.add_issue(
                ValidationLevel.INFO,
                "Hidden file/directory",
                path=path
            )
    
    def _is_ignored(self, path: str) -> bool:
        """Check if path matches any ignore pattern."""
        import fnmatch
        
        path_normalized = path.replace('\\', '/')
        path_parts = path_normalized.split('/')
        
        for pattern in self.ignore_patterns:
            # Directory pattern
            if pattern.endswith('/'):
                pattern_name = pattern[:-1]
                if any(fnmatch.fnmatch(part, pattern_name) for part in path_parts):
                    return True
            # File pattern
            elif fnmatch.fnmatch(path_normalized, pattern):
                return True
            elif fnmatch.fnmatch(path_parts[-1] if path_parts else '', pattern):
                return True
        
        return False
    
    def _check_output_conflicts(self, structure: Dict[str, Any], 
                                output_path: Path, 
                                result: ValidationResult) -> None:
        """Check for conflicts with existing files/directories."""
        
        def check_recursive(struct: Dict[str, Any], base_path: Path):
            for name, content in struct.items():
                target = base_path / name
                
                if target.exists():
                    is_dir = isinstance(content, dict)
                    target_is_dir = target.is_dir()
                    
                    if is_dir != target_is_dir:
                        result.add_issue(
                            ValidationLevel.ERROR,
                            f"Type conflict: expecting {'directory' if is_dir else 'file'}, "
                            f"found {'directory' if target_is_dir else 'file'}",
                            path=str(target),
                            suggestion="Use --force to overwrite or choose different output"
                        )
                    else:
                        result.add_issue(
                            ValidationLevel.WARNING,
                            f"{'Directory' if is_dir else 'File'} already exists",
                            path=str(target),
                            suggestion="Use --force to overwrite"
                        )
                
                if isinstance(content, dict) and content:
                    check_recursive(content, target)
        
        check_recursive(structure, output_path)
    
    def load_ignore_file(self, filepath: Path) -> List[str]:
        """Load ignore patterns from a file."""
        patterns = []
        
        if not filepath.exists():
            return patterns
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    # Skip empty lines and comments
                    if line and not line.startswith('#'):
                        patterns.append(line)
            
            self.ignore_patterns.extend(patterns)
            
        except Exception as e:
            self.logger.warn(f"Error loading ignore file: {e}")
        
        return patterns
    
    def set_ignore_patterns(self, patterns: List[str]) -> None:
        """Set ignore patterns."""
        self.ignore_patterns = patterns
    
    def add_ignore_pattern(self, pattern: str) -> None:
        """Add a single ignore pattern."""
        if pattern not in self.ignore_patterns:
            self.ignore_patterns.append(pattern)


# Create singleton instance
validator = StructureValidator()
