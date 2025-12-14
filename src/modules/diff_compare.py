"""
StructureMaster - Diff & Compare Module
Compares two project structures and generates diff reports.
"""

from pathlib import Path
from typing import Dict, Any, List, Optional, Set, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto

from .logger import Logger


class ChangeType(Enum):
    """Type of change detected."""
    ADDED = auto()
    REMOVED = auto()
    MODIFIED = auto()
    TYPE_CHANGED = auto()  # File became dir or vice versa
    UNCHANGED = auto()


@dataclass
class DiffItem:
    """Represents a single diff item."""
    path: str
    change_type: ChangeType
    old_value: Optional[Any] = None
    new_value: Optional[Any] = None
    details: str = ''
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'path': self.path,
            'change_type': self.change_type.name,
            'old_value': str(self.old_value) if self.old_value else None,
            'new_value': str(self.new_value) if self.new_value else None,
            'details': self.details,
        }


@dataclass
class DiffResult:
    """Result of diff operation."""
    has_differences: bool
    items: List[DiffItem] = field(default_factory=list)
    stats: Dict[str, int] = field(default_factory=lambda: {
        'added': 0,
        'removed': 0,
        'modified': 0,
        'type_changed': 0,
        'unchanged': 0,
        'total_old': 0,
        'total_new': 0,
    })
    old_path: str = ''
    new_path: str = ''
    comparison_time: str = field(default_factory=lambda: datetime.now().isoformat())
    
    @property
    def added_items(self) -> List[DiffItem]:
        return [i for i in self.items if i.change_type == ChangeType.ADDED]
    
    @property
    def removed_items(self) -> List[DiffItem]:
        return [i for i in self.items if i.change_type == ChangeType.REMOVED]
    
    @property
    def modified_items(self) -> List[DiffItem]:
        return [i for i in self.items if i.change_type == ChangeType.MODIFIED]


