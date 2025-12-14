"""
StructureMaster - Content Extractor Module
Extracts file contents with full metadata.
Features:
- Encoding auto-detection
- Binary file detection
- Metadata extraction (size, dates, MIME, SHA-256, permissions)
- Multi-threaded extraction
"""

import os
import hashlib
import mimetypes
import stat
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple, Generator, Callable
from dataclasses import dataclass, field
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
import chardet

from ..config import Config
from .logger import Logger
from .scanner import FileInfo


@dataclass
class FileContent:
    """Extracted file content with metadata."""
    path: str
    relative_path: str
    filename: str
    extension: str
    size: int
    mime_type: str
    sha256_hash: str
    permissions: str
    created_date: Optional[datetime]
    modified_date: Optional[datetime]
    encoding: str
    is_binary: bool
    content: Optional[str]  # None for binary files
    line_count: int = 0
    error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'path': self.path,
            'relative_path': self.relative_path,
            'filename': self.filename,
            'extension': self.extension,
            'size': self.size,
            'mime_type': self.mime_type,
            'sha256_hash': self.sha256_hash,
            'permissions': self.permissions,
            'created_date': self.created_date.isoformat() if self.created_date else None,
            'modified_date': self.modified_date.isoformat() if self.modified_date else None,
            'encoding': self.encoding,
            'is_binary': self.is_binary,
            'content': self.content,
            'line_count': self.line_count,
            'error': self.error,
        }
    
    def to_formatted_string(self) -> str:
        """Format as the specified output template."""
        size_str = f"{self.size:,} bytes"
        hash_str = self.sha256_hash or 'N/A'
        created = self.created_date.strftime('%Y-%m-%d %H:%M:%S') if self.created_date else 'N/A'
        modified = self.modified_date.strftime('%Y-%m-%d %H:%M:%S') if self.modified_date else 'N/A'
        
        header = f"""================================================================================
FILE: {self.filename}
PATH: {self.path}
TYPE: {self.extension.upper() if self.extension else 'UNKNOWN'}
SIZE: {size_str}
MIME: {self.mime_type}
SHA256: {hash_str}
PERMISSIONS: {self.permissions}
CREATED: {created}
MODIFIED: {modified}
================================================================================

"""
        if self.is_binary:
            content = "[Binary file - content not extracted]"
        elif self.error:
            content = f"[Error extracting content: {self.error}]"
        elif self.content:
            content = self.content
        else:
            content = "[Empty file]"
        
        return header + content + "\n\n"


@dataclass
class ExtractionResult:
    """Result of content extraction."""
    success: bool
    files: List[FileContent] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    stats: Dict[str, Any] = field(default_factory=lambda: {
        'total_files': 0,
        'extracted_files': 0,
        'binary_files': 0,
        'failed_files': 0,
        'total_size': 0,
        'total_lines': 0,
        'extraction_time_ms': 0,
    })


