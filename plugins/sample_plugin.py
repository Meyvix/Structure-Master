"""
StructureMaster - Sample Plugin
Example plugin demonstrating the plugin system.
"""

from pathlib import Path
from src.modules.plugin_manager import PluginBase


class SamplePlugin(PluginBase):
    """
    Sample plugin that logs events during scans and builds.
    """
    
    NAME = 'SamplePlugin'
    VERSION = '1.0.0'
    AUTHOR = 'StructureMaster Team'
    DESCRIPTION = 'A sample plugin demonstrating the plugin system'
    
    def on_load(self) -> None:
        """Called when the plugin is loaded."""
        self.logger.info(f"[{self.NAME}] Plugin loaded successfully!")
        self._file_count = 0
    
    def on_unload(self) -> None:
        """Called when the plugin is unloaded."""
        self.logger.info(f"[{self.NAME}] Plugin unloaded. Total files processed: {self._file_count}")
    
    def on_scan_start(self, path: Path) -> None:
        """Called when a scan starts."""
        self.logger.info(f"[{self.NAME}] Scan started for: {path}")
        self._file_count = 0
    
    def on_scan_complete(self, result) -> None:
        """Called when a scan completes."""
        if hasattr(result, 'stats'):
            self._file_count = result.stats.get('total_files', 0)
        self.logger.info(f"[{self.NAME}] Scan complete! Found {self._file_count} files")
    
    def on_build_start(self, structure: dict) -> None:
        """Called when a build starts."""
        item_count = self._count_items(structure)
        self.logger.info(f"[{self.NAME}] Build started with {item_count} items")
    
    def on_build_complete(self, result) -> None:
        """Called when a build completes."""
        if hasattr(result, 'stats'):
            created = result.stats.get('files_created', 0) + result.stats.get('directories_created', 0)
            self.logger.info(f"[{self.NAME}] Build complete! Created {created} items")
    
    def on_export_start(self, format: str) -> None:
        """Called when an export starts."""
        self.logger.info(f"[{self.NAME}] Export started in {format} format")
    
    def on_export_complete(self, result) -> None:
        """Called when an export completes."""
        if hasattr(result, 'output_path'):
            self.logger.info(f"[{self.NAME}] Export complete: {result.output_path}")
    
    def _count_items(self, structure: dict) -> int:
        """Count total items in structure."""
        count = 0
        for name, content in structure.items():
            count += 1
            if isinstance(content, dict):
                count += self._count_items(content)
        return count
