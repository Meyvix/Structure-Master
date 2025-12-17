"""
Stracture-Master - Structure Builder Tab
Build project structure from various input formats.
"""

import sys
from pathlib import Path
from typing import Optional

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QSplitter, QTextEdit, QComboBox, QCheckBox,
    QMessageBox, QFileDialog, QScrollArea
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from src.gui.styles import COLORS
from src.gui.components import (
    CardWidget, StatCard, TreeViewWidget, FileInputWidget,
    ProgressWidget, LogViewerWidget
)
from src.modules.parser import StructureParser
from src.modules.validator import StructureValidator
from src.modules.builder import StructureBuilder


class BuildWorker(QThread):
    """Background worker for building structure."""
    
    progress = pyqtSignal(int, int, str)
    finished = pyqtSignal(object)
    error = pyqtSignal(str)
    
    def __init__(self, structure: dict, output_path: Path, force: bool, dry_run: bool):
        super().__init__()
        self.structure = structure
        self.output_path = output_path
        self.force = force
        self.dry_run = dry_run
    
    def run(self):
        try:
            builder = StructureBuilder()
            builder.set_progress_callback(
                lambda c, t, n: self.progress.emit(c, t, n)
            )
            
            result = builder.build(
                self.structure,
                self.output_path,
                force=self.force,
                dry_run=self.dry_run
            )
            
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))


