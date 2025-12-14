"""
StructureMaster - Exporter Module
Exports project structure and content to various formats.
Supports: TXT, JSON, Markdown, YAML, HTML, ZIP, tar.gz
Features: AES-256 encryption, customizable templates
"""

import os
import json
import zipfile
import tarfile
import shutil
import tempfile
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
import html

from ..config import Config, ExportFormat
from .logger import Logger
from .content_extractor import FileContent


@dataclass
class ExportResult:
    """Result of export operation."""
    success: bool
    output_path: str = ''
    format: str = ''
    encrypted: bool = False
    errors: List[str] = field(default_factory=list)
    stats: Dict[str, Any] = field(default_factory=lambda: {
        'files_exported': 0,
        'total_size': 0,
        'export_time_ms': 0,
    })


class Exporter:
    """
    Exports project data to various formats.
    """
    
    def __init__(self):
        """Initialize exporter."""
        self.logger = Logger.get_instance()
        self._security = None  # Lazy import to avoid circular dependency
    
    def export_structure(self,
                         structure: Dict[str, Any],
                         output_path: Path,
                         format: ExportFormat = ExportFormat.JSON,
                         pretty: bool = True) -> ExportResult:
        """
        Export structure to file.
        
        Args:
            structure: Structure dictionary
            output_path: Output file path
            format: Export format
            pretty: Pretty print (for JSON/YAML)
            
        Returns:
            ExportResult
        """
        start_time = datetime.now()
        result = ExportResult(
            success=True,
            output_path=str(output_path),
            format=format.value
        )
        
        try:
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            if format == ExportFormat.JSON:
                content = self._to_json(structure, pretty)
            elif format == ExportFormat.TXT:
                content = self._to_tree(structure)
            elif format == ExportFormat.MARKDOWN:
                content = self._to_markdown_structure(structure)
            elif format == ExportFormat.YAML:
                content = self._to_yaml(structure)
            elif format == ExportFormat.HTML:
                content = self._to_html_structure(structure)
            else:
                result.success = False
                result.errors.append(f"Unsupported format for structure export: {format}")
                return result
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            result.stats['total_size'] = len(content.encode('utf-8'))
            
        except Exception as e:
            result.success = False
            result.errors.append(f"Export failed: {str(e)}")
        
        end_time = datetime.now()
        result.stats['export_time_ms'] = int((end_time - start_time).total_seconds() * 1000)
        
        return result
    
    def export_content(self,
                       files: List[FileContent],
                       output_path: Path,
                       format: ExportFormat = ExportFormat.TXT,
                       encrypt: bool = False,
                       password: Optional[str] = None,
                       compress: bool = False) -> ExportResult:
        """
        Export file contents.
        
        Args:
            files: List of FileContent objects
            output_path: Output file path
            format: Export format
            encrypt: Enable encryption
            password: Encryption password
            compress: Create compressed archive
            
        Returns:
            ExportResult
        """
        start_time = datetime.now()
        result = ExportResult(
            success=True,
            output_path=str(output_path),
            format=format.value,
            encrypted=encrypt
        )
        
        try:
            output_path = Path(output_path)
            
            # Handle archive formats
            if format in (ExportFormat.ZIP, ExportFormat.TAR_GZ) or compress:
                return self._export_archive(files, output_path, format, encrypt, password)
            
            # Export to single file
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            if format == ExportFormat.JSON:
                content = self._files_to_json(files)
            elif format == ExportFormat.TXT:
                content = self._files_to_txt(files)
            elif format == ExportFormat.MARKDOWN:
                content = self._files_to_markdown(files)
            elif format == ExportFormat.YAML:
                content = self._files_to_yaml(files)
            elif format == ExportFormat.HTML:
                content = self._files_to_html(files)
            else:
                result.success = False
                result.errors.append(f"Unsupported format: {format}")
                return result
            
            # Encrypt if requested
            if encrypt and password:
                content = self._encrypt_content(content, password)
                result.encrypted = True
            
            # Write output
            write_mode = 'wb' if encrypt else 'w'
            encoding = None if encrypt else 'utf-8'
            
            with open(output_path, write_mode, encoding=encoding) as f:
                if encrypt:
                    f.write(content)
                else:
                    f.write(content)
            
            result.stats['files_exported'] = len(files)
            result.stats['total_size'] = output_path.stat().st_size
            
        except Exception as e:
            result.success = False
            result.errors.append(f"Export failed: {str(e)}")
        
        end_time = datetime.now()
        result.stats['export_time_ms'] = int((end_time - start_time).total_seconds() * 1000)
        
        return result
    
    def _export_archive(self,
                        files: List[FileContent],
                        output_path: Path,
                        format: ExportFormat,
                        encrypt: bool,
                        password: Optional[str]) -> ExportResult:
        """Export to archive format (ZIP or tar.gz)."""
        result = ExportResult(
            success=True,
            output_path=str(output_path),
            format=format.value,
            encrypted=encrypt
        )
        
        try:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            if format == ExportFormat.ZIP or str(output_path).endswith('.zip'):
                self._create_zip(files, output_path, encrypt, password)
            else:
                self._create_targz(files, output_path)
            
            result.stats['files_exported'] = len(files)
            result.stats['total_size'] = output_path.stat().st_size
            
        except Exception as e:
            result.success = False
            result.errors.append(f"Archive creation failed: {str(e)}")
        
        return result
    
    def _create_zip(self, files: List[FileContent], output_path: Path,
                    encrypt: bool, password: Optional[str]) -> None:
        """Create ZIP archive."""
        with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            for file in files:
                if file.content:
                    zf.writestr(file.relative_path, file.content)
            
            # Add metadata file
            metadata = {
                'created': datetime.now().isoformat(),
                'files': len(files),
                'encrypted': encrypt,
            }
            zf.writestr('_metadata.json', json.dumps(metadata, indent=2))
    
    def _create_targz(self, files: List[FileContent], output_path: Path) -> None:
        """Create tar.gz archive."""
        # Create temp directory with files
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            for file in files:
                if file.content:
                    file_path = temp_path / file.relative_path
                    file_path.parent.mkdir(parents=True, exist_ok=True)
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(file.content)
            
            # Create tar.gz
            with tarfile.open(output_path, 'w:gz') as tf:
                for item in temp_path.iterdir():
                    tf.add(item, arcname=item.name)
    
    def _to_json(self, data: Any, pretty: bool = True) -> str:
        """Convert data to JSON string."""
        indent = 2 if pretty else None
        return json.dumps(data, indent=indent, ensure_ascii=False, default=str)
    
    def _to_tree(self, structure: Dict[str, Any], prefix: str = '') -> str:
        """Convert structure to tree format."""
        lines = []
        items = sorted(structure.items(), 
                      key=lambda x: (not isinstance(x[1], dict), x[0].lower()))
        
        for i, (name, content) in enumerate(items):
            is_last = (i == len(items) - 1)
            connector = '└── ' if is_last else '├── '
            
            if isinstance(content, dict):
                lines.append(f"{prefix}{connector}{name}/")
                if content:
                    extension = '    ' if is_last else '│   '
                    lines.append(self._to_tree(content, prefix + extension))
            else:
                lines.append(f"{prefix}{connector}{name}")
        
        return '\n'.join(lines)
    
    def _to_yaml(self, data: Any) -> str:
        """Convert data to YAML string."""
        try:
            import yaml
            return yaml.dump(data, default_flow_style=False, allow_unicode=True)
        except ImportError:
            # Fallback to simple YAML-like format
            return self._simple_yaml(data)
    
    def _simple_yaml(self, data: Any, indent: int = 0) -> str:
        """Simple YAML serialization fallback."""
        lines = []
        prefix = '  ' * indent
        
        if isinstance(data, dict):
            for key, value in data.items():
                if isinstance(value, dict):
                    lines.append(f"{prefix}{key}:")
                    lines.append(self._simple_yaml(value, indent + 1))
                elif value is None:
                    lines.append(f"{prefix}{key}: null")
                else:
                    lines.append(f"{prefix}{key}: {value}")
        elif isinstance(data, list):
            for item in data:
                lines.append(f"{prefix}- {item}")
        
        return '\n'.join(lines)
    
    def _to_markdown_structure(self, structure: Dict[str, Any], 
                               level: int = 0) -> str:
        """Convert structure to Markdown."""
        lines = []
        
        if level == 0:
            lines.append("# Project Structure\n")
            lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            lines.append("```")
        
        lines.append(self._to_tree(structure))
        
        if level == 0:
            lines.append("```")
        
        return '\n'.join(lines)
    
    def _to_html_structure(self, structure: Dict[str, Any]) -> str:
        """Convert structure to HTML."""
        tree_content = html.escape(self._to_tree(structure))
        
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Project Structure</title>
    <style>
        body {{
            font-family: 'Consolas', 'Monaco', monospace;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            color: #e5e5e5;
            padding: 40px;
            margin: 0;
            min-height: 100vh;
        }}
        .container {{
            max-width: 1000px;
            margin: 0 auto;
            background: rgba(255,255,255,0.05);
            border-radius: 16px;
            padding: 30px;
            box-shadow: 0 8px 32px rgba(0,0,0,0.3);
        }}
        h1 {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-top: 0;
        }}
        .meta {{
            color: #888;
            font-size: 0.9em;
            margin-bottom: 20px;
        }}
        pre {{
            background: #0d1117;
            padding: 20px;
            border-radius: 8px;
            overflow-x: auto;
            border: 1px solid #30363d;
        }}
        .folder {{ color: #58a6ff; }}
        .file {{ color: #8b949e; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>📁 Project Structure</h1>
        <div class="meta">Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</div>
        <pre>{tree_content}</pre>
    </div>
</body>
</html>
"""
    
    def _files_to_txt(self, files: List[FileContent]) -> str:
        """Convert file contents to TXT format."""
        lines = [
            "=" * 80,
            "StructureMaster - Project Content Export",
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"Total Files: {len(files)}",
            "=" * 80,
            "",
        ]
        
        for file in files:
            lines.append(file.to_formatted_string())
        
        return '\n'.join(lines)
    
    def _files_to_json(self, files: List[FileContent]) -> str:
        """Convert file contents to JSON format."""
        data = {
            'generated': datetime.now().isoformat(),
            'total_files': len(files),
            'files': [f.to_dict() for f in files]
        }
        return self._to_json(data)
    
    def _files_to_markdown(self, files: List[FileContent]) -> str:
        """Convert file contents to Markdown format."""
        lines = [
            "# Project Content Export",
            "",
            f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"**Total Files:** {len(files)}",
            "",
            "---",
            "",
        ]
        
        for file in files:
            ext = file.extension or 'txt'
            lines.extend([
                f"## 📄 {file.filename}",
                "",
                f"- **Path:** `{file.relative_path}`",
                f"- **Size:** {file.size:,} bytes",
                f"- **MIME:** {file.mime_type}",
                f"- **SHA256:** `{file.sha256_hash[:16]}...`" if file.sha256_hash else "",
                "",
            ])
            
            if file.is_binary:
                lines.append("*Binary file - content not displayed*\n")
            elif file.content:
                lines.extend([
                    f"```{ext}",
                    file.content,
                    "```",
                    "",
                ])
            
            lines.append("---\n")
        
        return '\n'.join(lines)
    
    def _files_to_yaml(self, files: List[FileContent]) -> str:
        """Convert file contents to YAML format."""
        data = {
            'generated': datetime.now().isoformat(),
            'total_files': len(files),
            'files': [f.to_dict() for f in files]
        }
        return self._to_yaml(data)
    
    def _files_to_html(self, files: List[FileContent]) -> str:
        """Convert file contents to HTML format."""
        file_cards = []
        
        for file in files:
            content = html.escape(file.content[:5000] if file.content else '') if not file.is_binary else '[Binary file]'
            
            file_cards.append(f"""
            <div class="file-card">
                <div class="file-header">
                    <span class="file-icon">📄</span>
                    <span class="file-name">{html.escape(file.filename)}</span>
                    <span class="file-size">{file.size:,} bytes</span>
                </div>
                <div class="file-meta">
                    <span>Path: {html.escape(file.relative_path)}</span>
                    <span>Type: {file.mime_type}</span>
                </div>
                <pre class="file-content"><code>{content}</code></pre>
            </div>
            """)
        
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Project Content Export</title>
    <style>
        * {{ box-sizing: border-box; }}
        body {{
            font-family: 'Segoe UI', system-ui, sans-serif;
            background: linear-gradient(135deg, #0f0f23 0%, #1a1a3e 100%);
            color: #e5e5e5;
            padding: 40px;
            margin: 0;
            min-height: 100vh;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
        }}
        h1 {{
            background: linear-gradient(135deg, #00d4ff 0%, #7c3aed 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            font-size: 2.5em;
            margin-bottom: 10px;
        }}
        .meta {{
            color: #888;
            margin-bottom: 30px;
        }}
        .file-card {{
            background: rgba(255,255,255,0.03);
            border: 1px solid rgba(255,255,255,0.1);
            border-radius: 12px;
            margin-bottom: 20px;
            overflow: hidden;
        }}
        .file-header {{
            background: rgba(124,58,237,0.2);
            padding: 15px 20px;
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        .file-icon {{ font-size: 1.2em; }}
        .file-name {{
            font-weight: bold;
            flex: 1;
            color: #00d4ff;
        }}
        .file-size {{
            color: #888;
            font-size: 0.9em;
        }}
        .file-meta {{
            padding: 10px 20px;
            font-size: 0.85em;
            color: #888;
            display: flex;
            gap: 20px;
            border-bottom: 1px solid rgba(255,255,255,0.05);
        }}
        .file-content {{
            margin: 0;
            padding: 20px;
            background: #0d1117;
            overflow-x: auto;
            font-size: 13px;
            max-height: 400px;
            overflow-y: auto;
        }}
        .file-content code {{
            font-family: 'Consolas', 'Monaco', monospace;
        }}
        .stats {{
            display: flex;
            gap: 30px;
            margin-bottom: 30px;
        }}
        .stat {{
            background: rgba(255,255,255,0.05);
            padding: 15px 25px;
            border-radius: 8px;
        }}
        .stat-value {{
            font-size: 1.5em;
            font-weight: bold;
            color: #00d4ff;
        }}
        .stat-label {{
            font-size: 0.85em;
            color: #888;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>📦 Project Content Export</h1>
        <div class="meta">Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</div>
        
        <div class="stats">
            <div class="stat">
                <div class="stat-value">{len(files)}</div>
                <div class="stat-label">Total Files</div>
            </div>
            <div class="stat">
                <div class="stat-value">{sum(f.size for f in files):,}</div>
                <div class="stat-label">Total Bytes</div>
            </div>
        </div>
        
        {''.join(file_cards)}
    </div>
</body>
</html>
"""
    
    def _encrypt_content(self, content: str, password: str) -> bytes:
        """Encrypt content with AES-256."""
        if self._security is None:
            from .security import SecurityManager
            self._security = SecurityManager()
        
        return self._security.encrypt(content.encode('utf-8'), password)


# Create singleton instance
exporter = Exporter()