class DiffCompare:
    """
    Compares project structures and generates diff reports.
    """
    
    def __init__(self):
        """Initialize diff compare."""
        self.logger = Logger.get_instance()
    
    def compare_structures(self,
                          old_structure: Dict[str, Any],
                          new_structure: Dict[str, Any],
                          old_path: str = 'old',
                          new_path: str = 'new') -> DiffResult:
        """
        Compare two structure dictionaries.
        
        Args:
            old_structure: Old/original structure
            new_structure: New/updated structure
            old_path: Label for old structure
            new_path: Label for new structure
            
        Returns:
            DiffResult with all differences
        """
        result = DiffResult(
            has_differences=False,
            old_path=old_path,
            new_path=new_path
        )
        
        # Get all paths from both structures
        old_paths = self._get_all_paths(old_structure)
        new_paths = self._get_all_paths(new_structure)
        
        result.stats['total_old'] = len(old_paths)
        result.stats['total_new'] = len(new_paths)
        
        all_paths = old_paths | new_paths
        
        for path in sorted(all_paths):
            old_value = self._get_value_at_path(old_structure, path)
            new_value = self._get_value_at_path(new_structure, path)
            
            if path not in old_paths:
                # Added
                result.items.append(DiffItem(
                    path=path,
                    change_type=ChangeType.ADDED,
                    new_value=new_value,
                    details='New item added'
                ))
                result.stats['added'] += 1
                result.has_differences = True
                
            elif path not in new_paths:
                # Removed
                result.items.append(DiffItem(
                    path=path,
                    change_type=ChangeType.REMOVED,
                    old_value=old_value,
                    details='Item removed'
                ))
                result.stats['removed'] += 1
                result.has_differences = True
                
            else:
                # Exists in both - check for type changes
                old_is_dir = isinstance(old_value, dict)
                new_is_dir = isinstance(new_value, dict)
                
                if old_is_dir != new_is_dir:
                    result.items.append(DiffItem(
                        path=path,
                        change_type=ChangeType.TYPE_CHANGED,
                        old_value='directory' if old_is_dir else 'file',
                        new_value='directory' if new_is_dir else 'file',
                        details=f"Changed from {'directory' if old_is_dir else 'file'} to {'directory' if new_is_dir else 'file'}"
                    ))
                    result.stats['type_changed'] += 1
                    result.has_differences = True
                else:
                    result.stats['unchanged'] += 1
        
        return result
    
    def compare_directories(self,
                           old_dir: Path,
                           new_dir: Path) -> DiffResult:
        """
        Compare two directories.
        
        Args:
            old_dir: Path to old/original directory
            new_dir: Path to new/updated directory
            
        Returns:
            DiffResult with all differences
        """
        from .scanner import ProjectScanner
        
        scanner = ProjectScanner()
        
        # Scan both directories
        old_scan = scanner.scan(old_dir)
        new_scan = scanner.scan(new_dir)
        
        result = self.compare_structures(
            old_scan.structure,
            new_scan.structure,
            str(old_dir),
            str(new_dir)
        )
        
        # Add file size/hash comparisons for common files
        old_files = {f.relative_path: f for f in old_scan.files if f.is_file}
        new_files = {f.relative_path: f for f in new_scan.files if f.is_file}
        
        for path in old_files.keys() & new_files.keys():
            old_file = old_files[path]
            new_file = new_files[path]
            
            if old_file.size != new_file.size:
                result.items.append(DiffItem(
                    path=path,
                    change_type=ChangeType.MODIFIED,
                    old_value=f"{old_file.size} bytes",
                    new_value=f"{new_file.size} bytes",
                    details=f"Size changed by {new_file.size - old_file.size:+d} bytes"
                ))
                result.stats['modified'] += 1
                result.has_differences = True
        
        return result
    
    def _get_all_paths(self, structure: Dict[str, Any], prefix: str = '') -> Set[str]:
        """Get all paths from a structure."""
        paths = set()
        
        for name, content in structure.items():
            current_path = f"{prefix}/{name}" if prefix else name
            paths.add(current_path)
            
            if isinstance(content, dict) and content:
                paths.update(self._get_all_paths(content, current_path))
        
        return paths
    
    def _get_value_at_path(self, structure: Dict[str, Any], 
                          path: str) -> Optional[Any]:
        """Get value at a specific path in structure."""
        parts = path.split('/')
        current = structure
        
        for part in parts:
            if not isinstance(current, dict) or part not in current:
                return None
            current = current[part]
        
        return current
    
    def to_markdown(self, result: DiffResult) -> str:
        """Convert diff result to Markdown format."""
        lines = [
            "# Structure Comparison Report",
            "",
            f"**Comparison Time:** {result.comparison_time}",
            f"**Old:** {result.old_path}",
            f"**New:** {result.new_path}",
            "",
            "## Summary",
            "",
            f"| Metric | Count |",
            f"|--------|-------|",
            f"| Added | {result.stats['added']} |",
            f"| Removed | {result.stats['removed']} |",
            f"| Modified | {result.stats['modified']} |",
            f"| Type Changed | {result.stats['type_changed']} |",
            f"| Unchanged | {result.stats['unchanged']} |",
            "",
        ]
        
        if result.added_items:
            lines.extend([
                "## ➕ Added Items",
                "",
                *[f"- `{item.path}`" for item in result.added_items],
                "",
            ])
        
        if result.removed_items:
            lines.extend([
                "## ➖ Removed Items",
                "",
                *[f"- `{item.path}`" for item in result.removed_items],
                "",
            ])
        
        if result.modified_items:
            lines.extend([
                "## 📝 Modified Items",
                "",
                *[f"- `{item.path}` - {item.details}" for item in result.modified_items],
                "",
            ])
        
        return '\n'.join(lines)
    
    def to_json(self, result: DiffResult) -> str:
        """Convert diff result to JSON format."""
        import json
        
        data = {
            'comparison_time': result.comparison_time,
            'old_path': result.old_path,
            'new_path': result.new_path,
            'has_differences': result.has_differences,
            'stats': result.stats,
            'items': [item.to_dict() for item in result.items],
        }
        
        return json.dumps(data, indent=2, ensure_ascii=False)
    
    def to_html(self, result: DiffResult) -> str:
        """Convert diff result to HTML format."""
        import html
        
        added_html = ''.join([
            f'<div class="item added">➕ {html.escape(item.path)}</div>'
            for item in result.added_items
        ])
        
        removed_html = ''.join([
            f'<div class="item removed">➖ {html.escape(item.path)}</div>'
            for item in result.removed_items
        ])
        
        modified_html = ''.join([
            f'<div class="item modified">📝 {html.escape(item.path)}<br><small>{html.escape(item.details)}</small></div>'
            for item in result.modified_items
        ])
        
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Structure Comparison Report</title>
    <style>
        body {{
            font-family: 'Segoe UI', system-ui, sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            color: #e5e5e5;
            padding: 40px;
            margin: 0;
            min-height: 100vh;
        }}
        .container {{
            max-width: 1000px;
            margin: 0 auto;
        }}
        h1 {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}
        .stats {{
            display: flex;
            gap: 20px;
            margin: 20px 0;
            flex-wrap: wrap;
        }}
        .stat {{
            background: rgba(255,255,255,0.05);
            padding: 15px 25px;
            border-radius: 8px;
        }}
        .stat-value {{
            font-size: 1.5em;
            font-weight: bold;
        }}
        .stat.added .stat-value {{ color: #4ade80; }}
        .stat.removed .stat-value {{ color: #f87171; }}
        .stat.modified .stat-value {{ color: #fbbf24; }}
        .section {{
            background: rgba(255,255,255,0.03);
            border-radius: 8px;
            padding: 20px;
            margin: 20px 0;
        }}
        .section h2 {{
            margin-top: 0;
        }}
        .item {{
            padding: 10px;
            margin: 5px 0;
            border-radius: 4px;
            font-family: monospace;
        }}
        .item.added {{ background: rgba(74, 222, 128, 0.1); border-left: 3px solid #4ade80; }}
        .item.removed {{ background: rgba(248, 113, 113, 0.1); border-left: 3px solid #f87171; }}
        .item.modified {{ background: rgba(251, 191, 36, 0.1); border-left: 3px solid #fbbf24; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🔄 Structure Comparison Report</h1>
        <p><strong>Old:</strong> {html.escape(result.old_path)}<br>
           <strong>New:</strong> {html.escape(result.new_path)}</p>
        
        <div class="stats">
            <div class="stat added"><div class="stat-value">{result.stats['added']}</div>Added</div>
            <div class="stat removed"><div class="stat-value">{result.stats['removed']}</div>Removed</div>
            <div class="stat modified"><div class="stat-value">{result.stats['modified']}</div>Modified</div>
        </div>
        
        <div class="section">
            <h2>Changes</h2>
            {added_html}
            {removed_html}
            {modified_html}
        </div>
    </div>
</body>
</html>
"""


# Create singleton instance
diff_compare = DiffCompare()
