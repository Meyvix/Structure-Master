"""
StructureMaster - Search GUI Tab
GUI tab for project-wide search functionality.
"""

from pathlib import Path
from typing import Dict, Any, List, Optional

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QComboBox, QCheckBox, QPushButton, QPlainTextEdit,
    QSpinBox, QTableWidget, QTableWidgetItem, QHeaderView,
    QSplitter, QGroupBox, QLineEdit
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QColor

from ..components import CardWidget, FileInputWidget, ProgressWidget


class SearchWorker(QThread):
    """Worker thread for search operations."""
    
    progress = pyqtSignal(str)
    finished = pyqtSignal(object)
    error = pyqtSignal(str)
    
    def __init__(self, search_path: Path, pattern: str, options: Dict):
        super().__init__()
        self.search_path = search_path
        self.pattern = pattern
        self.options = options
    
    def run(self):
        try:
            from src.search.search_engine import SearchEngine
            
            engine = SearchEngine()
            
            if self.options.get('search_content', False):
                result = engine.search_content(
                    self.search_path,
                    self.pattern,
                    is_regex=self.options.get('is_regex', True),
                    case_sensitive=self.options.get('case_sensitive', False),
                    context_lines=self.options.get('context_lines', 0)
                )
            else:
                result = engine.search_filename(
                    self.search_path,
                    self.pattern,
                    is_regex=self.options.get('is_regex', False),
                    case_sensitive=self.options.get('case_sensitive', False)
                )
            
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))


class SearchTab(QWidget):
    """Search tab for project-wide search."""
    
    def __init__(self):
        super().__init__()
        self._init_ui()
        self._worker = None
    
    def _init_ui(self):
        """Initialize the UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Search input card
        search_card = CardWidget("Search")
        search_layout = QVBoxLayout(search_card)
        
        # Project path
        path_layout = QHBoxLayout()
        path_layout.addWidget(QLabel("Project Path:"))
        self.path_input = FileInputWidget(mode='folder')
        path_layout.addWidget(self.path_input)
        search_layout.addLayout(path_layout)
        
        # Search pattern
        pattern_layout = QHBoxLayout()
        pattern_layout.addWidget(QLabel("Search Pattern:"))
        self.pattern_input = QLineEdit()
        self.pattern_input.setPlaceholderText("Enter search pattern (regex or text)...")
        pattern_layout.addWidget(self.pattern_input)
        search_layout.addLayout(pattern_layout)
        
        # Options
        options_layout = QHBoxLayout()
        
        self.regex_check = QCheckBox("Use Regex")
        self.regex_check.setChecked(True)
        options_layout.addWidget(self.regex_check)
        
        self.case_check = QCheckBox("Case Sensitive")
        options_layout.addWidget(self.case_check)
        
        self.content_check = QCheckBox("Search Content")
        self.content_check.setChecked(True)
        options_layout.addWidget(self.content_check)
        
        options_layout.addWidget(QLabel("Context Lines:"))
        self.context_spin = QSpinBox()
        self.context_spin.setRange(0, 10)
        self.context_spin.setValue(1)
        options_layout.addWidget(self.context_spin)
        
        options_layout.addStretch()
        search_layout.addLayout(options_layout)
        
        # Search buttons
        btn_layout = QHBoxLayout()
        
        self.search_btn = QPushButton("🔍 Search")
        self.search_btn.setObjectName("primaryButton")
        self.search_btn.clicked.connect(self._start_search)
        btn_layout.addWidget(self.search_btn)
        
        self.todo_btn = QPushButton("📝 Find TODOs")
        self.todo_btn.clicked.connect(self._search_todos)
        btn_layout.addWidget(self.todo_btn)
        
        self.large_btn = QPushButton("📦 Large Files")
        self.large_btn.clicked.connect(self._find_large_files)
        btn_layout.addWidget(self.large_btn)
        
        btn_layout.addStretch()
        search_layout.addLayout(btn_layout)
        
        layout.addWidget(search_card)
        
        # Progress
        self.progress = ProgressWidget()
        self.progress.hide()
        layout.addWidget(self.progress)
        
        # Results card
        results_card = CardWidget("Results")
        results_layout = QVBoxLayout(results_card)
        
        # Results table
        self.results_table = QTableWidget()
        self.results_table.setColumnCount(4)
        self.results_table.setHorizontalHeaderLabels(['File', 'Line', 'Match', 'Context'])
        self.results_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Interactive)
        self.results_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        self.results_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Interactive)
        self.results_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        self.results_table.setColumnWidth(1, 60)
        self.results_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.results_table.setAlternatingRowColors(True)
        results_layout.addWidget(self.results_table)
        
        # Results stats
        self.stats_label = QLabel("No results")
        results_layout.addWidget(self.stats_label)
        
        layout.addWidget(results_card, stretch=1)
    
    def _start_search(self):
        """Start search operation."""
        path = self.path_input.get_path()
        pattern = self.pattern_input.text().strip()
        
        if not path or not Path(path).exists():
            return
        if not pattern:
            return
        
        self.progress.start_indeterminate("Searching...")
        self.search_btn.setEnabled(False)
        
        options = {
            'is_regex': self.regex_check.isChecked(),
            'case_sensitive': self.case_check.isChecked(),
            'search_content': self.content_check.isChecked(),
            'context_lines': self.context_spin.value(),
        }
        
        self._worker = SearchWorker(Path(path), pattern, options)
        self._worker.finished.connect(self._on_search_complete)
        self._worker.error.connect(self._on_search_error)
        self._worker.start()
    
    def _search_todos(self):
        """Search for TODO/FIXME markers."""
        self.pattern_input.setText(r'\b(TODO|FIXME|HACK|XXX|BUG)\b')
        self.regex_check.setChecked(True)
        self.content_check.setChecked(True)
        self._start_search()
    
    def _find_large_files(self):
        """Find large files."""
        path = self.path_input.get_path()
        if not path or not Path(path).exists():
            return
        
        try:
            from src.search.search_engine import SearchEngine
            engine = SearchEngine()
            
            large_files = engine.find_large_files(Path(path), min_size_mb=1)
            
            self.results_table.setRowCount(len(large_files))
            for i, f in enumerate(large_files):
                self.results_table.setItem(i, 0, QTableWidgetItem(f['filename']))
                self.results_table.setItem(i, 1, QTableWidgetItem('-'))
                self.results_table.setItem(i, 2, QTableWidgetItem(f"{f['size_mb']} MB"))
                self.results_table.setItem(i, 3, QTableWidgetItem(f['path']))
            
            self.stats_label.setText(f"Found {len(large_files)} large files (>1 MB)")
        except Exception as e:
            self.stats_label.setText(f"Error: {e}")
    
    def _on_search_complete(self, result):
        """Handle search completion."""
        self.progress.stop()
        self.search_btn.setEnabled(True)
        
        matches = result.matches
        
        self.results_table.setRowCount(len(matches))
        for i, match in enumerate(matches):
            self.results_table.setItem(i, 0, QTableWidgetItem(match.filename))
            self.results_table.setItem(i, 1, QTableWidgetItem(str(match.line_number or '-')))
            self.results_table.setItem(i, 2, QTableWidgetItem(match.match_text[:50]))
            self.results_table.setItem(i, 3, QTableWidgetItem(match.context[:100]))
        
        self.stats_label.setText(
            f"Found {result.total_matches} matches in {result.files_searched} files "
            f"({result.search_time_ms} ms)"
        )
    
    def _on_search_error(self, error):
        """Handle search error."""
        self.progress.stop()
        self.search_btn.setEnabled(True)
        self.stats_label.setText(f"Error: {error}")