class StructureBuilderTab(QWidget):
    """Structure Builder tab for creating project structure."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._current_structure = {}
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
        
        # Left panel - Input
        left_panel = self._create_input_panel()
        splitter.addWidget(left_panel)
        
        # Right panel - Preview & Actions
        right_panel = self._create_preview_panel()
        splitter.addWidget(right_panel)
        
        splitter.setSizes([600, 500])
        layout.addWidget(splitter, 1)
        
        # Progress
        self.progress = ProgressWidget()
        layout.addWidget(self.progress)
    
    def _create_header(self) -> QWidget:
        """Create header section."""
        header = QFrame()
        layout = QHBoxLayout(header)
        layout.setContentsMargins(0, 0, 0, 10)
        
        # Title and description
        text_layout = QVBoxLayout()
        title = QLabel("🔨 Structure Builder")
        title.setStyleSheet(f"""
            font-size: 20px;
            font-weight: bold;
            color: {COLORS['text_primary']};
        """)
        text_layout.addWidget(title)
        
        desc = QLabel("Create project structure from JSON, tree text, or clipboard")
        desc.setStyleSheet(f"color: {COLORS['text_muted']};")
        text_layout.addWidget(desc)
        layout.addLayout(text_layout)
        
        layout.addStretch()
        
        # Quick buttons
        from_file_btn = QPushButton("📂 From File")
        from_file_btn.setObjectName("secondary")
        from_file_btn.clicked.connect(self._load_from_file)
        layout.addWidget(from_file_btn)
        
        from_clipboard_btn = QPushButton("📋 From Clipboard")
        from_clipboard_btn.setObjectName("secondary")
        from_clipboard_btn.clicked.connect(self._load_from_clipboard)
        layout.addWidget(from_clipboard_btn)
        
        return header
    
    def _create_input_panel(self) -> QWidget:
        """Create input panel."""
        panel = CardWidget("Input Structure")
        
        # Format selector
        format_layout = QHBoxLayout()
        format_label = QLabel("Format:")
        format_layout.addWidget(format_label)
        
        self.format_combo = QComboBox()
        self.format_combo.addItems(["Auto Detect", "JSON", "Tree Text", "Plain Paths"])
        format_layout.addWidget(self.format_combo)
        format_layout.addStretch()
        panel.addLayout(format_layout)
        
        # Text input
        self.input_text = QTextEdit()
        self.input_text.setPlaceholderText(
            "Paste or type your project structure here...\n\n"
            "Supported formats:\n"
            "• JSON: {\"src\": {\"main.py\": null}}\n"
            "• Tree: ├── src/\n│   └── main.py\n"
            "• Paths: src/main.py"
        )
        self.input_text.setStyleSheet(f"""
            QTextEdit {{
                font-family: 'Consolas', 'Monaco', monospace;
                font-size: 13px;
                background-color: {COLORS['bg_tertiary']};
                border: 1px solid {COLORS['border']};
                border-radius: 8px;
                padding: 15px;
            }}
        """)
        self.input_text.textChanged.connect(self._on_input_changed)
        panel.addWidget(self.input_text)
        
        # Parse button
        parse_btn = QPushButton("🔍 Parse Structure")
        parse_btn.clicked.connect(self._parse_input)
        panel.addWidget(parse_btn)
        
        return panel
    
    def _create_preview_panel(self) -> QWidget:
        """Create preview and actions panel with scroll support."""
        # Create scroll area for the entire panel
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet(f"""
            QScrollArea {{
                border: none;
                background: transparent;
            }}
        """)
        
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(15)
        
        # Preview card
        preview_card = CardWidget("Structure Preview")
        preview_card.setMinimumHeight(250)
        
        self.tree_view = TreeViewWidget()
        self.tree_view.setMinimumHeight(120)
        preview_card.addWidget(self.tree_view)
        
        # Stats row
        stats_layout = QHBoxLayout()
        self.files_stat = StatCard("Files", "0", "📄")
        self.dirs_stat = StatCard("Folders", "0", "📁")
        stats_layout.addWidget(self.files_stat)
        stats_layout.addWidget(self.dirs_stat)
        preview_card.addLayout(stats_layout)
        
        layout.addWidget(preview_card, 1)
        
        # Output settings card
        output_card = CardWidget("Output Settings")
        output_card.setMinimumHeight(180)
        
        # Output path
        output_label = QLabel("Output Directory:")
        output_card.addWidget(output_label)
        
        self.output_path = FileInputWidget(
            placeholder="Select output directory...",
            mode="folder"
        )
        output_card.addWidget(self.output_path)
        
        # Options
        options_layout = QHBoxLayout()
        
        self.force_check = QCheckBox("Force overwrite")
        self.force_check.setToolTip("Overwrite existing files and directories")
        options_layout.addWidget(self.force_check)
        
        self.dry_run_check = QCheckBox("Dry run")
        self.dry_run_check.setToolTip("Preview without creating anything")
        options_layout.addWidget(self.dry_run_check)
        
        options_layout.addStretch()
        output_card.addLayout(options_layout)
        
        # Build button
        build_layout = QHBoxLayout()
        build_layout.addStretch()
        
        self.build_btn = QPushButton("🚀 Build Structure")
        self.build_btn.setEnabled(False)
        self.build_btn.clicked.connect(self._build_structure)
        build_layout.addWidget(self.build_btn)
        
        output_card.addLayout(build_layout)
        
        layout.addWidget(output_card)
        
        scroll.setWidget(panel)
        return scroll
    
    def _on_input_changed(self):
        """Handle input text changes."""
        # Reset preview if input changes significantly
        pass
    
    def _load_from_file(self):
        """Load structure from file."""
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Open Structure File",
            "",
            "All Supported (*.json *.txt *.md);;JSON (*.json);;Text (*.txt);;Markdown (*.md)"
        )
        
        if path:
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    content = f.read()
                self.input_text.setPlainText(content)
                self._parse_input()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to read file: {e}")
    
    def _load_from_clipboard(self):
        """Load structure from clipboard."""
        from PyQt6.QtWidgets import QApplication
        clipboard = QApplication.clipboard()
        text = clipboard.text()
        
        if text:
            self.input_text.setPlainText(text)
            self._parse_input()
        else:
            QMessageBox.information(self, "Info", "Clipboard is empty")
    
    def _parse_input(self):
        """Parse the input structure."""
        text = self.input_text.toPlainText().strip()
        if not text:
            QMessageBox.warning(self, "Warning", "Please enter a structure")
            return
        
        parser = StructureParser()
        
        # Determine format
        format_map = {
            "Auto Detect": None,
            "JSON": "json",
            "Tree Text": "tree",
            "Plain Paths": "plain",
        }
        format_hint = format_map.get(self.format_combo.currentText())
        
        result = parser.parse(text, format_hint)
        
        if not result.success:
            QMessageBox.critical(
                self, "Parse Error",
                f"Failed to parse structure:\n{', '.join(result.errors)}"
            )
            return
        
        self._current_structure = result.structure
        
        # Update preview
        self.tree_view.load_structure(result.structure)
        
        # Update stats
        self.files_stat.set_value(str(result.stats.get('files', 0)))
        self.dirs_stat.set_value(str(result.stats.get('directories', 0)))
        
        # Enable build button
        self.build_btn.setEnabled(True)
        
        QMessageBox.information(
            self, "Parsed Successfully",
            f"Format: {result.format_detected.name}\n"
            f"Files: {result.stats.get('files', 0)}\n"
            f"Directories: {result.stats.get('directories', 0)}"
        )
    
    def _build_structure(self):
        """Build the project structure."""
        if not self._current_structure:
            QMessageBox.warning(self, "Warning", "No structure to build")
            return
        
        output_path = self.output_path.get_path()
        if not output_path:
            QMessageBox.warning(self, "Warning", "Please select output directory")
            return
        
        # Validate
        validator = StructureValidator()
        val_result = validator.validate(self._current_structure, Path(output_path))
        
        if not val_result.is_valid and not self.force_check.isChecked():
            errors = '\n'.join([f"• {e.message}" for e in val_result.errors[:5]])
            reply = QMessageBox.question(
                self, "Validation Issues",
                f"Structure has issues:\n{errors}\n\nContinue anyway?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.No:
                return
        
        # Start build
        self.progress.start("Building structure...")
        self.build_btn.setEnabled(False)
        
        self.worker = BuildWorker(
            self._current_structure,
            Path(output_path),
            self.force_check.isChecked(),
            self.dry_run_check.isChecked()
        )
        self.worker.progress.connect(self._on_build_progress)
        self.worker.finished.connect(self._on_build_finished)
        self.worker.error.connect(self._on_build_error)
        self.worker.start()
    
    def _on_build_progress(self, current: int, total: int, name: str):
        """Handle build progress updates."""
        self.progress.update_progress(current, total, f"Creating: {name}")
    
    def _on_build_finished(self, result):
        """Handle build completion."""
        self.build_btn.setEnabled(True)
        
        if result.success:
            self.progress.finish("Build complete!")
            QMessageBox.information(
                self, "Success",
                f"Structure built successfully!\n\n"
                f"Directories created: {result.stats['directories_created']}\n"
                f"Files created: {result.stats['files_created']}\n"
                f"Items skipped: {result.stats['items_skipped']}\n"
                f"Time: {result.stats['build_time_ms']}ms"
            )
        else:
            self.progress.finish("Build failed")
            QMessageBox.critical(
                self, "Build Failed",
                f"Errors:\n" + '\n'.join(result.errors[:5])
            )
    
    def _on_build_error(self, error: str):
        """Handle build error."""
        self.build_btn.setEnabled(True)
        self.progress.finish("Error")
        QMessageBox.critical(self, "Error", f"Build failed: {error}")
