"""
Stracture-Master - GUI Components
Reusable UI components for the application.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QTreeWidget, QTreeWidgetItem, QPlainTextEdit,
    QProgressBar, QSizePolicy, QScrollArea, QLineEdit,
    QFileDialog, QDialog, QDialogButtonBox, QTextEdit
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QColor

from .styles import COLORS, LOG_VIEWER_STYLE


class CardWidget(QFrame):
    """Modern card container widget."""
    
    def __init__(self, title: str = "", parent=None):
        super().__init__(parent)
        self.setObjectName("card")
        self.setStyleSheet(f"""
            QFrame#card {{
                background-color: {COLORS['bg_card']};
                border: 1px solid {COLORS['border']};
                border-radius: 16px;
            }}
        """)
        
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(20, 20, 20, 20)
        self.layout.setSpacing(12)
        
        if title:
            title_label = QLabel(title)
            title_label.setStyleSheet(f"""
                font-size: 15px;
                font-weight: 600;
                color: {COLORS['text_primary']};
                background: transparent;
                padding: 0px;
                margin: 0px;
            """)
            title_label.setMinimumHeight(24)
            title_label.setWordWrap(True)
            self.layout.addWidget(title_label)
    
    def addWidget(self, widget):
        self.layout.addWidget(widget)
    
    def addLayout(self, layout):
        self.layout.addLayout(layout)


class StatCard(QFrame):
    """Statistics display card."""
    
    def __init__(self, label: str, value: str, icon: str = "", parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['bg_tertiary']};
                border: 1px solid {COLORS['border']};
                border-radius: 12px;
            }}
        """)
        
        # Set minimum size to ensure text fits
        self.setMinimumWidth(140)
        self.setMinimumHeight(100)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(4)
        
        # Icon row (if icon)
        if icon:
            icon_label = QLabel(icon)
            icon_label.setStyleSheet("font-size: 18px; background: transparent;")
            icon_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
            layout.addWidget(icon_label)
        
        # Label
        label_widget = QLabel(label)
        label_widget.setStyleSheet(f"""
            font-size: 11px;
            color: {COLORS['text_muted']};
            background: transparent;
        """)
        label_widget.setWordWrap(True)
        layout.addWidget(label_widget)
        
        # Value
        self.value_label = QLabel(value)
        self.value_label.setStyleSheet(f"""
            font-size: 20px;
            font-weight: bold;
            color: {COLORS['accent_primary']};
            background: transparent;
        """)
        self.value_label.setWordWrap(True)
        layout.addWidget(self.value_label)
        
        layout.addStretch()
    
    def set_value(self, value: str):
        self.value_label.setText(value)


class TreeViewWidget(QTreeWidget):
    """Enhanced tree view for project structure."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setHeaderHidden(True)
        self.setIndentation(20)
        self.setAnimated(True)
        self.setStyleSheet(f"""
            QTreeWidget {{
                background-color: {COLORS['bg_tertiary']};
                border: 1px solid {COLORS['border']};
                border-radius: 8px;
                padding: 10px;
            }}
            QTreeWidget::item {{
                padding: 6px 5px;
                border-radius: 4px;
            }}
            QTreeWidget::item:hover {{
                background-color: {COLORS['bg_hover']};
            }}
            QTreeWidget::item:selected {{
                background-color: {COLORS['accent_primary']};
            }}
        """)
    
    def load_structure(self, structure: dict, parent_item=None):
        """Load structure dict into tree."""
        self.clear()
        self._add_items(structure, None)
    
    def _add_items(self, structure: dict, parent):
        """Recursively add items."""
        # Sort: directories first, then files
        items = sorted(structure.items(), 
                      key=lambda x: (not isinstance(x[1], dict), x[0].lower()))
        
        for name, content in items:
            if parent is None:
                item = QTreeWidgetItem(self)
            else:
                item = QTreeWidgetItem(parent)
            
            is_dir = isinstance(content, dict)
            icon = "📁" if is_dir else self._get_file_icon(name)
            item.setText(0, f"{icon} {name}")
            item.setData(0, Qt.ItemDataRole.UserRole, {'name': name, 'is_dir': is_dir})
            
            if is_dir and content:
                self._add_items(content, item)
                item.setExpanded(True)
    
    def _get_file_icon(self, filename: str) -> str:
        """Get icon for file type."""
        ext = filename.split('.')[-1].lower() if '.' in filename else ''
        icons = {
            'py': '🐍', 'js': '📜', 'ts': '📘', 'jsx': '⚛️', 'tsx': '⚛️',
            'html': '🌐', 'css': '🎨', 'json': '📋', 'md': '📝',
            'txt': '📄', 'yaml': '⚙️', 'yml': '⚙️', 'sql': '🗄️',
            'go': '🔵', 'rs': '🦀', 'java': '☕', 'php': '🐘',
            'rb': '💎', 'vue': '💚', 'svelte': '🔥',
        }
        return icons.get(ext, '📄')
    
    def get_structure(self) -> dict:
        """Get structure dict from tree."""
        structure = {}
        for i in range(self.topLevelItemCount()):
            item = self.topLevelItem(i)
            self._item_to_dict(item, structure)
        return structure
    
    def _item_to_dict(self, item, parent_dict):
        """Convert tree item to dict."""
        data = item.data(0, Qt.ItemDataRole.UserRole)
        if data:
            name = data['name']
            if data['is_dir']:
                parent_dict[name] = {}
                for i in range(item.childCount()):
                    self._item_to_dict(item.child(i), parent_dict[name])
            else:
                parent_dict[name] = None


class LogViewerWidget(QPlainTextEdit):
    """Log viewer with syntax highlighting."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setReadOnly(True)
        self.setObjectName("logViewer")
        self.setStyleSheet(LOG_VIEWER_STYLE)
        self.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        
        # Set monospace font
        font = QFont("Consolas", 10)
        self.setFont(font)
    
    def add_log(self, message: str, level: str = "INFO"):
        """Add a log message."""
        colors = {
            'TRACE': COLORS['text_muted'],
            'DEBUG': '#00bcd4',
            'INFO': COLORS['success'],
            'WARN': COLORS['warning'],
            'ERROR': COLORS['error'],
            'CRITICAL': '#9c27b0',
        }
        color = colors.get(level.upper(), COLORS['text_secondary'])
        
        from datetime import datetime
        timestamp = datetime.now().strftime('%H:%M:%S')
        
        # Append with color (simplified - actual implementation would use HTML)
        self.appendPlainText(f"[{timestamp}] [{level:8}] {message}")
        
        # Auto scroll to bottom
        scrollbar = self.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def clear_logs(self):
        """Clear all logs."""
        self.clear()


