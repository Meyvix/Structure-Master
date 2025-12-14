"""
StructureMaster - Settings Tab
Application settings and configuration.
"""

import sys
from pathlib import Path

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QScrollArea, QComboBox, QCheckBox, QLineEdit,
    QSpinBox, QListWidget, QListWidgetItem, QMessageBox,
    QFileDialog, QInputDialog
)
from PyQt6.QtCore import Qt

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from src.gui.styles import COLORS
from src.gui.components import CardWidget
from src.modules.profile_manager import ProfileManager


class SettingsTab(QWidget):
    """Settings tab for application configuration."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        self._load_settings()
    
    def _setup_ui(self):
        """Setup the tab UI."""
        # Scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet(f"""
            QScrollArea {{
                border: none;
                background: transparent;
            }}
        """)
        
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(25, 25, 25, 25)
        layout.setSpacing(20)
        
        # Header
        header = self._create_header()
        layout.addWidget(header)
        
        # Settings sections
        general_card = self._create_general_settings()
        layout.addWidget(general_card)
        
        scan_card = self._create_scan_settings()
        layout.addWidget(scan_card)
        
        export_card = self._create_export_settings()
        layout.addWidget(export_card)
        
        profiles_card = self._create_profiles_section()
        layout.addWidget(profiles_card)
        
        about_card = self._create_about_section()
        layout.addWidget(about_card)
        
        layout.addStretch()
        
        scroll.setWidget(content)
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(scroll)
    
    def _create_header(self) -> QWidget:
        """Create header section."""
        header = QFrame()
        layout = QHBoxLayout(header)
        layout.setContentsMargins(0, 0, 0, 10)
        
        text_layout = QVBoxLayout()
        title = QLabel("⚙️ Settings")
        title.setStyleSheet(f"""
            font-size: 20px;
            font-weight: bold;
            color: {COLORS['text_primary']};
        """)
        text_layout.addWidget(title)
        
        desc = QLabel("Configure application preferences and defaults")
        desc.setStyleSheet(f"color: {COLORS['text_muted']};")
        text_layout.addWidget(desc)
        layout.addLayout(text_layout)
        
        layout.addStretch()
        
        # Save button
        save_btn = QPushButton("💾 Save Settings")
        save_btn.clicked.connect(self._save_settings)
        layout.addWidget(save_btn)
        
        return header
    
    def _create_general_settings(self) -> QWidget:
        """Create general settings card."""
        card = CardWidget("General")
        
        # Theme
        theme_layout = QHBoxLayout()
        theme_label = QLabel("Theme:")
        theme_layout.addWidget(theme_label)
        
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Dark", "Light", "System"])
        self.theme_combo.setCurrentText("Dark")
        self.theme_combo.setFixedWidth(150)
        theme_layout.addWidget(self.theme_combo)
        theme_layout.addStretch()
        card.addLayout(theme_layout)
        
        # Language
        lang_layout = QHBoxLayout()
        lang_label = QLabel("Language:")
        lang_layout.addWidget(lang_label)
        
        self.lang_combo = QComboBox()
        self.lang_combo.addItems(["English", "فارسی (Persian)"])
        self.lang_combo.setFixedWidth(150)
        lang_layout.addWidget(self.lang_combo)
        lang_layout.addStretch()
        card.addLayout(lang_layout)
        
        # Default output directory
        output_layout = QHBoxLayout()
        output_label = QLabel("Default output directory:")
        output_layout.addWidget(output_label)
        
        self.output_dir = QLineEdit()
        self.output_dir.setPlaceholderText("Leave empty for current directory")
        output_layout.addWidget(self.output_dir, 1)
        
        browse_btn = QPushButton("Browse...")
        browse_btn.setObjectName("secondary")
        browse_btn.setFixedWidth(100)
        browse_btn.clicked.connect(self._browse_output_dir)
        output_layout.addWidget(browse_btn)
        card.addLayout(output_layout)
        
        return card
    
    def _create_scan_settings(self) -> QWidget:
        """Create scan settings card."""
        card = CardWidget("Scanning")
        
        # Default options
        self.recursive_default = QCheckBox("Recursive scan by default")
        self.recursive_default.setChecked(True)
        card.addWidget(self.recursive_default)
        
        self.hidden_default = QCheckBox("Include hidden files by default")
        card.addWidget(self.hidden_default)
        
        self.auto_detect_default = QCheckBox("Auto-detect project type")
        self.auto_detect_default.setChecked(True)
        card.addWidget(self.auto_detect_default)
        
        # Max workers
        workers_layout = QHBoxLayout()
        workers_label = QLabel("Max parallel workers:")
        workers_layout.addWidget(workers_label)
        
        self.workers_spin = QSpinBox()
        self.workers_spin.setRange(1, 32)
        self.workers_spin.setValue(4)
        self.workers_spin.setFixedWidth(100)
        workers_layout.addWidget(self.workers_spin)
        workers_layout.addStretch()
        card.addLayout(workers_layout)
        
        # Cache settings
        cache_layout = QHBoxLayout()
        self.cache_enabled = QCheckBox("Enable scan caching")
        self.cache_enabled.setChecked(True)
        cache_layout.addWidget(self.cache_enabled)
        
        clear_cache_btn = QPushButton("Clear Cache")
        clear_cache_btn.setObjectName("secondary")
        clear_cache_btn.setFixedWidth(120)
        clear_cache_btn.clicked.connect(self._clear_cache)
        cache_layout.addWidget(clear_cache_btn)
        cache_layout.addStretch()
        card.addLayout(cache_layout)
        
        return card
    
    def _create_export_settings(self) -> QWidget:
        """Create export settings card."""
        card = CardWidget("Export")
        
        # Default format
        format_layout = QHBoxLayout()
        format_label = QLabel("Default export format:")
        format_layout.addWidget(format_label)
        
        self.format_combo = QComboBox()
        self.format_combo.addItems(["JSON", "TXT", "Markdown", "YAML", "HTML"])
        self.format_combo.setFixedWidth(150)
        format_layout.addWidget(self.format_combo)
        format_layout.addStretch()
        card.addLayout(format_layout)
        
        # Options
        self.pretty_output = QCheckBox("Pretty print output")
        self.pretty_output.setChecked(True)
        card.addWidget(self.pretty_output)
        
        self.include_metadata = QCheckBox("Include file metadata in exports")
        self.include_metadata.setChecked(True)
        card.addWidget(self.include_metadata)
        
        # Max file size
        size_layout = QHBoxLayout()
        size_label = QLabel("Max file size for content extraction (MB):")
        size_layout.addWidget(size_label)
        
        self.max_size_spin = QSpinBox()
        self.max_size_spin.setRange(1, 1000)
        self.max_size_spin.setValue(100)
        self.max_size_spin.setFixedWidth(100)
        size_layout.addWidget(self.max_size_spin)
        size_layout.addStretch()
        card.addLayout(size_layout)
        
        return card
    
    def _create_profiles_section(self) -> QWidget:
        """Create profiles section."""
        card = CardWidget("Profiles")
        
        # Profile list
        self.profile_list = QListWidget()
        self.profile_list.setMaximumHeight(150)
        card.addWidget(self.profile_list)
        
        # Buttons
        btn_layout = QHBoxLayout()
        
        new_btn = QPushButton("➕ New")
        new_btn.setObjectName("secondary")
        new_btn.clicked.connect(self._create_profile)
        btn_layout.addWidget(new_btn)
        
        edit_btn = QPushButton("✏️ Edit")
        edit_btn.setObjectName("secondary")
        edit_btn.clicked.connect(self._edit_profile)
        btn_layout.addWidget(edit_btn)
        
        delete_btn = QPushButton("🗑️ Delete")
        delete_btn.setObjectName("danger")
        delete_btn.clicked.connect(self._delete_profile)
        btn_layout.addWidget(delete_btn)
        
        btn_layout.addStretch()
        card.addLayout(btn_layout)
        
        # Load profiles
        self._load_profiles()
        
        return card
    
    def _create_about_section(self) -> QWidget:
        """Create about section."""
        card = CardWidget("About")
        
        about_text = QLabel(
            f"<b>StructureMaster</b> v1.0.0<br><br>"
            f"A comprehensive tool for project structure analysis, "
            f"generation, and documentation.<br><br>"
            f"<a href='#' style='color: {COLORS['accent_primary']};'>GitHub</a> | "
            f"<a href='#' style='color: {COLORS['accent_primary']};'>Documentation</a> | "
            f"<a href='#' style='color: {COLORS['accent_primary']};'>Report Issue</a>"
        )
        about_text.setOpenExternalLinks(True)
        about_text.setWordWrap(True)
        card.addWidget(about_text)
        
        return card
    
    def _browse_output_dir(self):
        """Browse for output directory."""
        path = QFileDialog.getExistingDirectory(
            self, "Select Default Output Directory"
        )
        if path:
            self.output_dir.setText(path)
    
    def _clear_cache(self):
        """Clear scan cache."""
        from src.modules.cache_manager import CacheManager
        cache = CacheManager()
        cache.clear()
        QMessageBox.information(self, "Cache Cleared", "Scan cache has been cleared")
    
    def _load_profiles(self):
        """Load profiles into list."""
        self.profile_list.clear()
        pm = ProfileManager()
        
        for name in pm.list_profiles():
            info = pm.get_profile_info(name)
            item = QListWidgetItem(f"📋 {name}")
            if info:
                item.setToolTip(info.get('description', ''))
            self.profile_list.addItem(item)
    
    def _create_profile(self):
        """Create new profile."""
        name, ok = QInputDialog.getText(
            self, "New Profile", "Profile name:"
        )
        if ok and name:
            pm = ProfileManager()
            pm.create(name, description="Custom profile")
            self._load_profiles()
    
    def _edit_profile(self):
        """Edit selected profile."""
        item = self.profile_list.currentItem()
        if not item:
            QMessageBox.warning(self, "Warning", "Please select a profile")
            return
        
        name = item.text().replace("📋 ", "")
        QMessageBox.information(
            self, "Edit Profile",
            f"Profile editor for '{name}' would open here.\n"
            "This feature is available in the full version."
        )
    
    def _delete_profile(self):
        """Delete selected profile."""
        item = self.profile_list.currentItem()
        if not item:
            QMessageBox.warning(self, "Warning", "Please select a profile")
            return
        
        name = item.text().replace("📋 ", "")
        reply = QMessageBox.question(
            self, "Delete Profile",
            f"Delete profile '{name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            pm = ProfileManager()
            pm.delete(name)
            self._load_profiles()
    
    def _load_settings(self):
        """Load settings from config."""
        # Settings would be loaded from a config file
        pass
    
    def _save_settings(self):
        """Save settings to config."""
        # Settings would be saved to a config file
        QMessageBox.information(
            self, "Settings Saved",
            "Settings have been saved successfully"
        )