class ContentExtractor:
    """
    Extracts file contents with metadata.
    """
    
    def __init__(self, 
                 max_file_size_mb: float = 100,
                 max_workers: Optional[int] = None):
        """
        Initialize content extractor.
        
        Args:
            max_file_size_mb: Maximum file size to extract content from
            max_workers: Maximum threads for parallel extraction
        """
        self.logger = Logger.get_instance()
        self.max_file_size = int(max_file_size_mb * 1024 * 1024)
        self.max_workers = max_workers or Config.MAX_WORKERS
        
        # Progress callback
        self._progress_callback: Optional[Callable[[int, int, str], None]] = None
        
        # Extraction lock for thread safety
        self._lock = threading.Lock()
    
    def extract(self, 
                files: List[FileInfo],
                root_path: Optional[Path] = None,
                include_binary: bool = False,
                extract_content: bool = True) -> ExtractionResult:
        """
        Extract content from a list of files.
        
        Args:
            files: List of FileInfo objects to extract
            root_path: Root path for relative paths
            include_binary: Include binary files (metadata only)
            extract_content: Extract actual file content
            
        Returns:
            ExtractionResult with extracted content
        """
        start_time = datetime.now()
        result = ExtractionResult(success=True)
        
        # Filter to only files (not directories)
        file_list = [f for f in files if f.is_file]
        result.stats['total_files'] = len(file_list)
        
        if not file_list:
            return result
        
        # Use parallel extraction for large file counts
        if len(file_list) > 10 and self.max_workers > 1:
            self._extract_parallel(file_list, result, include_binary, extract_content)
        else:
            self._extract_sequential(file_list, result, include_binary, extract_content)
        
        # Calculate extraction time
        end_time = datetime.now()
        result.stats['extraction_time_ms'] = int((end_time - start_time).total_seconds() * 1000)
        
        return result
    
    def extract_single(self, filepath: Path, 
                       relative_to: Optional[Path] = None) -> FileContent:
        """
        Extract content from a single file.
        
        Args:
            filepath: Path to file
            relative_to: Base path for relative path calculation
            
        Returns:
            FileContent with extracted data
        """
        filepath = Path(filepath).resolve()
        
        if not filepath.exists():
            return FileContent(
                path=str(filepath),
                relative_path=str(filepath),
                filename=filepath.name,
                extension=filepath.suffix.lower(),
                size=0,
                mime_type='application/octet-stream',
                sha256_hash='',
                permissions='',
                created_date=None,
                modified_date=None,
                encoding='',
                is_binary=False,
                content=None,
                error="File not found"
            )
        
        # Calculate relative path
        if relative_to:
            try:
                rel_path = str(filepath.relative_to(relative_to)).replace('\\', '/')
            except ValueError:
                rel_path = str(filepath)
        else:
            rel_path = str(filepath)
        
        # Get file stats
        try:
            stat_info = filepath.stat()
            size = stat_info.st_size
            created = datetime.fromtimestamp(stat_info.st_ctime)
            modified = datetime.fromtimestamp(stat_info.st_mtime)
            permissions = self._format_permissions(stat_info.st_mode)
        except Exception as e:
            return FileContent(
                path=str(filepath),
                relative_path=rel_path,
                filename=filepath.name,
                extension=filepath.suffix.lower(),
                size=0,
                mime_type='application/octet-stream',
                sha256_hash='',
                permissions='',
                created_date=None,
                modified_date=None,
                encoding='',
                is_binary=False,
                content=None,
                error=f"Cannot read file stats: {e}"
            )
        
        # Get MIME type
        mime_type, _ = mimetypes.guess_type(str(filepath))
        if not mime_type:
            mime_type = Config.get_mime_type(str(filepath))
        
        # Check if binary
        is_binary = self._is_binary(filepath)
        
        # Calculate hash
        sha256_hash = self._calculate_hash(filepath)
        
        # Extract content if not binary and within size limit
        content = None
        encoding = ''
        line_count = 0
        error = None
        
        if not is_binary and size <= self.max_file_size:
            try:
                content, encoding = self._read_file_content(filepath)
                line_count = content.count('\n') + 1 if content else 0
            except Exception as e:
                error = f"Error reading content: {e}"
        elif is_binary:
            encoding = 'binary'
        elif size > self.max_file_size:
            error = f"File too large ({size:,} bytes > {self.max_file_size:,} bytes limit)"
        
        return FileContent(
            path=str(filepath),
            relative_path=rel_path,
            filename=filepath.name,
            extension=filepath.suffix.lower().lstrip('.'),
            size=size,
            mime_type=mime_type,
            sha256_hash=sha256_hash,
            permissions=permissions,
            created_date=created,
            modified_date=modified,
            encoding=encoding,
            is_binary=is_binary,
            content=content,
            line_count=line_count,
            error=error
        )
    
    def _extract_sequential(self, files: List[FileInfo], result: ExtractionResult,
                           include_binary: bool, extract_content: bool) -> None:
        """Extract files sequentially."""
        for i, file_info in enumerate(files):
            try:
                # Skip binary if not included
                if file_info.is_binary and not include_binary:
                    result.stats['binary_files'] += 1
                    continue
                
                filepath = Path(file_info.path)
                content = self.extract_single(filepath)
                
                # Don't extract content if flag is False
                if not extract_content:
                    content.content = None
                
                result.files.append(content)
                result.stats['extracted_files'] += 1
                result.stats['total_size'] += content.size
                result.stats['total_lines'] += content.line_count
                
                if content.is_binary:
                    result.stats['binary_files'] += 1
                
                if content.error:
                    result.warnings.append(f"{file_info.path}: {content.error}")
                
                # Progress callback
                if self._progress_callback:
                    self._progress_callback(i + 1, len(files), file_info.name)
                    
            except Exception as e:
                result.stats['failed_files'] += 1
                result.errors.append(f"Error extracting {file_info.path}: {e}")
    
    def _extract_parallel(self, files: List[FileInfo], result: ExtractionResult,
                         include_binary: bool, extract_content: bool) -> None:
        """Extract files in parallel."""
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all tasks
            future_to_file = {
                executor.submit(self._extract_file_task, f, include_binary, extract_content): f
                for f in files
            }
            
            completed = 0
            for future in as_completed(future_to_file):
                file_info = future_to_file[future]
                completed += 1
                
                try:
                    content, should_include = future.result()
                    
                    if should_include and content:
                        with self._lock:
                            result.files.append(content)
                            result.stats['extracted_files'] += 1
                            result.stats['total_size'] += content.size
                            result.stats['total_lines'] += content.line_count
                            
                            if content.is_binary:
                                result.stats['binary_files'] += 1
                            
                            if content.error:
                                result.warnings.append(f"{file_info.path}: {content.error}")
                    
                    # Progress callback
                    if self._progress_callback:
                        self._progress_callback(completed, len(files), file_info.name)
                        
                except Exception as e:
                    with self._lock:
                        result.stats['failed_files'] += 1
                        result.errors.append(f"Error extracting {file_info.path}: {e}")
    
    def _extract_file_task(self, file_info: FileInfo, 
                          include_binary: bool,
                          extract_content: bool) -> Tuple[Optional[FileContent], bool]:
        """Task for parallel extraction."""
        # Skip binary if not included
        if file_info.is_binary and not include_binary:
            return None, False
        
        filepath = Path(file_info.path)
        content = self.extract_single(filepath)
        
        # Don't extract content if flag is False
        if not extract_content:
            content.content = None
        
        return content, True
    
    def _is_binary(self, filepath: Path) -> bool:
        """Check if file is binary."""
        # First check by extension
        if Config.is_binary_file(str(filepath)):
            return True
        
        # Then check content
        try:
            with open(filepath, 'rb') as f:
                chunk = f.read(8192)
                if b'\x00' in chunk:
                    return True
                # High ratio of non-printable characters
                text_chars = bytearray({7, 8, 9, 10, 12, 13, 27} | set(range(0x20, 0x100)))
                non_text = sum(1 for byte in chunk if byte not in text_chars)
                return len(chunk) > 0 and (non_text / len(chunk)) > 0.30
        except Exception:
            return True
    
    def _calculate_hash(self, filepath: Path) -> str:
        """Calculate SHA-256 hash of file."""
        sha256 = hashlib.sha256()
        try:
            with open(filepath, 'rb') as f:
                for chunk in iter(lambda: f.read(8192), b''):
                    sha256.update(chunk)
            return sha256.hexdigest()
        except Exception:
            return ''
    
    def _read_file_content(self, filepath: Path) -> Tuple[str, str]:
        """Read file content with encoding detection."""
        # Detect encoding
        try:
            with open(filepath, 'rb') as f:
                raw = f.read(10000)
                result = chardet.detect(raw)
                encoding = result.get('encoding', 'utf-8') or 'utf-8'
        except Exception:
            encoding = 'utf-8'
        
        # Read content
        try:
            with open(filepath, 'r', encoding=encoding, errors='replace') as f:
                content = f.read()
            return content, encoding
        except Exception:
            # Fallback to binary read
            with open(filepath, 'rb') as f:
                raw = f.read()
                content = raw.decode(encoding, errors='replace')
            return content, encoding
    
    def _format_permissions(self, mode: int) -> str:
        """Format file permissions as Unix-style string."""
        perms = ''
        for who in ['USR', 'GRP', 'OTH']:
            for perm, char in [('R', 'r'), ('W', 'w'), ('X', 'x')]:
                if mode & getattr(stat, f'S_I{perm}{who}', 0):
                    perms += char
                else:
                    perms += '-'
        return perms
    
    def set_progress_callback(self, callback: Callable[[int, int, str], None]) -> None:
        """Set progress callback function."""
        self._progress_callback = callback
    
    def set_max_file_size(self, size_mb: float) -> None:
        """Set maximum file size for content extraction."""
        self.max_file_size = int(size_mb * 1024 * 1024)


# Create singleton instance
content_extractor = ContentExtractor()
