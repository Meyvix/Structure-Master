"""
Stracture-Master - Statistics Module
Advanced project statistics and analysis.
"""

from pathlib import Path
from typing import Dict, Any, List, Optional, Set
from dataclasses import dataclass, field
from datetime import datetime
from collections import Counter, defaultdict
import mimetypes
import hashlib


@dataclass
class FileTypeStats:
    """Statistics for a file type."""
    extension: str
    count: int = 0
    total_size: int = 0
    total_lines: int = 0
    avg_size: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'extension': self.extension,
            'count': self.count,
            'total_size': self.total_size,
            'total_lines': self.total_lines,
            'avg_size': round(self.avg_size, 2),
        }


@dataclass
class DirectoryStats:
    """Statistics for a directory."""
    path: str
    file_count: int = 0
    dir_count: int = 0
    total_size: int = 0
    depth: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'path': self.path,
            'file_count': self.file_count,
            'dir_count': self.dir_count,
            'total_size': self.total_size,
            'depth': self.depth,
        }


@dataclass
class DuplicateGroup:
    """Group of duplicate files."""
    hash: str
    size: int
    files: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'hash': self.hash,
            'size': self.size,
            'count': len(self.files),
            'wasted_space': self.size * (len(self.files) - 1),
            'files': self.files,
        }


@dataclass
class ProjectAnalysis:
    """Complete project analysis."""
    project_path: str
    scan_time: datetime = field(default_factory=datetime.now)
    
    # File counts
    total_files: int = 0
    total_directories: int = 0
    total_size: int = 0
    max_depth: int = 0
    
    # By type
    file_types: Dict[str, FileTypeStats] = field(default_factory=dict)
    
    # By directory
    directories: List[DirectoryStats] = field(default_factory=list)
    
    # Largest files
    largest_files: List[Dict[str, Any]] = field(default_factory=list)
    
    # Duplicates
    duplicates: List[DuplicateGroup] = field(default_factory=list)
    duplicate_count: int = 0
    duplicate_wasted_size: int = 0
    
    # Time-based
    recently_modified: List[Dict[str, Any]] = field(default_factory=list)
    oldest_files: List[Dict[str, Any]] = field(default_factory=list)
    
    # Code metrics
    total_lines: int = 0
    code_lines: int = 0
    blank_lines: int = 0
    comment_lines: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'project_path': self.project_path,
            'scan_time': self.scan_time.isoformat(),
            'summary': {
                'total_files': self.total_files,
                'total_directories': self.total_directories,
                'total_size': self.total_size,
                'total_size_formatted': self._format_size(self.total_size),
                'max_depth': self.max_depth,
            },
            'by_type': {ext: s.to_dict() for ext, s in self.file_types.items()},
            'largest_files': self.largest_files[:10],
            'duplicates': {
                'count': self.duplicate_count,
                'wasted_size': self.duplicate_wasted_size,
                'groups': [d.to_dict() for d in self.duplicates[:10]],
            },
            'code_metrics': {
                'total_lines': self.total_lines,
                'code_lines': self.code_lines,
                'blank_lines': self.blank_lines,
                'comment_lines': self.comment_lines,
            },
        }
    
    def _format_size(self, size: int) -> str:
        """Format size in human readable form."""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} PB"


