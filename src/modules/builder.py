"""
Stracture-Master - Builder Module
Builds project structure from parsed input.
Features:
- Create directories and files
- Handle conflicts with force/dry-run modes
- Multi-threaded file creation
- Rollback on errors
"""

import os
import shutil
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple, Callable
from dataclasses import dataclass, field
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

from .logger import Logger


@dataclass
class BuildOperation:
    """Represents a single build operation."""
    operation: str  # 'create_dir', 'create_file', 'skip', 'overwrite'
    path: str
    success: bool = False
    error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'operation': self.operation,
            'path': self.path,
            'success': self.success,
            'error': self.error,
        }


@dataclass
class BuildResult:
    """Result of build operation."""
    success: bool
    output_path: str = ''
    operations: List[BuildOperation] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    stats: Dict[str, int] = field(default_factory=lambda: {
        'directories_created': 0,
        'files_created': 0,
        'items_skipped': 0,
        'items_overwritten': 0,
        'errors': 0,
        'build_time_ms': 0,
    })
    
    @property
    def created_paths(self) -> List[str]:
        return [op.path for op in self.operations 
                if op.success and op.operation in ('create_dir', 'create_file')]


class StructureBuilder:
    """
    Builds project structure from a structure dictionary.
    """
    
    def __init__(self, max_workers: Optional[int] = None):
        """
        Initialize builder.
        
        Args:
            max_workers: Maximum threads for parallel creation
        """
        self.logger = Logger.get_instance()
        self.max_workers = max_workers or os.cpu_count() or 4
        
        # Progress callback
        self._progress_callback: Optional[Callable[[int, int, str], None]] = None
        
        # Thread safety
        self._lock = threading.Lock()
        
        # Created paths for potential rollback
        self._created_paths: List[Path] = []
    
    def build(self,
              structure: Dict[str, Any],
              output_path: Optional[Path] = None,
              force: bool = False,
              dry_run: bool = False,
              create_root: bool = True) -> BuildResult:
        """
        Build project structure.
        
        Args:
            structure: Structure dictionary to build
            output_path: Output directory (default: 'root' in current dir)
            force: Overwrite existing files/directories
            dry_run: Preview without creating anything
            create_root: Create root directory if it doesn't exist
            
        Returns:
            BuildResult with operation details
        """
        start_time = datetime.now()
        
        # Set default output path
        if output_path is None:
            output_path = Path.cwd() / 'root'
        else:
            output_path = Path(output_path).resolve()
        
        result = BuildResult(
            success=True,
            output_path=str(output_path)
        )
        
        # Reset created paths for rollback
        self._created_paths = []
        
        try:
            # Create root directory if needed
            if create_root and not dry_run:
                if not output_path.exists():
                    output_path.mkdir(parents=True, exist_ok=True)
                    self._created_paths.append(output_path)
                    result.operations.append(BuildOperation(
                        operation='create_dir',
                        path=str(output_path),
                        success=True
                    ))
                    result.stats['directories_created'] += 1
                elif not output_path.is_dir():
                    result.success = False
                    result.errors.append(f"Output path exists but is not a directory: {output_path}")
                    return result
            
            # Build structure
            if dry_run:
                self._preview_build(structure, output_path, result, force)
            else:
                self._execute_build(structure, output_path, result, force)
                
        except Exception as e:
            result.success = False
            result.errors.append(f"Build failed: {str(e)}")
            
            # Rollback on failure
            if not dry_run and self._created_paths:
                self._rollback(result)
        
        # Calculate build time
        end_time = datetime.now()
        result.stats['build_time_ms'] = int((end_time - start_time).total_seconds() * 1000)
        
        return result
    
    def _preview_build(self, structure: Dict[str, Any], base_path: Path,
                       result: BuildResult, force: bool,
                       current_path: str = '') -> None:
        """Preview build operations without executing."""
        for name, content in structure.items():
            full_path = base_path / name
            display_path = f"{current_path}/{name}" if current_path else name
            
            is_directory = isinstance(content, dict)
            
            if full_path.exists():
                if force:
                    operation = 'overwrite'
                    result.stats['items_overwritten'] += 1
                else:
                    operation = 'skip'
                    result.stats['items_skipped'] += 1
                    result.warnings.append(f"Would skip (exists): {display_path}")
            else:
                operation = 'create_dir' if is_directory else 'create_file'
                if is_directory:
                    result.stats['directories_created'] += 1
                else:
                    result.stats['files_created'] += 1
            
            result.operations.append(BuildOperation(
                operation=operation,
                path=str(full_path),
                success=True  # In preview mode, all operations "succeed"
            ))
            
            # Recurse into directories
            if is_directory and content:
                self._preview_build(content, full_path, result, force, display_path)
    
    def _execute_build(self, structure: Dict[str, Any], base_path: Path,
                       result: BuildResult, force: bool,
                       current_path: str = '') -> None:
        """Execute build operations."""
        total_items = self._count_items(structure)
        processed = 0
        
        def process_item(item: Tuple[str, Any, Path, str]) -> BuildOperation:
            name, content, parent, display = item
            full_path = parent / name
            is_directory = isinstance(content, dict)
            
            try:
                # Handle existing paths
                if full_path.exists():
                    if not force:
                        return BuildOperation(
                            operation='skip',
                            path=str(full_path),
                            success=True
                        )
                    else:
                        # Remove existing for overwrite
                        if full_path.is_dir():
                            shutil.rmtree(full_path)
                        else:
                            full_path.unlink()
                
                # Create directory or file
                if is_directory:
                    full_path.mkdir(parents=True, exist_ok=True)
                    self._created_paths.append(full_path)
                    return BuildOperation(
                        operation='create_dir',
                        path=str(full_path),
                        success=True
                    )
                else:
                    full_path.parent.mkdir(parents=True, exist_ok=True)
                    full_path.touch()
                    self._created_paths.append(full_path)
                    return BuildOperation(
                        operation='create_file',
                        path=str(full_path),
                        success=True
                    )
                    
            except Exception as e:
                return BuildOperation(
                    operation='create_dir' if is_directory else 'create_file',
                    path=str(full_path),
                    success=False,
                    error=str(e)
                )
        
        # Collect all items to process
        items_to_process = []
        self._collect_items(structure, base_path, '', items_to_process)
        
        # Process items
        if len(items_to_process) > 20 and self.max_workers > 1:
            # Parallel processing for large structures
            # Note: We need to process directories before files
            dirs = [(n, c, p, d) for n, c, p, d in items_to_process if isinstance(c, dict)]
            files = [(n, c, p, d) for n, c, p, d in items_to_process if not isinstance(c, dict)]
            
            # Create directories first (sequentially to ensure parents exist)
            for item in dirs:
                op = process_item(item)
                self._record_operation(op, result)
                processed += 1
                if self._progress_callback:
                    self._progress_callback(processed, total_items, item[0])
            
            # Create files in parallel
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                futures = {executor.submit(process_item, item): item for item in files}
                for future in as_completed(futures):
                    op = future.result()
                    with self._lock:
                        self._record_operation(op, result)
                        processed += 1
                        if self._progress_callback:
                            self._progress_callback(processed, total_items, futures[future][0])
        else:
            # Sequential processing
            for item in items_to_process:
                op = process_item(item)
                self._record_operation(op, result)
                processed += 1
                if self._progress_callback:
                    self._progress_callback(processed, total_items, item[0])
    
    def _collect_items(self, structure: Dict[str, Any], base_path: Path,
                       current_path: str,
                       items: List[Tuple[str, Any, Path, str]]) -> None:
        """Collect all items to process."""
        for name, content in structure.items():
            display = f"{current_path}/{name}" if current_path else name
            items.append((name, content, base_path, display))
            
            if isinstance(content, dict) and content:
                self._collect_items(content, base_path / name, display, items)
    
    def _count_items(self, structure: Dict[str, Any]) -> int:
        """Count total items in structure."""
        count = 0
        for name, content in structure.items():
            count += 1
            if isinstance(content, dict) and content:
                count += self._count_items(content)
        return count
    
    def _record_operation(self, op: BuildOperation, result: BuildResult) -> None:
        """Record an operation result."""
        result.operations.append(op)
        
        if not op.success:
            result.stats['errors'] += 1
            if op.error:
                result.errors.append(f"{op.path}: {op.error}")
        else:
            if op.operation == 'create_dir':
                result.stats['directories_created'] += 1
            elif op.operation == 'create_file':
                result.stats['files_created'] += 1
            elif op.operation == 'skip':
                result.stats['items_skipped'] += 1
            elif op.operation == 'overwrite':
                result.stats['items_overwritten'] += 1
    
    def _rollback(self, result: BuildResult) -> None:
        """Rollback created files/directories on failure."""
        self.logger.warn("Rolling back created files...")
        
        # Remove in reverse order (files before directories)
        for path in reversed(self._created_paths):
            try:
                if path.is_file():
                    path.unlink()
                elif path.is_dir():
                    shutil.rmtree(path)
            except Exception as e:
                result.warnings.append(f"Rollback failed for {path}: {e}")
    
    def set_progress_callback(self, callback: Callable[[int, int, str], None]) -> None:
        """Set progress callback function."""
        self._progress_callback = callback


# Create singleton instance
builder = StructureBuilder()