class FileInputWidget(QWidget):
    """File/folder input with browse button."""
    
    pathChanged = pyqtSignal(str)
    
    def __init__(self, placeholder: str = "Select path...", 
                 mode: str = "file", parent=None):
        super().__init__(parent)
        self.mode = mode  # 'file' or 'folder'
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        
        self.input = QLineEdit()
        self.input.setPlaceholderText(placeholder)
        self.input.textChanged.connect(self.pathChanged.emit)
        layout.addWidget(self.input, 1)
        
        self.browse_btn = QPushButton("Browse...")
        self.browse_btn.setObjectName("secondary")
        self.browse_btn.setFixedWidth(100)
        self.browse_btn.clicked.connect(self._browse)
        layout.addWidget(self.browse_btn)
    
    def _browse(self):
        """Open file/folder dialog."""
        if self.mode == "folder":
            path = QFileDialog.getExistingDirectory(
                self, "Select Folder", self.input.text()
            )
        else:
            path, _ = QFileDialog.getOpenFileName(
                self, "Select File", self.input.text()
            )
        
        if path:
            self.input.setText(path)
    
    def get_path(self) -> str:
        return self.input.text()
    
    def set_path(self, path: str):
        self.input.setText(path)


class ProgressWidget(QWidget):
    """Progress indicator with label."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)
        
        # Label row
        label_row = QHBoxLayout()
        self.label = QLabel("Ready")
        self.label.setStyleSheet(f"color: {COLORS['text_secondary']};")
        label_row.addWidget(self.label)
        
        self.percent_label = QLabel("")
        self.percent_label.setStyleSheet(f"color: {COLORS['text_muted']};")
        label_row.addWidget(self.percent_label)
        label_row.addStretch()
        layout.addLayout(label_row)
        
        # Progress bar
        self.progress = QProgressBar()
        self.progress.setStyleSheet(f"""
            QProgressBar {{
                background-color: {COLORS['bg_tertiary']};
                border: none;
                border-radius: 6px;
                height: 8px;
            }}
            QProgressBar::chunk {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {COLORS['accent_gradient_start']},
                    stop:1 {COLORS['accent_gradient_end']});
                border-radius: 6px;
            }}
        """)
        self.progress.setTextVisible(False)
        layout.addWidget(self.progress)
        
        self.hide()
    
    def start(self, message: str = "Processing..."):
        """Start indeterminate progress."""
        self.label.setText(message)
        self.percent_label.setText("")
        self.progress.setRange(0, 0)  # Indeterminate
        self.show()
    
    def update_progress(self, value: int, total: int, message: str = ""):
        """Update progress."""
        self.progress.setRange(0, total)
        self.progress.setValue(value)
        percent = int(value / total * 100) if total > 0 else 0
        self.percent_label.setText(f"{percent}%")
        if message:
            self.label.setText(message)
        self.show()
    
    def finish(self, message: str = "Complete"):
        """Mark progress as complete."""
        self.progress.setRange(0, 100)
        self.progress.setValue(100)
        self.percent_label.setText("100%")
        self.label.setText(message)
        
        # Hide after delay
        QTimer.singleShot(2000, self.hide)


class ConfirmDialog(QDialog):
    """Modern confirmation dialog."""
    
    def __init__(self, title: str, message: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setMinimumWidth(400)
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {COLORS['bg_primary']};
            }}
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(25, 25, 25, 25)
        layout.setSpacing(20)
        
        # Message
        msg_label = QLabel(message)
        msg_label.setWordWrap(True)
        msg_label.setStyleSheet(f"""
            font-size: 14px;
            color: {COLORS['text_primary']};
        """)
        layout.addWidget(msg_label)
        
        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setObjectName("secondary")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        
        confirm_btn = QPushButton("Confirm")
        confirm_btn.clicked.connect(self.accept)
        btn_layout.addWidget(confirm_btn)
        
        layout.addLayout(btn_layout)


def create_sidebar_button(icon: str, text: str, tooltip: str = "") -> QPushButton:
    """Create a sidebar navigation button."""
    btn = QPushButton(f"  {icon}  {text}")
    btn.setToolTip(tooltip)
    btn.setFixedHeight(48)
    btn.setStyleSheet(f"""
        QPushButton {{
            background: transparent;
            color: {COLORS['text_secondary']};
            border: none;
            border-radius: 10px;
            padding: 12px 15px;
            text-align: left;
            font-size: 14px;
        }}
        QPushButton:hover {{
            background: {COLORS['bg_hover']};
            color: {COLORS['text_primary']};
        }}
    """)
    return btn
