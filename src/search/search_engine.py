"""
Stracture-Master - Search Engine Module
Advanced search with regex, filters, and content search.
"""

import re
import os
from pathlib import Path
from typing import Dict, Any, List, Optional, Set, Union, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
import fnmatch


@dataclass
class SearchMatch:
    """A search match result."""
    path: str
    filename: str
    line_number: Optional[int] = None
    column: Optional[int] = None
    context: str = ''
    match_text: str = ''
    match_type: str = 'filename'  # 'filename', 'content', 'path'
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'path': self.path,
            'filename': self.filename,
            'line_number': self.line_number,
            'column': self.column,
            'context': self.context,
            'match_text': self.match_text,
            'match_type': self.match_type,
        }


@dataclass
class SearchFilter:
    """Filters for search."""
    extensions: Optional[List[str]] = None
    exclude_extensions: Optional[List[str]] = None
    min_size: Optional[int] = None
    max_size: Optional[int] = None
    modified_after: Optional[datetime] = None
    modified_before: Optional[datetime] = None
    created_after: Optional[datetime] = None
    created_before: Optional[datetime] = None
    path_contains: Optional[str] = None
    path_not_contains: Optional[str] = None
    exclude_dirs: Optional[List[str]] = None
    include_hidden: bool = False
    
    def matches(self, file_path: Path, stat: os.stat_result) -> bool:
        """Check if file matches all filters."""
        try:
            # Hidden files
            if not self.include_hidden and file_path.name.startswith('.'):
                return False
            
            # Extensions
            ext = file_path.suffix.lower()
            if self.extensions and ext not in [e.lower() for e in self.extensions]:
                return False
            if self.exclude_extensions and ext in [e.lower() for e in self.exclude_extensions]:
                return False
            
            # Size
            size = stat.st_size
            if self.min_size and size < self.min_size:
                return False
            if self.max_size and size > self.max_size:
                return False
            
            # Modification time
            mtime = datetime.fromtimestamp(stat.st_mtime)
            if self.modified_after and mtime < self.modified_after:
                return False
            if self.modified_before and mtime > self.modified_before:
                return False
            
            # Creation time
            ctime = datetime.fromtimestamp(stat.st_ctime)
            if self.created_after and ctime < self.created_after:
                return False
            if self.created_before and ctime > self.created_before:
                return False
            
            # Path patterns
            path_str = str(file_path)
            if self.path_contains and self.path_contains not in path_str:
                return False
            if self.path_not_contains and self.path_not_contains in path_str:
                return False
            
            # Exclude directories
            if self.exclude_dirs:
                for dir_name in self.exclude_dirs:
                    if dir_name in file_path.parts:
                        return False
            
            return True
        except (PermissionError, OSError):
            return False


@dataclass
class SearchResult:
    """Search operation result."""
    query: str
    is_regex: bool
    search_type: str
    total_matches: int
    files_searched: int
    search_time_ms: int
    matches: List[SearchMatch] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'query': self.query,
            'is_regex': self.is_regex,
            'search_type': self.search_type,
            'total_matches': self.total_matches,
            'files_searched': self.files_searched,
            'search_time_ms': self.search_time_ms,
            'matches': [m.to_dict() for m in self.matches],
            'errors': self.errors,
        }


