"""
Stracture-Master - Content Extractor Tab
Extract file contents with metadata.
"""

import sys
from pathlib import Path

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QSplitter, QComboBox, QCheckBox, QMessageBox,
    QFileDialog, QSpinBox, QLineEdit, QScrollArea
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
from src.modules.content_extractor import ContentExtractor
from src.modules.exporter import Exporter


class ExtractWorker(QThread):
    """Background worker for content extraction."""
    
    progress = pyqtSignal(int, int, str)
    finished = pyqtSignal(object, object)  # scan_result, extract_result
    error = pyqtSignal(str)
    
    def __init__(self, path: Path, include_binary: bool, max_size_mb: float):
        super().__init__()
        self.path = path
        self.include_binary = include_binary
        self.max_size_mb = max_size_mb
    
    def run(self):
        try:
            # Scan first
            scanner = ProjectScanner()
            scan_result = scanner.scan(self.path)
            
            if not scan_result.success:
                self.error.emit("Scan failed: " + ', '.join(scan_result.errors))
                return
            
            # Extract content
            extractor = ContentExtractor(max_file_size_mb=self.max_size_mb)
            extractor.set_progress_callback(
                lambda c, t, n: self.progress.emit(c, t, n)
            )
            
            extract_result = extractor.extract(
                scan_result.files,
                include_binary=self.include_binary,
                extract_content=True
            )
            
            self.finished.emit(scan_result, extract_result)
        except Exception as e:
            self.error.emit(str(e))


