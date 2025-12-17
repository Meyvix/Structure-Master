"""
Stracture-Master - Scanner Module
Scans and extracts project structures from the filesystem.
Features:
- Multi-threaded scanning for large projects
- Smart caching for improved performance
- Auto project type detection
- Configurable ignore patterns
"""

import os
import fnmatch
from pathlib import Path
from typing import Dict, Any, List, Optional, Set, Callable, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
import hashlib
import json

from ..config import Config, ProjectType
from .logger import Logger
from .project_detector import ProjectDetector


@dataclass 
class FileInfo:
    """Information about a scanned file."""
    path: str
    name: str
    relative_path: str
    size: int
    is_file: bool
    is_dir: bool
    extension: str = ''
    modified_time: Optional[datetime] = None
    created_time: Optional[datetime] = None
    permissions: str = ''
    is_binary: bool = False
    is_hidden: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'path': self.path,
            'name': self.name,
            'relative_path': self.relative_path,
            'size': self.size,
            'is_file': self.is_file,
            'is_dir': self.is_dir,
            'extension': self.extension,
            'modified_time': self.modified_time.isoformat() if self.modified_time else None,
            'created_time': self.created_time.isoformat() if self.created_time else None,
            'permissions': self.permissions,
            'is_binary': self.is_binary,
            'is_hidden': self.is_hidden,
        }


@dataclass
class ScanResult:
    """Result of a project scan."""
    success: bool
    structure: Dict[str, Any] = field(default_factory=dict)
    files: List[FileInfo] = field(default_factory=list)
    project_type: ProjectType = ProjectType.UNKNOWN
    root_path: str = ''
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    stats: Dict[str, Any] = field(default_factory=lambda: {
        'total_files': 0,
        'total_directories': 0,
        'total_size': 0,
        'binary_files': 0,
        'hidden_items': 0,
        'skipped_items': 0,
        'scan_time_ms': 0,
    })


