"""
StructureMaster - Analytics GUI Tab
GUI tab for project analytics and charts.
"""

from pathlib import Path
from typing import Dict, Any, Optional

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QScrollArea, QFrame, QSplitter,
    QTableWidget, QTableWidgetItem, QHeaderView, QGroupBox
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtWebEngineWidgets import QWebEngineView

from ..components import CardWidget, FileInputWidget, StatCard, ProgressWidget


class AnalyticsWorker(QThread):
    """Worker thread for analytics operations."""
    
    progress = pyqtSignal(str)
    finished = pyqtSignal(object, str, str, str)  # stats, pie_svg, bar_svg, treemap_svg
    error = pyqtSignal(str)
    
    def __init__(self, project_path: Path):
        super().__init__()
        self.project_path = project_path
    
    def run(self):
        try:
            from src.analytics.statistics import ProjectStatistics
            from src.analytics.charts import ChartGenerator
            
            stats = ProjectStatistics()
            charts = ChartGenerator()
            
            self.progress.emit("Analyzing project...")
            analysis = stats.analyze(self.project_path)
            
            self.progress.emit("Generating charts...")
            
            # File type distribution pie chart
            type_dist = stats.get_type_distribution(analysis)
            pie_svg = charts.pie_chart(type_dist, "File Type Distribution")
            
            # Size distribution bar chart
            size_dist = stats.get_size_distribution([])  # Would need files list
            bar_svg = charts.bar_chart(
                {k: v for k, v in analysis.file_types.items() if v.count > 0},
                "Files by Extension"
            )
            
            # Directory sizes treemap
            dir_sizes = stats.get_directory_sizes(self.project_path, max_depth=2)
            treemap_svg = charts.treemap(dir_sizes, "Directory Sizes")
            
            self.finished.emit(analysis, pie_svg, bar_svg, treemap_svg)
        except Exception as e:
            self.error.emit(str(e))