class ContentExtractorTab(QWidget):
    """Content Extractor tab for extracting file contents."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._scan_result = None
        self._extract_result = None
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
        title = QLabel("📄 Content Extractor")
        title.setStyleSheet(f"""
            font-size: 20px;
            font-weight: bold;
            color: {COLORS['text_primary']};
        """)
        text_layout.addWidget(title)
        
        desc = QLabel("Extract file contents with full metadata (hash, MIME, encoding)")
        desc.setStyleSheet(f"color: {COLORS['text_muted']};")
        text_layout.addWidget(desc)
        layout.addLayout(text_layout)
        
        layout.addStretch()
        
        return header
    
    def _create_settings_panel(self) -> QWidget:
        """Create settings panel with scroll support."""
        # Create scroll area for the panel
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet(f"""
            QScrollArea {{
                border: none;
                background: transparent;
            }}
        """)
        scroll.setMinimumWidth(280)
        
        panel = CardWidget("Extraction Settings")
        panel.setMinimumHeight(500)
        
        # Path input
        path_label = QLabel("Project Path:")
        panel.addWidget(path_label)
        
        self.path_input = FileInputWidget(
            placeholder="Select project folder...",
            mode="folder"
        )
        panel.addWidget(self.path_input)
        
        # Max file size
        size_layout = QHBoxLayout()
        size_label = QLabel("Max file size (MB):")
        size_layout.addWidget(size_label)
        
        self.max_size_spin = QSpinBox()
        self.max_size_spin.setRange(1, 1000)
        self.max_size_spin.setValue(100)
        self.max_size_spin.setFixedWidth(100)
        self.max_size_spin.setMinimumHeight(32)
        size_layout.addWidget(self.max_size_spin)
        size_layout.addStretch()
        panel.addLayout(size_layout)
        
        # Options
        options_label = QLabel("Options")
        options_label.setStyleSheet(f"""
            font-weight: 600;
            color: {COLORS['text_primary']};
            padding-top: 10px;
            padding-bottom: 4px;
        """)
        options_label.setMinimumHeight(30)
        panel.addWidget(options_label)
        
        self.binary_check = QCheckBox("Include binary files (metadata only)")
        self.binary_check.setChecked(True)
        panel.addWidget(self.binary_check)
        
        self.hash_check = QCheckBox("Calculate SHA-256 hashes")
        self.hash_check.setChecked(True)
        panel.addWidget(self.hash_check)
        
        # Extract button
        extract_btn = QPushButton("📦 Extract Content")
        extract_btn.clicked.connect(self._extract_content)
        panel.addWidget(extract_btn)
        
        # Spacer
        spacer = QWidget()
        spacer.setFixedHeight(20)
        panel.addWidget(spacer)
        
        # Export section
        export_label = QLabel("Export")
        export_label.setStyleSheet(f"""
            font-weight: 600;
            color: {COLORS['text_primary']};
        """)
        export_label.setMinimumHeight(24)
        panel.addWidget(export_label)
        
        format_layout = QHBoxLayout()
        format_label = QLabel("Format:")
        format_layout.addWidget(format_label)
        
        self.format_combo = QComboBox()
        self.format_combo.addItems(["TXT", "JSON", "Markdown", "HTML", "ZIP Archive"])
        format_layout.addWidget(self.format_combo)
        format_layout.addStretch()
        panel.addLayout(format_layout)
        
        # Encryption
        self.encrypt_check = QCheckBox("Encrypt output (AES-256)")
        panel.addWidget(self.encrypt_check)
        
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Encryption password...")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setEnabled(False)
        self.encrypt_check.toggled.connect(self.password_input.setEnabled)
        panel.addWidget(self.password_input)
        
        self.export_btn = QPushButton("💾 Export Content")
        self.export_btn.setObjectName("secondary")
        self.export_btn.setEnabled(False)
        self.export_btn.clicked.connect(self._export_content)
        panel.addWidget(self.export_btn)
        
        scroll.setWidget(panel)
        return scroll
    
    def _create_results_panel(self) -> QWidget:
        """Create results panel."""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(15)
        
        # Stats row
        stats_layout = QHBoxLayout()
        self.files_stat = StatCard("Files", "0", "📄")
        self.binary_stat = StatCard("Binary", "0", "📦")
        self.lines_stat = StatCard("Lines", "0", "📝")
        self.size_stat = StatCard("Total Size", "0 B", "💾")
        
        stats_layout.addWidget(self.files_stat)
        stats_layout.addWidget(self.binary_stat)
        stats_layout.addWidget(self.lines_stat)
        stats_layout.addWidget(self.size_stat)
        layout.addLayout(stats_layout)
        
        # Tree view
        tree_card = CardWidget("Extracted Files")
        self.tree_view = TreeViewWidget()
        tree_card.addWidget(self.tree_view)
        layout.addWidget(tree_card, 1)
        
        return panel
    
    def _extract_content(self):
        """Start content extraction."""
        path = self.path_input.get_path()
        if not path:
            QMessageBox.warning(self, "Warning", "Please select a project folder")
            return
        
        if not Path(path).exists():
            QMessageBox.warning(self, "Warning", "Selected path does not exist")
            return
        
        # Start extraction
        self.progress.start("Extracting content...")
        
        self.worker = ExtractWorker(
            Path(path),
            self.binary_check.isChecked(),
            self.max_size_spin.value()
        )
        self.worker.progress.connect(self._on_extract_progress)
        self.worker.finished.connect(self._on_extract_finished)
        self.worker.error.connect(self._on_extract_error)
        self.worker.start()
    
    def _on_extract_progress(self, current: int, total: int, name: str):
        """Handle extraction progress."""
        self.progress.update_progress(current, total, f"Extracting: {name}")
    
    def _on_extract_finished(self, scan_result, extract_result):
        """Handle extraction completion."""
        self._scan_result = scan_result
        self._extract_result = extract_result
        
        if extract_result:
            self.progress.finish("Extraction complete!")
            
            # Update stats
            self.files_stat.set_value(str(extract_result.stats['extracted_files']))
            self.binary_stat.set_value(str(extract_result.stats['binary_files']))
            self.lines_stat.set_value(f"{extract_result.stats['total_lines']:,}")
            
            # Format size
            size = extract_result.stats['total_size']
            if size >= 1024 * 1024:
                size_str = f"{size / (1024*1024):.1f} MB"
            elif size >= 1024:
                size_str = f"{size / 1024:.1f} KB"
            else:
                size_str = f"{size} B"
            self.size_stat.set_value(size_str)
            
            # Load tree
            self.tree_view.load_structure(scan_result.structure)
            
            # Enable export
            self.export_btn.setEnabled(True)
        else:
            self.progress.finish("Extraction failed")
    
    def _on_extract_error(self, error: str):
        """Handle extraction error."""
        self.progress.finish("Error")
        QMessageBox.critical(self, "Error", f"Extraction failed: {error}")
    
    def _export_content(self):
        """Export the extracted content."""
        if not self._extract_result:
            return
        
        # Get format
        format_map = {
            "TXT": (ExportFormat.TXT, "txt"),
            "JSON": (ExportFormat.JSON, "json"),
            "Markdown": (ExportFormat.MARKDOWN, "md"),
            "HTML": (ExportFormat.HTML, "html"),
            "ZIP Archive": (ExportFormat.ZIP, "zip"),
        }
        fmt, ext = format_map.get(self.format_combo.currentText(),
                                  (ExportFormat.TXT, "txt"))
        
        # Get save path
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Content",
            f"content.{ext}",
            f"{self.format_combo.currentText()} (*.{ext})"
        )
        
        if not path:
            return
        
        # Check encryption
        encrypt = self.encrypt_check.isChecked()
        password = self.password_input.text() if encrypt else None
        
        if encrypt and not password:
            QMessageBox.warning(self, "Warning", "Please enter encryption password")
            return
        
        # Export
        exporter = Exporter()
        result = exporter.export_content(
            self._extract_result.files,
            Path(path),
            format=fmt,
            encrypt=encrypt,
            password=password
        )
        
        if result.success:
            msg = f"Content exported to:\n{path}"
            if encrypt:
                msg += "\n\n🔐 File is encrypted"
            QMessageBox.information(self, "Success", msg)
        else:
            QMessageBox.critical(
                self, "Export Failed",
                f"Errors:\n" + '\n'.join(result.errors)
            )