class ProjectScanner:
    """
    Scans projects and extracts their structure.
    """
    
    def __init__(self, 
                 ignore_patterns: Optional[List[str]] = None,
                 max_workers: Optional[int] = None,
                 use_cache: bool = True):
        """
        Initialize scanner.
        
        Args:
            ignore_patterns: Additional patterns to ignore
            max_workers: Maximum threads for parallel scanning
            use_cache: Enable caching for repeated scans
        """
        self.logger = Logger.get_instance()
        self.detector = ProjectDetector()
        self.ignore_patterns = ignore_patterns or []
        self.max_workers = max_workers or Config.MAX_WORKERS
        self.use_cache = use_cache
        
        # Cache for scan results
        self._cache: Dict[str, Tuple[float, ScanResult]] = {}
        self._cache_lock = threading.Lock()
        
        # Progress callback
        self._progress_callback: Optional[Callable[[int, int, str], None]] = None
    
    def scan(self, 
             path: Path,
             recursive: bool = True,
             include_hidden: bool = False,
             follow_symlinks: bool = False,
             auto_detect_project: bool = True,
             custom_ignore: Optional[List[str]] = None) -> ScanResult:
        """
        Scan a project directory.
        
        Args:
            path: Path to scan
            recursive: Scan subdirectories
            include_hidden: Include hidden files/directories
            follow_symlinks: Follow symbolic links
            auto_detect_project: Auto-detect project type
            custom_ignore: Additional ignore patterns
            
        Returns:
            ScanResult with structure and file information
        """
        path = Path(path).resolve()
        start_time = datetime.now()
        
        # Check if path exists
        if not path.exists():
            return ScanResult(
                success=False,
                errors=[f"Path does not exist: {path}"]
            )
        
        if not path.is_dir():
            return ScanResult(
                success=False,
                errors=[f"Path is not a directory: {path}"]
            )
        
        # Check cache
        cache_key = self._get_cache_key(path, recursive, include_hidden)
        if self.use_cache:
            cached = self._get_cached(cache_key, path)
            if cached:
                self.logger.debug(f"Using cached scan result for {path}")
                return cached
        
        # Initialize result
        result = ScanResult(
            success=True,
            root_path=str(path)
        )
        
        # Build ignore patterns
        all_ignore = set(Config.DEFAULT_IGNORE_PATTERNS)
        all_ignore.update(self.ignore_patterns)
        if custom_ignore:
            all_ignore.update(custom_ignore)
        
        # Load .structureignore if present
        structureignore = path / '.structureignore'
        if structureignore.exists():
            all_ignore.update(self._load_ignore_file(structureignore))
        
        # Auto-detect project type
        if auto_detect_project:
            result.project_type = self.detector.detect(path)
            self.logger.info(f"Detected project type: {result.project_type.name}")
            
            # Add project-specific ignore patterns
            project_patterns = Config.PROJECT_IGNORE_PATTERNS.get(result.project_type, [])
            all_ignore.update(project_patterns)
        
        # Scan directory
        try:
            if recursive:
                if self.max_workers > 1:
                    self._scan_parallel(
                        path, path, result, 
                        frozenset(all_ignore), 
                        include_hidden, 
                        follow_symlinks
                    )
                else:
                    self._scan_recursive(
                        path, path, result,
                        frozenset(all_ignore),
                        include_hidden,
                        follow_symlinks
                    )
            else:
                self._scan_single_level(
                    path, path, result,
                    frozenset(all_ignore),
                    include_hidden
                )
            
        except PermissionError as e:
            result.errors.append(f"Permission denied: {e}")
        except Exception as e:
            result.errors.append(f"Scan error: {str(e)}")
            result.success = False
        
        # Calculate scan time
        end_time = datetime.now()
        result.stats['scan_time_ms'] = int((end_time - start_time).total_seconds() * 1000)
        
        # Cache result
        if self.use_cache and result.success:
            self._cache_result(cache_key, path, result)
        
        return result
    
    def _scan_recursive(self, 
                        current_path: Path,
                        root_path: Path,
                        result: ScanResult,
                        ignore_patterns: frozenset,
                        include_hidden: bool,
                        follow_symlinks: bool,
                        current_dict: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Recursively scan directory."""
        if current_dict is None:
            current_dict = result.structure
        
        try:
            entries = sorted(current_path.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower()))
        except PermissionError:
            result.warnings.append(f"Permission denied: {current_path}")
            return current_dict
        except Exception as e:
            result.warnings.append(f"Error reading directory {current_path}: {e}")
            return current_dict
        
        for entry in entries:
            try:
                relative = entry.relative_to(root_path)
                relative_str = str(relative).replace('\\', '/')
                
                # Check if should skip
                if self._should_skip(entry.name, relative_str, ignore_patterns, include_hidden):
                    result.stats['skipped_items'] += 1
                    continue
                
                # Handle symlinks
                if entry.is_symlink() and not follow_symlinks:
                    continue
                
                # Get file info
                file_info = self._get_file_info(entry, root_path)
                result.files.append(file_info)
                
                if entry.is_dir():
                    result.stats['total_directories'] += 1
                    current_dict[entry.name] = {}
                    self._scan_recursive(
                        entry, root_path, result, ignore_patterns,
                        include_hidden, follow_symlinks, current_dict[entry.name]
                    )
                else:
                    result.stats['total_files'] += 1
                    result.stats['total_size'] += file_info.size
                    if file_info.is_binary:
                        result.stats['binary_files'] += 1
                    if file_info.is_hidden:
                        result.stats['hidden_items'] += 1
                    current_dict[entry.name] = None
                
                # Progress callback
                if self._progress_callback:
                    total = result.stats['total_files'] + result.stats['total_directories']
                    self._progress_callback(total, 0, entry.name)
                    
            except Exception as e:
                result.warnings.append(f"Error processing {entry}: {e}")
        
        return current_dict
    
    def _scan_parallel(self,
                       current_path: Path,
                       root_path: Path,
                       result: ScanResult,
                       ignore_patterns: frozenset,
                       include_hidden: bool,
                       follow_symlinks: bool) -> None:
        """Scan directories in parallel using thread pool."""
        
        # First pass: get all directories to scan
        dirs_to_scan: List[Tuple[Path, Dict[str, Any]]] = []
        
        def collect_dirs(path: Path, parent_dict: Dict[str, Any]):
            try:
                for entry in path.iterdir():
                    relative = entry.relative_to(root_path)
                    relative_str = str(relative).replace('\\', '/')
                    
                    if self._should_skip(entry.name, relative_str, ignore_patterns, include_hidden):
                        result.stats['skipped_items'] += 1
                        continue
                    
                    if entry.is_symlink() and not follow_symlinks:
                        continue
                    
                    if entry.is_dir():
                        parent_dict[entry.name] = {}
                        dirs_to_scan.append((entry, parent_dict[entry.name]))
                    else:
                        parent_dict[entry.name] = None
                        file_info = self._get_file_info(entry, root_path)
                        result.files.append(file_info)
                        result.stats['total_files'] += 1
                        result.stats['total_size'] += file_info.size
                        
            except PermissionError:
                result.warnings.append(f"Permission denied: {path}")
        
        # Start with root
        collect_dirs(current_path, result.structure)
        result.stats['total_directories'] += len(dirs_to_scan)
        
        # Process directories in parallel
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            while dirs_to_scan:
                futures = {}
                batch = dirs_to_scan[:self.max_workers * 2]
                dirs_to_scan = dirs_to_scan[self.max_workers * 2:]
                
                for dir_path, dir_dict in batch:
                    future = executor.submit(
                        self._scan_directory_files,
                        dir_path, root_path, dir_dict, ignore_patterns, include_hidden
                    )
                    futures[future] = (dir_path, dir_dict)
                
                for future in as_completed(futures):
                    dir_path, dir_dict = futures[future]
                    try:
                        sub_files, sub_dirs, sub_stats = future.result()
                        result.files.extend(sub_files)
                        result.stats['total_files'] += sub_stats['files']
                        result.stats['total_size'] += sub_stats['size']
                        
                        # Add new directories to scan
                        for sub_dir, sub_dict in sub_dirs:
                            dirs_to_scan.append((sub_dir, sub_dict))
                            result.stats['total_directories'] += 1
                            
                    except Exception as e:
                        result.warnings.append(f"Error scanning {dir_path}: {e}")
    
    def _scan_directory_files(self,
                              path: Path,
                              root_path: Path,
                              parent_dict: Dict[str, Any],
                              ignore_patterns: frozenset,
                              include_hidden: bool) -> Tuple[List[FileInfo], List[Tuple[Path, Dict]], Dict[str, int]]:
        """Scan a single directory (for parallel processing)."""
        files = []
        sub_dirs = []
        stats = {'files': 0, 'size': 0}
        
        try:
            for entry in path.iterdir():
                relative = entry.relative_to(root_path)
                relative_str = str(relative).replace('\\', '/')
                
                if self._should_skip(entry.name, relative_str, ignore_patterns, include_hidden):
                    continue
                
                if entry.is_dir():
                    parent_dict[entry.name] = {}
                    sub_dirs.append((entry, parent_dict[entry.name]))
                else:
                    parent_dict[entry.name] = None
                    file_info = self._get_file_info(entry, root_path)
                    files.append(file_info)
                    stats['files'] += 1
                    stats['size'] += file_info.size
                    
        except PermissionError:
            pass
        
        return files, sub_dirs, stats
    
    def _scan_single_level(self,
                           path: Path,
                           root_path: Path,
                           result: ScanResult,
                           ignore_patterns: frozenset,
                           include_hidden: bool) -> None:
        """Scan only the top level of a directory."""
        try:
            for entry in sorted(path.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower())):
                relative_str = entry.name
                
                if self._should_skip(entry.name, relative_str, ignore_patterns, include_hidden):
                    result.stats['skipped_items'] += 1
                    continue
                
                file_info = self._get_file_info(entry, root_path)
                result.files.append(file_info)
                
                if entry.is_dir():
                    result.stats['total_directories'] += 1
                    result.structure[entry.name] = {}
                else:
                    result.stats['total_files'] += 1
                    result.stats['total_size'] += file_info.size
                    result.structure[entry.name] = None
                    
        except PermissionError:
            result.warnings.append(f"Permission denied: {path}")
    
    def _should_skip(self, name: str, relative_path: str, 
                     ignore_patterns: frozenset, include_hidden: bool) -> bool:
        """Check if a file/directory should be skipped."""
        # Skip hidden files if not included
        if not include_hidden and name.startswith('.'):
            return True
        
        # Check ignore patterns
        for pattern in ignore_patterns:
            # Directory pattern (ends with /)
            if pattern.endswith('/'):
                if fnmatch.fnmatch(name, pattern[:-1]):
                    return True
            # Regular pattern
            elif fnmatch.fnmatch(name, pattern):
                return True
            elif fnmatch.fnmatch(relative_path, pattern):
                return True
        
        return False
    
    def _get_file_info(self, path: Path, root_path: Path) -> FileInfo:
        """Get detailed information about a file/directory."""
        try:
            stat = path.stat()
            relative = path.relative_to(root_path)
            
            # Check if binary
            is_binary = False
            if path.is_file():
                is_binary = Config.is_binary_file(str(path))
            
            # Get permissions
            permissions = self._format_permissions(stat.st_mode)
            
            return FileInfo(
                path=str(path),
                name=path.name,
                relative_path=str(relative).replace('\\', '/'),
                size=stat.st_size if path.is_file() else 0,
                is_file=path.is_file(),
                is_dir=path.is_dir(),
                extension=path.suffix.lower() if path.is_file() else '',
                modified_time=datetime.fromtimestamp(stat.st_mtime),
                created_time=datetime.fromtimestamp(stat.st_ctime),
                permissions=permissions,
                is_binary=is_binary,
                is_hidden=path.name.startswith('.'),
            )
        except Exception:
            return FileInfo(
                path=str(path),
                name=path.name,
                relative_path=str(path.relative_to(root_path)).replace('\\', '/'),
                size=0,
                is_file=path.is_file(),
                is_dir=path.is_dir(),
            )
    
    def _format_permissions(self, mode: int) -> str:
        """Format file permissions as Unix-style string."""
        import stat as stat_module
        perms = ''
        for who in ['USR', 'GRP', 'OTH']:
            for perm, char in [('R', 'r'), ('W', 'w'), ('X', 'x')]:
                if mode & getattr(stat_module, f'S_I{perm}{who}', 0):
                    perms += char
                else:
                    perms += '-'
        return perms
    
    def _load_ignore_file(self, filepath: Path) -> List[str]:
        """Load ignore patterns from a file."""
        patterns = []
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        patterns.append(line)
        except Exception:
            pass
        return patterns
    
    def _get_cache_key(self, path: Path, recursive: bool, include_hidden: bool) -> str:
        """Generate cache key for a scan."""
        key_data = f"{path}:{recursive}:{include_hidden}:{sorted(self.ignore_patterns)}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def _get_cached(self, key: str, path: Path) -> Optional[ScanResult]:
        """Get cached scan result if valid."""
        with self._cache_lock:
            if key not in self._cache:
                return None
            
            mtime, result = self._cache[key]
            
            # Check if cache is still valid
            try:
                current_mtime = path.stat().st_mtime
                if current_mtime > mtime:
                    del self._cache[key]
                    return None
            except Exception:
                return None
            
            return result
    
    def _cache_result(self, key: str, path: Path, result: ScanResult) -> None:
        """Cache a scan result."""
        with self._cache_lock:
            try:
                mtime = path.stat().st_mtime
                self._cache[key] = (mtime, result)
            except Exception:
                pass
    
    def clear_cache(self) -> None:
        """Clear the scan cache."""
        with self._cache_lock:
            self._cache.clear()
    
    def set_progress_callback(self, callback: Callable[[int, int, str], None]) -> None:
        """Set progress callback function."""
        self._progress_callback = callback
    
    def add_ignore_pattern(self, pattern: str) -> None:
        """Add an ignore pattern."""
        if pattern not in self.ignore_patterns:
            self.ignore_patterns.append(pattern)
    
    def set_ignore_patterns(self, patterns: List[str]) -> None:
        """Set ignore patterns."""
        self.ignore_patterns = list(patterns)


# Create singleton instance
scanner = ProjectScanner()
