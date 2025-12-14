"""
StructureMaster - Structure Extractor Tab
Scan and extract project structure.
"""

import sys
from pathlib import Path

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QSplitter, QComboBox, QCheckBox, QMessageBox,
    QFileDialog
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from src.gui.styles import COLORS
from src.gui.components import (
    CardWidget, StatCard, TreeViewWidget, FileInputWidget,
    ProgressWidget
)
from src.config import ExportFormat
from src.modules.scanner import ProjectScanner
from src.modules.exporter import Exporter


class ScanWorker(QThread):
    """Background worker for scanning."""
    
    progress = pyqtSignal(int, int, str)
    finished = pyqtSignal(object)
    error = pyqtSignal(str)
    
    def __init__(self, path: Path, recursive: bool, include_hidden: bool):
        super().__init__()
        self.path = path
        self.recursive = recursive
        self.include_hidden = include_hidden
    
    def run(self):
        try:
            scanner = ProjectScanner()
            result = scanner.scan(
                self.path,
                recursive=self.recursive,
                include_hidden=self.include_hidden
            )
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))


class StructureExtractorTab(QWidget):
    """Structure Extractor tab for scanning projects."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._scan_result = None
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup the tab UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(25, 25, 25, 25)
        layout.setSpacing(20)
        
        # Header
        header = self._create_header()
        layout.addWidget(header)
        
        # Main content - splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setStyleSheet(f"""
            QSplitter::handle {{
                background: {COLORS['border']};
                width: 2px;
            }}
        """)
        
        # Left panel - Settings
        left_panel = self._create_settings_panel()
        splitter.addWidget(left_panel)
        
        # Right panel - Results
        right_panel = self._create_results_panel()
        splitter.addWidget(right_panel)
        
        splitter.setSizes([400, 700])
        layout.addWidget(splitter, 1)
        
        # Progress
        self.progress = ProgressWidget()
        layout.addWidget(self.progress)
    
    def _create_header(self) -> QWidget:
        """Create header section."""
        header = QFrame()
        layout = QHBoxLayout(header)
        layout.setContentsMargins(0, 0, 0, 10)
        
        text_layout = QVBoxLayout()
        title = QLabel("📂 Structure Extractor")
        title.setStyleSheet(f"""
            font-size: 20px;
            font-weight: bold;
            color: {COLORS['text_primary']};
        """)
        text_layout.addWidget(title)
        
        desc = QLabel("Scan and extract project structure from existing projects")
        desc.setStyleSheet(f"color: {COLORS['text_muted']};")
        text_layout.addWidget(desc)
        layout.addLayout(text_layout)
        
        layout.addStretch()
        
        return header
    
    def _create_settings_panel(self) -> QWidget:
        """Create settings panel."""
        panel = CardWidget("Scan Settings")
        
        # Path input
        path_label = QLabel("Project Path:")
        panel.addWidget(path_label)
        
        self.path_input = FileInputWidget(
            placeholder="Select project folder...",
            mode="folder"
        )
        panel.addWidget(self.path_input)
        
        # Options
        options_label = QLabel("Options")
        options_label.setStyleSheet(f"""
            font-weight: 600;
            color: {COLORS['text_primary']};
            margin-top: 15px;
        """)
        panel.addWidget(options_label)
        
        self.recursive_check = QCheckBox("Recursive scan")
        self.recursive_check.setChecked(True)
        panel.addWidget(self.recursive_check)
        
        self.hidden_check = QCheckBox("Include hidden files")
        panel.addWidget(self.hidden_check)
        
        self.symlinks_check = QCheckBox("Follow symlinks")
        panel.addWidget(self.symlinks_check)
        
        self.auto_detect_check = QCheckBox("Auto-detect project type")
        self.auto_detect_check.setChecked(True)
        panel.addWidget(self.auto_detect_check)
        
        # Scan button
        scan_btn = QPushButton("🔍 Scan Project")
        scan_btn.clicked.connect(self._scan_project)
        panel.addWidget(scan_btn)
        
        # Spacer
        spacer = QWidget()
        spacer.setMinimumHeight(20)
        panel.addWidget(spacer)
        
        # Export section
        export_label = QLabel("Export")
        export_label.setStyleSheet(f"""
            font-weight: 600;
            color: {COLORS['text_primary']};
        """)
        panel.addWidget(export_label)
        
        format_layout = QHBoxLayout()
        format_label = QLabel("Format:")
        format_layout.addWidget(format_label)
        
        self.format_combo = QComboBox()
        self.format_combo.addItems(["JSON", "TXT (Tree)", "Markdown", "YAML", "HTML"])
        format_layout.addWidget(self.format_combo)
        format_layout.addStretch()
        panel.addLayout(format_layout)
        
        self.export_btn = QPushButton("💾 Export Structure")
        self.export_btn.setObjectName("secondary")
        self.export_btn.setEnabled(False)
        self.export_btn.clicked.connect(self._export_structure)
        panel.addWidget(self.export_btn)
        
        return panel
    
    def _create_results_panel(self) -> QWidget:
        """Create results panel."""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(15)
        
        # Stats row
        stats_layout = QHBoxLayout()
        self.type_stat = StatCard("Project Type", "-", "🏷️")
        self.files_stat = StatCard("Files", "0", "📄")
        self.dirs_stat = StatCard("Folders", "0", "📁")
        self.size_stat = StatCard("Total Size", "0 B", "💾")
        
        stats_layout.addWidget(self.type_stat)
        stats_layout.addWidget(self.files_stat)
        stats_layout.addWidget(self.dirs_stat)
        stats_layout.addWidget(self.size_stat)
        layout.addLayout(stats_layout)
        
        # Tree view
        tree_card = CardWidget("Project Structure")
        self.tree_view = TreeViewWidget()
        tree_card.addWidget(self.tree_view)
        layout.addWidget(tree_card, 1)
        
        return panel
    
    def _scan_project(self):
        """Start scanning the project."""
        path = self.path_input.get_path()
        if not path:
            QMessageBox.warning(self, "Warning", "Please select a project folder")
            return
        
        if not Path(path).exists():
            QMessageBox.warning(self, "Warning", "Selected path does not exist")
            return
        
        # Start scan
        self.progress.start("Scanning project...")
        
        self.worker = ScanWorker(
            Path(path),
            self.recursive_check.isChecked(),
            self.hidden_check.isChecked()
        )
        self.worker.finished.connect(self._on_scan_finished)
        self.worker.error.connect(self._on_scan_error)
        self.worker.start()
    
    def _on_scan_finished(self, result):
        """Handle scan completion."""
        self._scan_result = result
        
        if result.success:
            self.progress.finish("Scan complete!")
            
            # Update stats
            self.type_stat.set_value(result.project_type.name)
            self.files_stat.set_value(str(result.stats['total_files']))
            self.dirs_stat.set_value(str(result.stats['total_directories']))
            
            # Format size
            size = result.stats['total_size']
            if size >= 1024 * 1024:
                size_str = f"{size / (1024*1024):.1f} MB"
            elif size >= 1024:
                size_str = f"{size / 1024:.1f} KB"
            else:
                size_str = f"{size} B"
            self.size_stat.set_value(size_str)
            
            # Load tree
            self.tree_view.load_structure(result.structure)
            
            # Enable export
            self.export_btn.setEnabled(True)
        else:
            self.progress.finish("Scan failed")
            QMessageBox.critical(
                self, "Scan Failed",
                f"Errors:\n" + '\n'.join(result.errors[:5])
            )
    
    def _on_scan_error(self, error: str):
        """Handle scan error."""
        self.progress.finish("Error")
        QMessageBox.critical(self, "Error", f"Scan failed: {error}")
    
    def _export_structure(self):
        """Export the scanned structure."""
        if not self._scan_result:
            return
        
        # Get format
        format_map = {
            "JSON": (ExportFormat.JSON, "json"),
            "TXT (Tree)": (ExportFormat.TXT, "txt"),
            "Markdown": (ExportFormat.MARKDOWN, "md"),
            "YAML": (ExportFormat.YAML, "yaml"),
            "HTML": (ExportFormat.HTML, "html"),
        }
        fmt, ext = format_map.get(self.format_combo.currentText(), 
                                  (ExportFormat.JSON, "json"))
        
        # Get save path
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Structure",
            f"structure.{ext}",
            f"{self.format_combo.currentText()} (*.{ext})"
        )
        
        if not path:
            return
        
        # Export
        exporter = Exporter()
        result = exporter.export_structure(
            self._scan_result.structure,
            Path(path),
            fmt
        )
        
        if result.success:
            QMessageBox.information(
                self, "Success",
                f"Structure exported to:\n{path}"
            )
        else:
            QMessageBox.critical(
                self, "Export Failed",
                f"Errors:\n" + '\n'.join(result.errors)
            )