class ProjectStatistics:
    """
    Advanced project statistics and analysis.
    """
    
    def __init__(self):
        """Initialize statistics analyzer."""
        self._file_hashes: Dict[str, List[str]] = defaultdict(list)
    
    def analyze(self, 
                project_path: Path,
                files: Optional[List[Dict[str, Any]]] = None) -> ProjectAnalysis:
        """
        Analyze a project directory.
        
        Args:
            project_path: Path to project
            files: Optional pre-scanned file list
            
        Returns:
            ProjectAnalysis object
        """
        analysis = ProjectAnalysis(project_path=str(project_path))
        
        if files:
            self._analyze_files(analysis, files)
        else:
            self._scan_and_analyze(analysis, project_path)
        
        return analysis
    
    def _scan_and_analyze(self, analysis: ProjectAnalysis, path: Path) -> None:
        """Scan directory and collect statistics."""
        files = []
        
        for item in path.rglob('*'):
            if item.is_file():
                try:
                    stat = item.stat()
                    files.append({
                        'path': str(item),
                        'name': item.name,
                        'size': stat.st_size,
                        'modified': datetime.fromtimestamp(stat.st_mtime),
                        'created': datetime.fromtimestamp(stat.st_ctime),
                        'extension': item.suffix.lower(),
                    })
                except (PermissionError, OSError):
                    pass
        
        self._analyze_files(analysis, files)
    
    def _analyze_files(self, analysis: ProjectAnalysis, files: List[Dict[str, Any]]) -> None:
        """Analyze list of files."""
        type_stats: Dict[str, FileTypeStats] = {}
        dir_files: Dict[str, int] = Counter()
        
        for f in files:
            analysis.total_files += 1
            size = f.get('size', 0)
            analysis.total_size += size
            
            # Extension stats
            ext = f.get('extension', '') or '(no ext)'
            if ext not in type_stats:
                type_stats[ext] = FileTypeStats(extension=ext)
            
            type_stats[ext].count += 1
            type_stats[ext].total_size += size
            type_stats[ext].total_lines += f.get('lines', 0)
            
            # Directory tracking
            path = Path(f.get('path', ''))
            parent = str(path.parent)
            dir_files[parent] += 1
            
            # Depth calculation
            depth = len(path.parts)
            if depth > analysis.max_depth:
                analysis.max_depth = depth
            
            # Hash for duplicates
            file_hash = f.get('hash')
            if file_hash:
                self._file_hashes[file_hash].append(str(path))
            
            # Lines if available
            analysis.total_lines += f.get('lines', 0)
            analysis.code_lines += f.get('code_lines', 0)
            analysis.blank_lines += f.get('blank_lines', 0)
            analysis.comment_lines += f.get('comment_lines', 0)
        
        # Calculate averages
        for ext, stats in type_stats.items():
            if stats.count > 0:
                stats.avg_size = stats.total_size / stats.count
        
        analysis.file_types = type_stats
        analysis.total_directories = len(dir_files)
        
        # Largest files
        sorted_by_size = sorted(files, key=lambda x: x.get('size', 0), reverse=True)
        analysis.largest_files = [
            {'path': f.get('path'), 'size': f.get('size')}
            for f in sorted_by_size[:20]
        ]
        
        # Recently modified
        sorted_by_time = sorted(
            files, 
            key=lambda x: x.get('modified', datetime.min), 
            reverse=True
        )
        analysis.recently_modified = [
            {'path': f.get('path'), 'modified': str(f.get('modified'))}
            for f in sorted_by_time[:10]
        ]
        
        # Duplicates
        for hash_val, paths in self._file_hashes.items():
            if len(paths) > 1:
                size = next((f.get('size', 0) for f in files if f.get('hash') == hash_val), 0)
                analysis.duplicates.append(DuplicateGroup(
                    hash=hash_val,
                    size=size,
                    files=paths
                ))
                analysis.duplicate_count += len(paths) - 1
                analysis.duplicate_wasted_size += size * (len(paths) - 1)
    
    def get_size_distribution(self, files: List[Dict[str, Any]]) -> Dict[str, int]:
        """
        Get file size distribution.
        
        Returns:
            Dict with size ranges and counts
        """
        distribution = {
            '< 1 KB': 0,
            '1-10 KB': 0,
            '10-100 KB': 0,
            '100 KB - 1 MB': 0,
            '1-10 MB': 0,
            '> 10 MB': 0,
        }
        
        for f in files:
            size = f.get('size', 0)
            if size < 1024:
                distribution['< 1 KB'] += 1
            elif size < 10 * 1024:
                distribution['1-10 KB'] += 1
            elif size < 100 * 1024:
                distribution['10-100 KB'] += 1
            elif size < 1024 * 1024:
                distribution['100 KB - 1 MB'] += 1
            elif size < 10 * 1024 * 1024:
                distribution['1-10 MB'] += 1
            else:
                distribution['> 10 MB'] += 1
        
        return distribution
    
    def get_type_distribution(self, analysis: ProjectAnalysis) -> Dict[str, int]:
        """Get file type distribution for charts."""
        return {
            ext: stats.count 
            for ext, stats in sorted(
                analysis.file_types.items(),
                key=lambda x: x[1].count,
                reverse=True
            )[:15]  # Top 15 types
        }
    
    def get_directory_sizes(self, project_path: Path, max_depth: int = 2) -> Dict[str, int]:
        """
        Get directory sizes for treemap.
        
        Args:
            project_path: Project path
            max_depth: Maximum depth to report
            
        Returns:
            Dict of directory paths and sizes
        """
        sizes: Dict[str, int] = defaultdict(int)
        
        for item in project_path.rglob('*'):
            if item.is_file():
                try:
                    size = item.stat().st_size
                    
                    # Add to each parent up to max_depth
                    rel_parts = item.relative_to(project_path).parts
                    for i in range(min(len(rel_parts), max_depth)):
                        partial_path = '/'.join(rel_parts[:i+1])
                        sizes[partial_path] += size
                except (PermissionError, OSError):
                    pass
        
        return dict(sizes)
    
    def find_duplicates(self, project_path: Path) -> List[DuplicateGroup]:
        """
        Find duplicate files by content hash.
        
        Args:
            project_path: Path to scan
            
        Returns:
            List of duplicate groups
        """
        hashes: Dict[str, List[str]] = defaultdict(list)
        sizes: Dict[str, int] = {}
        
        for item in project_path.rglob('*'):
            if item.is_file():
                try:
                    if item.stat().st_size > 10 * 1024 * 1024:  # Skip files > 10MB
                        continue
                    
                    file_hash = self._compute_hash(item)
                    hashes[file_hash].append(str(item))
                    sizes[file_hash] = item.stat().st_size
                except (PermissionError, OSError):
                    pass
        
        duplicates = []
        for hash_val, paths in hashes.items():
            if len(paths) > 1:
                duplicates.append(DuplicateGroup(
                    hash=hash_val,
                    size=sizes.get(hash_val, 0),
                    files=paths
                ))
        
        return sorted(duplicates, key=lambda x: x.size * len(x.files), reverse=True)
    
    def _compute_hash(self, file_path: Path, algorithm: str = 'sha256') -> str:
        """Compute file hash."""
        hasher = hashlib.new(algorithm)
        
        with open(file_path, 'rb') as f:
            while chunk := f.read(8192):
                hasher.update(chunk)
        
        return hasher.hexdigest()


# Singleton instance
statistics = ProjectStatistics()
