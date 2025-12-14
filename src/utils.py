"""
StructureMaster - Utility Functions Module
Contains common utility functions used across the application.
"""

import os
import sys
import re
import hashlib
import mimetypes
import stat
import shutil
import tempfile
from pathlib import Path
from typing import Optional, List, Dict, Any, Union, Tuple, Generator
from datetime import datetime
import json
import fnmatch
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
import chardet


class Utils:
    """Collection of utility functions for StructureMaster."""
    
    # Thread-local storage for caching
    _local = threading.local()
    
    # =========================================================================
    # File System Utilities
    # =========================================================================
    
    @staticmethod
    def ensure_directory(path: Union[str, Path]) -> Path:
        """Create directory if it doesn't exist."""
        path = Path(path)
        path.mkdir(parents=True, exist_ok=True)
        return path
    
    @staticmethod
    def get_file_size(filepath: Union[str, Path]) -> int:
        """Get file size in bytes."""
        try:
            return Path(filepath).stat().st_size
        except OSError:
            return 0
    
    @staticmethod
    def get_file_size_human(size_bytes: int) -> str:
        """Convert bytes to human-readable format."""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.2f} PB"
    
    @staticmethod
    def get_file_dates(filepath: Union[str, Path]) -> Dict[str, datetime]:
        """Get creation and modification dates of a file."""
        path = Path(filepath)
        try:
            stat_info = path.stat()
            return {
                'created': datetime.fromtimestamp(stat_info.st_ctime),
                'modified': datetime.fromtimestamp(stat_info.st_mtime),
                'accessed': datetime.fromtimestamp(stat_info.st_atime),
            }
        except OSError:
            now = datetime.now()
            return {'created': now, 'modified': now, 'accessed': now}
    
    @staticmethod
    def get_file_permissions(filepath: Union[str, Path]) -> str:
        """Get file permissions in Unix-style format."""
        try:
            mode = Path(filepath).stat().st_mode
            perms = ''
            for who in ['USR', 'GRP', 'OTH']:
                for perm, char in [('R', 'r'), ('W', 'w'), ('X', 'x')]:
                    if mode & getattr(stat, f'S_I{perm}{who}'):
                        perms += char
                    else:
                        perms += '-'
            return perms
        except OSError:
            return '---------'
    
    @staticmethod
    def get_file_hash(filepath: Union[str, Path], algorithm: str = 'sha256') -> str:
        """Calculate hash of a file."""
        hash_func = hashlib.new(algorithm)
        try:
            with open(filepath, 'rb') as f:
                for chunk in iter(lambda: f.read(8192), b''):
                    hash_func.update(chunk)
            return hash_func.hexdigest()
        except (OSError, IOError):
            return ''
    
    @staticmethod
    def get_mime_type(filepath: Union[str, Path]) -> str:
        """Get MIME type of a file."""
        mime_type, _ = mimetypes.guess_type(str(filepath))
        return mime_type or 'application/octet-stream'
    
    @staticmethod
    def is_binary_file(filepath: Union[str, Path], chunk_size: int = 8192) -> bool:
        """Check if a file is binary by reading its content."""
        try:
            with open(filepath, 'rb') as f:
                chunk = f.read(chunk_size)
                if b'\x00' in chunk:
                    return True
                # Check for high ratio of non-printable characters
                text_chars = bytearray({7, 8, 9, 10, 12, 13, 27} | set(range(0x20, 0x100)))
                non_text = sum(1 for byte in chunk if byte not in text_chars)
                return len(chunk) > 0 and (non_text / len(chunk)) > 0.30
        except (OSError, IOError):
            return True
    
    @staticmethod
    def detect_encoding(filepath: Union[str, Path]) -> str:
        """Detect file encoding."""
        try:
            with open(filepath, 'rb') as f:
                raw = f.read(10000)
                result = chardet.detect(raw)
                return result.get('encoding', 'utf-8') or 'utf-8'
        except (OSError, IOError):
            return 'utf-8'
    
    @staticmethod
    def read_file_content(filepath: Union[str, Path], encoding: Optional[str] = None) -> Tuple[str, str]:
        """Read file content with auto-detected encoding."""
        if encoding is None:
            encoding = Utils.detect_encoding(filepath)
        
        try:
            with open(filepath, 'r', encoding=encoding, errors='replace') as f:
                return f.read(), encoding
        except Exception:
            # Fallback to binary read and decode
            with open(filepath, 'rb') as f:
                content = f.read()
                return content.decode(encoding, errors='replace'), encoding
    
    @staticmethod
    def write_file_content(filepath: Union[str, Path], content: str, 
                          encoding: str = 'utf-8') -> bool:
        """Write content to a file."""
        try:
            path = Path(filepath)
            path.parent.mkdir(parents=True, exist_ok=True)
            with open(path, 'w', encoding=encoding, newline='') as f:
                f.write(content)
            return True
        except (OSError, IOError):
            return False
    
    @staticmethod
    def copy_file(src: Union[str, Path], dst: Union[str, Path]) -> bool:
        """Copy a file from source to destination."""
        try:
            Path(dst).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
            return True
        except (OSError, IOError):
            return False
    
    @staticmethod
    def safe_delete(path: Union[str, Path]) -> bool:
        """Safely delete a file or directory."""
        try:
            p = Path(path)
            if p.is_file():
                p.unlink()
            elif p.is_dir():
                shutil.rmtree(p)
            return True
        except (OSError, IOError):
            return False
    
    @staticmethod
    def get_temp_file(suffix: str = '', prefix: str = 'structuremaster_') -> Path:
        """Create a temporary file and return its path."""
        fd, path = tempfile.mkstemp(suffix=suffix, prefix=prefix)
        os.close(fd)
        return Path(path)
    
    @staticmethod
    def get_temp_dir(prefix: str = 'structuremaster_') -> Path:
        """Create a temporary directory and return its path."""
        return Path(tempfile.mkdtemp(prefix=prefix))
    
    # =========================================================================
    # Path Utilities
    # =========================================================================
    
    @staticmethod
    def normalize_path(path: Union[str, Path]) -> Path:
        """Normalize a path to absolute form."""
        return Path(path).resolve()
    
    @staticmethod
    def get_relative_path(path: Union[str, Path], base: Union[str, Path]) -> str:
        """Get relative path from base."""
        try:
            return str(Path(path).relative_to(Path(base)))
        except ValueError:
            return str(path)
    
    @staticmethod
    def is_subpath(path: Union[str, Path], parent: Union[str, Path]) -> bool:
        """Check if path is a subpath of parent."""
        try:
            Path(path).relative_to(Path(parent))
            return True
        except ValueError:
            return False
    
    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """Remove invalid characters from filename."""
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            filename = filename.replace(char, '_')
        return filename.strip('. ')
    
    @staticmethod
    def get_extension(filepath: Union[str, Path]) -> str:
        """Get file extension in lowercase."""
        return Path(filepath).suffix.lower()
    
    @staticmethod
    def get_basename(filepath: Union[str, Path]) -> str:
        """Get filename without path."""
        return Path(filepath).name
    
    @staticmethod
    def get_stem(filepath: Union[str, Path]) -> str:
        """Get filename without extension."""
        return Path(filepath).stem
    
    # =========================================================================
    # Pattern Matching Utilities
    # =========================================================================
    
    @staticmethod
    def matches_pattern(path: str, pattern: str) -> bool:
        """Check if path matches a glob pattern."""
        # Handle directory patterns
        if pattern.endswith('/'):
            pattern = pattern[:-1]
            path_parts = path.replace('\\', '/').split('/')
            return any(fnmatch.fnmatch(part, pattern) for part in path_parts)
        
        # Handle regular patterns
        return fnmatch.fnmatch(path, pattern) or \
               fnmatch.fnmatch(Path(path).name, pattern)
    
    @staticmethod
    def matches_any_pattern(path: str, patterns: List[str]) -> bool:
        """Check if path matches any of the patterns."""
        return any(Utils.matches_pattern(path, p) for p in patterns)
    
    @staticmethod
    def load_ignore_patterns(ignore_file: Union[str, Path]) -> List[str]:
        """Load patterns from an ignore file."""
        patterns = []
        try:
            with open(ignore_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        patterns.append(line)
        except (OSError, IOError):
            pass
        return patterns
    
    # =========================================================================
    # JSON/YAML Utilities
    # =========================================================================
    
    @staticmethod
    def load_json(filepath: Union[str, Path]) -> Dict[str, Any]:
        """Load JSON file."""
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    @staticmethod
    def save_json(filepath: Union[str, Path], data: Dict[str, Any], 
                  indent: int = 2) -> bool:
        """Save data to JSON file."""
        try:
            Path(filepath).parent.mkdir(parents=True, exist_ok=True)
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=indent, ensure_ascii=False, default=str)
            return True
        except (OSError, IOError):
            return False
    
    @staticmethod
    def to_json(data: Any, indent: int = 2) -> str:
        """Convert data to JSON string."""
        return json.dumps(data, indent=indent, ensure_ascii=False, default=str)
    
    @staticmethod
    def from_json(json_str: str) -> Any:
        """Parse JSON string."""
        return json.loads(json_str)
    
    # =========================================================================
    # String Utilities
    # =========================================================================
    
    @staticmethod
    def truncate_string(s: str, max_length: int, suffix: str = '...') -> str:
        """Truncate string to maximum length."""
        if len(s) <= max_length:
            return s
        return s[:max_length - len(suffix)] + suffix
    
    @staticmethod
    def count_lines(text: str) -> int:
        """Count number of lines in text."""
        return len(text.splitlines())
    
    @staticmethod
    def indent_text(text: str, spaces: int = 2) -> str:
        """Indent each line of text."""
        indent = ' ' * spaces
        return '\n'.join(indent + line for line in text.splitlines())
    
    @staticmethod
    def strip_comments(code: str, language: str) -> str:
        """Strip comments from code (basic implementation)."""
        if language in ['python', 'py', 'shell', 'bash', 'sh', 'yaml', 'yml']:
            # Remove # comments
            return re.sub(r'#.*$', '', code, flags=re.MULTILINE)
        elif language in ['javascript', 'js', 'typescript', 'ts', 'java', 'c', 'cpp', 'cs', 'go']:
            # Remove // and /* */ comments
            code = re.sub(r'//.*$', '', code, flags=re.MULTILINE)
            code = re.sub(r'/\*[\s\S]*?\*/', '', code)
            return code
        return code
    
    # =========================================================================
    # Tree Structure Utilities
    # =========================================================================
    
    @staticmethod
    def build_tree_string(structure: Dict[str, Any], prefix: str = '', 
                         is_last: bool = True) -> str:
        """Build a tree-like string representation of structure."""
        lines = []
        items = list(structure.items())
        
        for i, (name, content) in enumerate(items):
            is_last_item = (i == len(items) - 1)
            connector = '└── ' if is_last_item else '├── '
            lines.append(f"{prefix}{connector}{name}")
            
            if isinstance(content, dict) and content:
                extension = '    ' if is_last_item else '│   '
                lines.append(Utils.build_tree_string(
                    content, prefix + extension, is_last_item
                ))
        
        return '\n'.join(lines)
    
    @staticmethod
    def parse_tree_string(tree_str: str) -> Dict[str, Any]:
        """Parse a tree-like string into a structure dictionary."""
        lines = tree_str.strip().split('\n')
        root: Dict[str, Any] = {}
        stack: List[Tuple[int, Dict[str, Any]]] = [(0, root)]
        
        for line in lines:
            if not line.strip():
                continue
            
            # Calculate depth based on indentation
            stripped = line.lstrip()
            indent = len(line) - len(stripped)
            
            # Remove tree characters
            name = re.sub(r'^[├└│─\s]+', '', stripped).strip()
            if not name:
                continue
            
            # Determine if it's a directory (ends with /)
            is_dir = name.endswith('/')
            if is_dir:
                name = name[:-1]
            
            # Find parent level
            while stack and stack[-1][0] >= indent:
                stack.pop()
            
            if not stack:
                stack = [(0, root)]
            
            parent = stack[-1][1]
            
            if is_dir:
                parent[name] = {}
                stack.append((indent, parent[name]))
            else:
                parent[name] = None
        
        return root
    
    # =========================================================================
    # Threading Utilities
    # =========================================================================
    
    @staticmethod
    def parallel_map(func, items: List[Any], max_workers: Optional[int] = None,
                    show_progress: bool = False) -> List[Any]:
        """Execute function on items in parallel."""
        results = []
        max_workers = max_workers or os.cpu_count() or 4
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {executor.submit(func, item): i for i, item in enumerate(items)}
            results = [None] * len(items)
            
            for future in as_completed(futures):
                idx = futures[future]
                try:
                    results[idx] = future.result()
                except Exception as e:
                    results[idx] = None
        
        return results
    
    # =========================================================================
    # Date/Time Utilities
    # =========================================================================
    
    @staticmethod
    def format_datetime(dt: datetime, format_str: str = '%Y-%m-%d %H:%M:%S') -> str:
        """Format datetime to string."""
        return dt.strftime(format_str)
    
    @staticmethod
    def parse_datetime(date_str: str, format_str: str = '%Y-%m-%d %H:%M:%S') -> datetime:
        """Parse string to datetime."""
        return datetime.strptime(date_str, format_str)
    
    @staticmethod
    def get_timestamp() -> str:
        """Get current timestamp string."""
        return datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # =========================================================================
    # Clipboard Utilities
    # =========================================================================
    
    @staticmethod
    def get_clipboard_content() -> str:
        """Get content from clipboard."""
        try:
            import pyperclip
            return pyperclip.paste()
        except ImportError:
            # Fallback for Windows
            if sys.platform == 'win32':
                import subprocess
                result = subprocess.run(['powershell', '-command', 
                                       'Get-Clipboard'], capture_output=True, text=True)
                return result.stdout
        except Exception:
            pass
        return ''
    
    @staticmethod
    def set_clipboard_content(content: str) -> bool:
        """Set content to clipboard."""
        try:
            import pyperclip
            pyperclip.copy(content)
            return True
        except Exception:
            return False
    
    # =========================================================================
    # Validation Utilities
    # =========================================================================
    
    @staticmethod
    def is_valid_path(path: str) -> bool:
        """Check if path string is valid."""
        try:
            Path(path)
            # Check for invalid characters
            invalid_chars = '<>"|?*' if sys.platform == 'win32' else '\x00'
            return not any(c in path for c in invalid_chars)
        except Exception:
            return False
    
    @staticmethod
    def is_valid_json(json_str: str) -> bool:
        """Check if string is valid JSON."""
        try:
            json.loads(json_str)
            return True
        except (json.JSONDecodeError, TypeError):
            return False
    
    @staticmethod
    def validate_structure(structure: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Validate a structure dictionary."""
        errors = []
        
        def validate_recursive(struct: Dict[str, Any], path: str = ''):
            for name, content in struct.items():
                current_path = f"{path}/{name}" if path else name
                
                # Check for valid name
                if not name or any(c in name for c in '<>:"|?*'):
                    errors.append(f"Invalid name: {current_path}")
                
                # Recursively validate directories
                if isinstance(content, dict):
                    validate_recursive(content, current_path)
        
        validate_recursive(structure)
        return len(errors) == 0, errors


# Create singleton instance for convenience
utils = Utils()