class SearchEngine:
    """
    Advanced search engine with regex, content search, and filtering.
    """
    
    # Default directories to exclude
    DEFAULT_EXCLUDE_DIRS = [
        'node_modules', 'vendor', '.git', '.svn', '__pycache__',
        '.idea', '.vscode', 'venv', '.venv', 'build', 'dist',
    ]
    
    # Default binary extensions to skip for content search
    BINARY_EXTENSIONS = {
        '.exe', '.dll', '.so', '.dylib', '.bin', '.obj', '.o',
        '.png', '.jpg', '.jpeg', '.gif', '.bmp', '.ico', '.svg',
        '.mp3', '.mp4', '.avi', '.mkv', '.mov', '.wav', '.flac',
        '.zip', '.tar', '.gz', '.rar', '.7z', '.bz2',
        '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx',
        '.pyc', '.pyo', '.class', '.jar', '.war',
    }
    
    def __init__(self, max_workers: int = 4):
        """
        Initialize search engine.
        
        Args:
            max_workers: Number of parallel workers
        """
        self.max_workers = max_workers
        self._cancel_flag = False
    
    def search_filename(self,
                       search_path: Path,
                       pattern: str,
                       is_regex: bool = False,
                       case_sensitive: bool = False,
                       filters: Optional[SearchFilter] = None) -> SearchResult:
        """
        Search for files by filename pattern.
        
        Args:
            search_path: Path to search
            pattern: Search pattern (glob or regex)
            is_regex: Use regex matching
            case_sensitive: Case sensitive search
            filters: Optional search filters
            
        Returns:
            SearchResult
        """
        import time
        start_time = time.time()
        
        matches: List[SearchMatch] = []
        files_searched = 0
        errors: List[str] = []
        
        filters = filters or SearchFilter()
        if not filters.exclude_dirs:
            filters.exclude_dirs = self.DEFAULT_EXCLUDE_DIRS
        
        # Compile pattern
        if is_regex:
            flags = 0 if case_sensitive else re.IGNORECASE
            try:
                regex = re.compile(pattern, flags)
            except re.error as e:
                return SearchResult(
                    query=pattern,
                    is_regex=True,
                    search_type='filename',
                    total_matches=0,
                    files_searched=0,
                    search_time_ms=0,
                    errors=[f"Invalid regex: {e}"]
                )
        else:
            if not case_sensitive:
                pattern = pattern.lower()
        
        for file_path in search_path.rglob('*'):
            if self._cancel_flag:
                break
            
            if not file_path.is_file():
                continue
            
            try:
                stat = file_path.stat()
                if not filters.matches(file_path, stat):
                    continue
                
                files_searched += 1
                filename = file_path.name
                
                # Match check
                if is_regex:
                    if regex.search(filename):
                        matches.append(SearchMatch(
                            path=str(file_path),
                            filename=filename,
                            match_text=filename,
                            match_type='filename'
                        ))
                else:
                    target = filename if case_sensitive else filename.lower()
                    if fnmatch.fnmatch(target, f'*{pattern}*'):
                        matches.append(SearchMatch(
                            path=str(file_path),
                            filename=filename,
                            match_text=filename,
                            match_type='filename'
                        ))
            except (PermissionError, OSError) as e:
                errors.append(f"Error accessing {file_path}: {e}")
        
        elapsed = int((time.time() - start_time) * 1000)
        
        return SearchResult(
            query=pattern,
            is_regex=is_regex,
            search_type='filename',
            total_matches=len(matches),
            files_searched=files_searched,
            search_time_ms=elapsed,
            matches=matches,
            errors=errors
        )
    
    def search_content(self,
                       search_path: Path,
                       pattern: str,
                       is_regex: bool = True,
                       case_sensitive: bool = False,
                       filters: Optional[SearchFilter] = None,
                       context_lines: int = 0,
                       max_matches_per_file: int = 100) -> SearchResult:
        """
        Search for pattern in file contents.
        
        Args:
            search_path: Path to search
            pattern: Search pattern
            is_regex: Use regex matching
            case_sensitive: Case sensitive search
            filters: Optional filters
            context_lines: Number of context lines around match
            max_matches_per_file: Max matches per file
            
        Returns:
            SearchResult
        """
        import time
        start_time = time.time()
        
        all_matches: List[SearchMatch] = []
        files_searched = 0
        errors: List[str] = []
        
        filters = filters or SearchFilter()
        if not filters.exclude_dirs:
            filters.exclude_dirs = self.DEFAULT_EXCLUDE_DIRS
        
        # Compile pattern
        flags = 0 if case_sensitive else re.IGNORECASE
        try:
            regex = re.compile(pattern, flags)
        except re.error as e:
            return SearchResult(
                query=pattern,
                is_regex=is_regex,
                search_type='content',
                total_matches=0,
                files_searched=0,
                search_time_ms=0,
                errors=[f"Invalid regex: {e}"]
            )
        
        # Collect files to search
        files_to_search = []
        for file_path in search_path.rglob('*'):
            if not file_path.is_file():
                continue
            
            # Skip binary files
            if file_path.suffix.lower() in self.BINARY_EXTENSIONS:
                continue
            
            try:
                stat = file_path.stat()
                if filters.matches(file_path, stat):
                    files_to_search.append(file_path)
            except (PermissionError, OSError):
                pass
        
        # Search in parallel
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {
                executor.submit(
                    self._search_file_content,
                    file_path,
                    regex,
                    context_lines,
                    max_matches_per_file
                ): file_path
                for file_path in files_to_search
            }
            
            for future in as_completed(futures):
                if self._cancel_flag:
                    break
                
                file_path = futures[future]
                files_searched += 1
                
                try:
                    file_matches = future.result()
                    all_matches.extend(file_matches)
                except Exception as e:
                    errors.append(f"Error searching {file_path}: {e}")
        
        elapsed = int((time.time() - start_time) * 1000)
        
        return SearchResult(
            query=pattern,
            is_regex=is_regex,
            search_type='content',
            total_matches=len(all_matches),
            files_searched=files_searched,
            search_time_ms=elapsed,
            matches=all_matches,
            errors=errors
        )
    
    def _search_file_content(self,
                             file_path: Path,
                             regex: re.Pattern,
                             context_lines: int,
                             max_matches: int) -> List[SearchMatch]:
        """Search content of a single file."""
        matches = []
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
            
            match_count = 0
            for line_num, line in enumerate(lines, 1):
                if match_count >= max_matches:
                    break
                
                for match in regex.finditer(line):
                    if match_count >= max_matches:
                        break
                    
                    # Get context
                    context = ''
                    if context_lines > 0:
                        start = max(0, line_num - 1 - context_lines)
                        end = min(len(lines), line_num + context_lines)
                        context_lines_list = lines[start:end]
                        context = ''.join(context_lines_list).strip()
                    
                    matches.append(SearchMatch(
                        path=str(file_path),
                        filename=file_path.name,
                        line_number=line_num,
                        column=match.start() + 1,
                        context=context or line.strip(),
                        match_text=match.group(),
                        match_type='content'
                    ))
                    match_count += 1
        except Exception:
            pass
        
        return matches
    
    def search_todos(self, 
                     search_path: Path,
                     patterns: Optional[List[str]] = None,
                     filters: Optional[SearchFilter] = None) -> SearchResult:
        """
        Search for TODO, FIXME, and similar markers.
        
        Args:
            search_path: Path to search
            patterns: Custom patterns (default: TODO, FIXME, HACK, XXX)
            filters: Optional filters
            
        Returns:
            SearchResult
        """
        if patterns is None:
            patterns = ['TODO', 'FIXME', 'HACK', 'XXX', 'BUG', 'OPTIMIZE']
        
        pattern = r'\b(' + '|'.join(patterns) + r')\b[:\s]?.*'
        
        return self.search_content(
            search_path,
            pattern,
            is_regex=True,
            case_sensitive=False,
            filters=filters
        )
    
    def find_large_files(self,
                         search_path: Path,
                         min_size_mb: float = 10,
                         limit: int = 50) -> List[Dict[str, Any]]:
        """
        Find large files.
        
        Args:
            search_path: Path to search
            min_size_mb: Minimum size in MB
            limit: Maximum results
            
        Returns:
            List of file info dicts
        """
        min_bytes = int(min_size_mb * 1024 * 1024)
        large_files = []
        
        for file_path in search_path.rglob('*'):
            if not file_path.is_file():
                continue
            
            try:
                size = file_path.stat().st_size
                if size >= min_bytes:
                    large_files.append({
                        'path': str(file_path),
                        'filename': file_path.name,
                        'size': size,
                        'size_mb': round(size / (1024 * 1024), 2),
                    })
            except (PermissionError, OSError):
                pass
        
        # Sort by size descending
        large_files.sort(key=lambda x: x['size'], reverse=True)
        
        return large_files[:limit]
    
    def find_recently_modified(self,
                               search_path: Path,
                               days: int = 7,
                               limit: int = 50) -> List[Dict[str, Any]]:
        """
        Find recently modified files.
        
        Args:
            search_path: Path to search
            days: Modified within this many days
            limit: Maximum results
            
        Returns:
            List of file info dicts
        """
        cutoff = datetime.now() - timedelta(days=days)
        recent_files = []
        
        for file_path in search_path.rglob('*'):
            if not file_path.is_file():
                continue
            
            try:
                stat = file_path.stat()
                mtime = datetime.fromtimestamp(stat.st_mtime)
                if mtime >= cutoff:
                    recent_files.append({
                        'path': str(file_path),
                        'filename': file_path.name,
                        'modified': mtime.isoformat(),
                        'size': stat.st_size,
                    })
            except (PermissionError, OSError):
                pass
        
        # Sort by modification time descending
        recent_files.sort(key=lambda x: x['modified'], reverse=True)
        
        return recent_files[:limit]
    
    def find_by_extension(self,
                          search_path: Path,
                          extensions: List[str]) -> Dict[str, List[str]]:
        """
        Group files by extension.
        
        Args:
            search_path: Path to search
            extensions: Extensions to find
            
        Returns:
            Dict mapping extension to file paths
        """
        result: Dict[str, List[str]] = {ext: [] for ext in extensions}
        
        for file_path in search_path.rglob('*'):
            if not file_path.is_file():
                continue
            
            ext = file_path.suffix.lower()
            if ext in extensions:
                result[ext].append(str(file_path))
        
        return result
    
    def cancel(self):
        """Cancel ongoing search."""
        self._cancel_flag = True
    
    def reset(self):
        """Reset cancel flag."""
        self._cancel_flag = False


# Singleton instance
search_engine = SearchEngine()