class AnalyticsTab(QWidget):
    """Analytics tab for project analysis and visualization."""
    
    def __init__(self):
        super().__init__()
        self._init_ui()
        self._worker = None
    
    def _init_ui(self):
        """Initialize the UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Header
        header_layout = QHBoxLayout()
        header_layout.addWidget(QLabel("📊 Project Analytics"))
        header_layout.addStretch()
        layout.addLayout(header_layout)
        
        # Input card
        input_card = CardWidget("Analysis Input")
        input_layout = QHBoxLayout(input_card)
        
        input_layout.addWidget(QLabel("Project Path:"))
        self.path_input = FileInputWidget(mode='folder')
        input_layout.addWidget(self.path_input, stretch=1)
        
        self.analyze_btn = QPushButton("🔍 Analyze")
        self.analyze_btn.setObjectName("primaryButton")
        self.analyze_btn.clicked.connect(self._start_analysis)
        input_layout.addWidget(self.analyze_btn)
        
        layout.addWidget(input_card)
        
        # Progress
        self.progress = ProgressWidget()
        self.progress.hide()
        layout.addWidget(self.progress)
        
        # Stats row
        stats_layout = QHBoxLayout()
        
        self.files_stat = StatCard("Total Files", "0")
        stats_layout.addWidget(self.files_stat)
        
        self.dirs_stat = StatCard("Directories", "0")
        stats_layout.addWidget(self.dirs_stat)
        
        self.size_stat = StatCard("Total Size", "0 B")
        stats_layout.addWidget(self.size_stat)
        
        self.lines_stat = StatCard("Lines of Code", "0")
        stats_layout.addWidget(self.lines_stat)
        
        self.duplicates_stat = StatCard("Duplicates", "0")
        stats_layout.addWidget(self.duplicates_stat)
        
        layout.addLayout(stats_layout)
        
        # Charts area (scrollable)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        
        charts_widget = QWidget()
        charts_layout = QVBoxLayout(charts_widget)
        charts_layout.setSpacing(20)
        
        # Charts row 1
        row1 = QHBoxLayout()
        
        self.pie_card = CardWidget("File Type Distribution")
        self.pie_view = QWebEngineView()
        self.pie_view.setMinimumHeight(300)
        pie_layout = QVBoxLayout(self.pie_card)
        pie_layout.addWidget(self.pie_view)
        row1.addWidget(self.pie_card)
        
        self.bar_card = CardWidget("Files by Extension")
        self.bar_view = QWebEngineView()
        self.bar_view.setMinimumHeight(300)
        bar_layout = QVBoxLayout(self.bar_card)
        bar_layout.addWidget(self.bar_view)
        row1.addWidget(self.bar_card)
        
        charts_layout.addLayout(row1)
        
        # Charts row 2
        row2 = QHBoxLayout()
        
        self.treemap_card = CardWidget("Directory Size Distribution")
        self.treemap_view = QWebEngineView()
        self.treemap_view.setMinimumHeight(300)
        treemap_layout = QVBoxLayout(self.treemap_card)
        treemap_layout.addWidget(self.treemap_view)
        row2.addWidget(self.treemap_card)
        
        charts_layout.addLayout(row2)
        
        # File types table
        types_card = CardWidget("File Types Summary")
        types_layout = QVBoxLayout(types_card)
        
        self.types_table = QTableWidget()
        self.types_table.setColumnCount(4)
        self.types_table.setHorizontalHeaderLabels(['Extension', 'Count', 'Total Size', 'Avg Size'])
        self.types_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.types_table.setAlternatingRowColors(True)
        types_layout.addWidget(self.types_table)
        
        charts_layout.addWidget(types_card)
        
        scroll.setWidget(charts_widget)
        layout.addWidget(scroll, stretch=1)
    
    def _start_analysis(self):
        """Start analysis operation."""
        path = self.path_input.get_path()
        if not path or not Path(path).exists():
            return
        
        self.progress.start_indeterminate("Analyzing project...")
        self.analyze_btn.setEnabled(False)
        
        self._worker = AnalyticsWorker(Path(path))
        self._worker.progress.connect(self._on_progress)
        self._worker.finished.connect(self._on_analysis_complete)
        self._worker.error.connect(self._on_analysis_error)
        self._worker.start()
    
    def _on_progress(self, message: str):
        """Handle progress update."""
        self.progress.start_indeterminate(message)
    
    def _on_analysis_complete(self, analysis, pie_svg, bar_svg, treemap_svg):
        """Handle analysis completion."""
        self.progress.stop()
        self.analyze_btn.setEnabled(True)
        
        # Update stats
        self.files_stat.set_value(str(analysis.total_files))
        self.dirs_stat.set_value(str(analysis.total_directories))
        self.size_stat.set_value(self._format_size(analysis.total_size))
        self.lines_stat.set_value(str(analysis.total_lines))
        self.duplicates_stat.set_value(str(analysis.duplicate_count))
        
        # Update charts
        self._load_svg(self.pie_view, pie_svg)
        self._load_svg(self.bar_view, bar_svg)
        self._load_svg(self.treemap_view, treemap_svg)
        
        # Update types table
        types = sorted(
            analysis.file_types.items(),
            key=lambda x: x[1].count,
            reverse=True
        )[:20]
        
        self.types_table.setRowCount(len(types))
        for i, (ext, stats) in enumerate(types):
            self.types_table.setItem(i, 0, QTableWidgetItem(ext or '(no ext)'))
            self.types_table.setItem(i, 1, QTableWidgetItem(str(stats.count)))
            self.types_table.setItem(i, 2, QTableWidgetItem(self._format_size(stats.total_size)))
            self.types_table.setItem(i, 3, QTableWidgetItem(self._format_size(int(stats.avg_size))))
    
    def _on_analysis_error(self, error: str):
        """Handle analysis error."""
        self.progress.stop()
        self.analyze_btn.setEnabled(True)
    
    def _load_svg(self, view: QWebEngineView, svg: str):
        """Load SVG into web view."""
        html = f'''<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ margin: 0; background: #1e1e38; display: flex; justify-content: center; align-items: center; }}
        svg {{ max-width: 100%; height: auto; }}
    </style>
</head>
<body>{svg}</body>
</html>'''
        view.setHtml(html)
    
    def _format_size(self, size: int) -> str:
        """Format size in human readable form."""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"
