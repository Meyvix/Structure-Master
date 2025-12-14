"""
StructureMaster - Main GUI Window
Beautiful modern interface with tabbed navigation.
"""

import sys
from pathlib import Path
from typing import Optional

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTabWidget, QLabel, QPushButton, QFrame, QStatusBar, QMenuBar,
    QMenu, QMessageBox, QSplitter, QStackedWidget, QSizePolicy
)
from PyQt6.QtCore import Qt, QSize, QTimer, pyqtSignal
from PyQt6.QtGui import QIcon, QFont, QAction, QColor, QPalette

from .styles import MAIN_STYLE, COLORS
from .tabs.structure_builder_tab import StructureBuilderTab
from .tabs.structure_extractor_tab import StructureExtractorTab
from .tabs.content_extractor_tab import ContentExtractorTab
from .tabs.settings_tab import SettingsTab
from .components import LogViewerWidget, create_sidebar_button


class MainWindow(QMainWindow):
    """Main application window."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("StructureMaster v1.0")
        self.setMinimumSize(1200, 800)
        self.resize(1400, 900)
        
        # Apply styling
        self.setStyleSheet(MAIN_STYLE)
        
        # Setup UI
        self._setup_ui()
        self._setup_menu()
        self._setup_status_bar()
        
        # Center window
        self._center_on_screen()
    
    def _setup_ui(self):
        """Setup main UI layout."""
        # Central widget
        central = QWidget()
        self.setCentralWidget(central)
        
        # Main layout
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Sidebar
        sidebar = self._create_sidebar()
        main_layout.addWidget(sidebar)
        
        # Content area
        content_area = self._create_content_area()
        main_layout.addWidget(content_area, 1)
    
    def _create_sidebar(self) -> QFrame:
        """Create sidebar with navigation."""
        sidebar = QFrame()
        sidebar.setFixedWidth(280)
        sidebar.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['bg_secondary']};
                border-right: 1px solid {COLORS['border']};
            }}
        """)
        
        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Logo/Title
        title_frame = QFrame()
        title_layout = QVBoxLayout(title_frame)
        title_layout.setContentsMargins(0, 0, 0, 20)
        
        title = QLabel("StructureMaster")
        title.setStyleSheet(f"""
            font-size: 22px;
            font-weight: bold;
            color: {COLORS['accent_primary']};
        """)
        title_layout.addWidget(title)
        
        subtitle = QLabel("Project Structure Tool")
        subtitle.setStyleSheet(f"""
            font-size: 12px;
            color: {COLORS['text_muted']};
        """)
        title_layout.addWidget(subtitle)
        
        layout.addWidget(title_frame)
        
        # Navigation buttons
        self.nav_buttons = []
        nav_items = [
            ("🔨", "Structure Builder", "Build project from structure"),
            ("📂", "Extract Structure", "Extract from existing project"),
            ("📄", "Extract Content", "Extract file contents"),
            ("⚙️", "Settings", "Configure application"),
        ]
        
        for icon, text, tooltip in nav_items:
            btn = create_sidebar_button(icon, text, tooltip)
            btn.clicked.connect(lambda checked, t=text: self._on_nav_click(t))
            layout.addWidget(btn)
            self.nav_buttons.append((text, btn))
        
        # Set first button as active
        if self.nav_buttons:
            self._set_active_nav(self.nav_buttons[0][0])
        
        layout.addStretch()
        
        # Version info
        version = QLabel("v1.0.0")
        version.setStyleSheet(f"""
            color: {COLORS['text_muted']};
            font-size: 11px;
        """)
        version.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(version)
        
        return sidebar
    
    def _create_content_area(self) -> QWidget:
        """Create main content area."""
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Header
        header = self._create_header()
        layout.addWidget(header)
        
        # Stacked widget for tabs
        self.stack = QStackedWidget()
        self.stack.setStyleSheet(f"""
            QStackedWidget {{
                background-color: {COLORS['bg_primary']};
            }}
        """)
        
        # Add tabs
        self.builder_tab = StructureBuilderTab()
        self.extractor_tab = StructureExtractorTab()
        self.content_tab = ContentExtractorTab()
        self.settings_tab = SettingsTab()
        
        self.stack.addWidget(self.builder_tab)
        self.stack.addWidget(self.extractor_tab)
        self.stack.addWidget(self.content_tab)
        self.stack.addWidget(self.settings_tab)
        
        layout.addWidget(self.stack, 1)
        
        return content
    
    def _create_header(self) -> QFrame:
        """Create header bar."""
        header = QFrame()
        header.setFixedHeight(60)
        header.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['bg_secondary']};
                border-bottom: 1px solid {COLORS['border']};
            }}
        """)
        
        layout = QHBoxLayout(header)
        layout.setContentsMargins(25, 0, 25, 0)
        
        # Page title (will be updated)
        self.page_title = QLabel("Structure Builder")
        self.page_title.setStyleSheet(f"""
            font-size: 18px;
            font-weight: 600;
            color: {COLORS['text_primary']};
        """)
        layout.addWidget(self.page_title)
        
        layout.addStretch()
        
        # Quick actions
        help_btn = QPushButton("📖 Help")
        help_btn.setObjectName("secondary")
        help_btn.setFixedWidth(100)
        help_btn.clicked.connect(self._show_help)
        layout.addWidget(help_btn)
        
        return header
    
    def _setup_menu(self):
        """Setup menu bar."""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("File")
        
        new_action = QAction("New Project", self)
        new_action.setShortcut("Ctrl+N")
        file_menu.addAction(new_action)
        
        open_action = QAction("Open Structure...", self)
        open_action.setShortcut("Ctrl+O")
        file_menu.addAction(open_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("Exit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Edit menu
        edit_menu = menubar.addMenu("Edit")
        
        prefs_action = QAction("Preferences", self)
        prefs_action.triggered.connect(lambda: self._on_nav_click("Settings"))
        edit_menu.addAction(prefs_action)
        
        # Tools menu
        tools_menu = menubar.addMenu("Tools")
        
        scan_action = QAction("Scan Project", self)
        scan_action.triggered.connect(lambda: self._on_nav_click("Extract Structure"))
        tools_menu.addAction(scan_action)
        
        build_action = QAction("Build Structure", self)
        build_action.triggered.connect(lambda: self._on_nav_click("Structure Builder"))
        tools_menu.addAction(build_action)
        
        tools_menu.addSeparator()
        
        compare_action = QAction("Compare Projects", self)
        tools_menu.addAction(compare_action)
        
        # Help menu
        help_menu = menubar.addMenu("Help")
        
        docs_action = QAction("Documentation", self)
        docs_action.triggered.connect(self._show_help)
        help_menu.addAction(docs_action)
        
        help_menu.addSeparator()
        
        about_action = QAction("About StructureMaster", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)
    
    def _setup_status_bar(self):
        """Setup status bar."""
        status = self.statusBar()
        status.showMessage("Ready")
    
    def _on_nav_click(self, name: str):
        """Handle navigation button click."""
        self._set_active_nav(name)
        
        # Update page
        pages = {
            "Structure Builder": (0, "Structure Builder"),
            "Extract Structure": (1, "Extract Structure"),
            "Extract Content": (2, "Extract Content"),
            "Settings": (3, "Settings"),
        }
        
        if name in pages:
            idx, title = pages[name]
            self.stack.setCurrentIndex(idx)
            self.page_title.setText(title)
    
    def _set_active_nav(self, active_name: str):
        """Set active navigation button."""
        for name, btn in self.nav_buttons:
            if name == active_name:
                btn.setStyleSheet(f"""
                    QPushButton {{
                        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                            stop:0 {COLORS['accent_gradient_start']},
                            stop:1 {COLORS['accent_gradient_end']});
                        color: white;
                        border: none;
                        border-radius: 10px;
                        padding: 12px 15px;
                        text-align: left;
                        font-weight: 600;
                    }}
                """)
            else:
                btn.setStyleSheet(f"""
                    QPushButton {{
                        background: transparent;
                        color: {COLORS['text_secondary']};
                        border: none;
                        border-radius: 10px;
                        padding: 12px 15px;
                        text-align: left;
                    }}
                    QPushButton:hover {{
                        background: {COLORS['bg_hover']};
                        color: {COLORS['text_primary']};
                    }}
                """)
    
    def _center_on_screen(self):
        """Center window on screen."""
        screen = QApplication.primaryScreen()
        if screen:
            center = screen.availableGeometry().center()
            geo = self.frameGeometry()
            geo.moveCenter(center)
            self.move(geo.topLeft())
    
    def _show_help(self):
        """Show help dialog."""
        QMessageBox.information(
            self,
            "Help",
            "StructureMaster v1.0\n\n"
            "A comprehensive tool for project structure analysis, "
            "generation, and documentation.\n\n"
            "• Structure Builder: Create projects from structure files\n"
            "• Extract Structure: Scan and extract project structure\n"
            "• Extract Content: Extract file contents with metadata\n\n"
            "For detailed documentation, see docs/README_FA.md"
        )
    
    def _show_about(self):
        """Show about dialog."""
        QMessageBox.about(
            self,
            "About StructureMaster",
            "<h2>StructureMaster</h2>"
            "<p>Version 1.0.0</p>"
            "<p>A comprehensive, intelligent, and extensible tool for "
            "project structure analysis, generation, and documentation.</p>"
            "<p><b>Features:</b></p>"
            "<ul>"
            "<li>Structure Building & Extraction</li>"
            "<li>Content Extraction with Metadata</li>"
            "<li>AES-256 Encryption</li>"
            "<li>Multi-format Export</li>"
            "<li>Project Type Detection</li>"
            "</ul>"
        )


def main():
    """Main entry point for GUI."""
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    
    # Set application properties
    app.setApplicationName("StructureMaster")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("StructureMaster")
    
    # Create and show main window
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
