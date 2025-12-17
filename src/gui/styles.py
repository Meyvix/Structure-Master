"""
Stracture-Master - GUI Styles Module
Modern dark theme styling for PyQt6.
"""

# Modern Dark Theme Colors
DARK_COLORS = {
    'bg_primary': '#0f0f1a',
    'bg_secondary': '#1a1a2e',
    'bg_tertiary': '#252542',
    'bg_card': '#1e1e38',
    'bg_hover': '#2d2d52',
    'bg_selected': '#3d3d6d',
    
    'text_primary': '#ffffff',
    'text_secondary': '#b0b0c0',
    'text_muted': '#6e6e8a',
    'text_disabled': '#4a4a5e',
    
    'accent_primary': '#7c3aed',
    'accent_secondary': '#a855f7',
    'accent_gradient_start': '#667eea',
    'accent_gradient_end': '#764ba2',
    
    'success': '#10b981',
    'warning': '#f59e0b',
    'error': '#ef4444',
    'info': '#3b82f6',
    
    'border': '#3d3d5c',
    'border_hover': '#5d5d8c',
    'border_focus': '#7c3aed',
    
    'scrollbar_bg': '#1a1a2e',
    'scrollbar_handle': '#3d3d5c',
    'scrollbar_handle_hover': '#5d5d7c',
}

# Modern Light Theme Colors
LIGHT_COLORS = {
    'bg_primary': '#f5f5f7',
    'bg_secondary': '#ffffff',
    'bg_tertiary': '#e8e8ed',
    'bg_card': '#ffffff',
    'bg_hover': '#e0e0e8',
    'bg_selected': '#d0d0e0',
    
    'text_primary': '#1a1a2e',
    'text_secondary': '#4a4a5e',
    'text_muted': '#6e6e8a',
    'text_disabled': '#a0a0b0',
    
    'accent_primary': '#7c3aed',
    'accent_secondary': '#a855f7',
    'accent_gradient_start': '#667eea',
    'accent_gradient_end': '#764ba2',
    
    'success': '#10b981',
    'warning': '#f59e0b',
    'error': '#ef4444',
    'info': '#3b82f6',
    
    'border': '#d0d0dc',
    'border_hover': '#b0b0c0',
    'border_focus': '#7c3aed',
    
    'scrollbar_bg': '#e8e8ed',
    'scrollbar_handle': '#c0c0d0',
    'scrollbar_handle_hover': '#a0a0b0',
}

# Current theme (default: dark)
COLORS = DARK_COLORS.copy()

def get_theme_colors(theme_name: str) -> dict:
    """Get colors for a specific theme."""
    if theme_name == "Light":
        return LIGHT_COLORS.copy()
    else:  # Dark or System (default to dark)
        return DARK_COLORS.copy()

def set_current_theme(theme_name: str):
    """Set the current theme colors globally."""
    global COLORS
    COLORS.clear()
    COLORS.update(get_theme_colors(theme_name))

def generate_main_style(colors: dict) -> str:
    """Generate the main application stylesheet with given colors."""
    return f"""
QMainWindow {{
    background-color: {colors['bg_primary']};
}}

QWidget {{
    background-color: transparent;
    color: {colors['text_primary']};
    font-family: 'Segoe UI', 'SF Pro Display', system-ui, sans-serif;
    font-size: 13px;
}}

QLabel {{
    color: {colors['text_primary']};
    background: transparent;
    padding: 2px 0px;
}}

QLabel#title {{
    font-size: 24px;
    font-weight: bold;
    color: {colors['accent_primary']};
}}

QLabel#subtitle {{
    font-size: 14px;
    color: {colors['text_secondary']};
}}

/* Buttons */
QPushButton {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 {colors['accent_gradient_start']},
        stop:1 {colors['accent_gradient_end']});
    color: white;
    border: none;
    border-radius: 8px;
    padding: 10px 20px;
    font-weight: 600;
    font-size: 13px;
    min-width: 100px;
}}

QPushButton:hover {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 {colors['accent_gradient_end']},
        stop:1 {colors['accent_gradient_start']});
}}

QPushButton:pressed {{
    background: {colors['accent_primary']};
}}

QPushButton:disabled {{
    background: {colors['bg_tertiary']};
    color: {colors['text_disabled']};
}}

QPushButton#secondary {{
    background: {colors['bg_tertiary']};
    border: 1px solid {colors['border']};
}}

QPushButton#secondary:hover {{
    background: {colors['bg_hover']};
    border-color: {colors['border_hover']};
}}

QPushButton#danger {{
    background: {colors['error']};
}}

QPushButton#danger:hover {{
    background: #dc2626;
}}

/* Input Fields */
QLineEdit, QTextEdit, QPlainTextEdit {{
    background-color: {colors['bg_tertiary']};
    border: 1px solid {colors['border']};
    border-radius: 8px;
    padding: 10px 12px;
    color: {colors['text_primary']};
    selection-background-color: {colors['accent_primary']};
}}

QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {{
    border-color: {colors['accent_primary']};
}}

/* ComboBox */
QComboBox {{
    background-color: {colors['bg_tertiary']};
    border: 1px solid {colors['border']};
    border-radius: 8px;
    padding: 8px 12px;
    color: {colors['text_primary']};
    min-width: 120px;
}}

QComboBox:hover {{
    border-color: {colors['border_hover']};
}}

QComboBox:focus {{
    border-color: {colors['accent_primary']};
}}

QComboBox::drop-down {{
    border: none;
    padding-right: 10px;
}}

QComboBox::down-arrow {{
    image: none;
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-top: 6px solid {colors['text_secondary']};
    margin-right: 10px;
}}

QComboBox QAbstractItemView {{
    background-color: {colors['bg_card']};
    border: 1px solid {colors['border']};
    border-radius: 8px;
    selection-background-color: {colors['accent_primary']};
    outline: none;
}}

/* SpinBox */
QSpinBox, QDoubleSpinBox {{
    background-color: {colors['bg_tertiary']};
    border: 1px solid {colors['border']};
    border-radius: 4px;
    padding: 3px 6px;
    color: {colors['text_primary']};
    min-width: 45px;
}}

QSpinBox:hover, QDoubleSpinBox:hover {{
    border-color: {colors['border_hover']};
}}

QSpinBox:focus, QDoubleSpinBox:focus {{
    border-color: {colors['accent_primary']};
}}

QSpinBox::up-button, QDoubleSpinBox::up-button {{
    subcontrol-origin: border;
    subcontrol-position: top right;
    width: 16px;
    border-left: 1px solid {colors['border']};
    border-top-right-radius: 3px;
    background-color: #1a1a1a;
}}

QSpinBox::down-button, QDoubleSpinBox::down-button {{
    subcontrol-origin: border;
    subcontrol-position: bottom right;
    width: 16px;
    border-left: 1px solid {colors['border']};
    border-bottom-right-radius: 3px;
    background-color: #1a1a1a;
}}

QSpinBox::up-button:hover, QDoubleSpinBox::up-button:hover,
QSpinBox::down-button:hover, QDoubleSpinBox::down-button:hover {{
    background-color: #333333;
}}

/* ScrollBar */
QScrollBar:vertical {{
    background: {colors['scrollbar_bg']};
    width: 12px;
    border-radius: 6px;
    margin: 0;
}}

QScrollBar::handle:vertical {{
    background: {colors['scrollbar_handle']};
    border-radius: 6px;
    min-height: 30px;
}}

QScrollBar::handle:vertical:hover {{
    background: {colors['scrollbar_handle_hover']};
}}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0;
}}

QScrollBar:horizontal {{
    background: {colors['scrollbar_bg']};
    height: 12px;
    border-radius: 6px;
    margin: 0;
}}

QScrollBar::handle:horizontal {{
    background: {colors['scrollbar_handle']};
    border-radius: 6px;
    min-width: 30px;
}}

QScrollBar::handle:horizontal:hover {{
    background: {colors['scrollbar_handle_hover']};
}}

QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
    width: 0;
}}

/* Check Box */
QCheckBox {{
    spacing: 10px;
    color: {colors['text_primary']};
}}

QCheckBox::indicator {{
    width: 20px;
    height: 20px;
    border: 2px solid {colors['border']};
    border-radius: 4px;
    background: {colors['bg_tertiary']};
}}

QCheckBox::indicator:hover {{
    border-color: {colors['accent_primary']};
}}

QCheckBox::indicator:checked {{
    background: {colors['accent_primary']};
    border-color: {colors['accent_primary']};
}}

/* Tree Widget */
QTreeWidget {{
    background-color: {colors['bg_tertiary']};
    border: 1px solid {colors['border']};
    border-radius: 8px;
    outline: none;
}}

QTreeWidget::item {{
    padding: 6px;
    border-radius: 4px;
}}

QTreeWidget::item:hover {{
    background-color: {colors['bg_hover']};
}}

QTreeWidget::item:selected {{
    background-color: {colors['accent_primary']};
}}

/* List Widget */
QListWidget {{
    background-color: {colors['bg_tertiary']};
    border: 1px solid {colors['border']};
    border-radius: 8px;
    outline: none;
}}

QListWidget::item {{
    padding: 8px;
    border-radius: 4px;
}}

QListWidget::item:hover {{
    background-color: {colors['bg_hover']};
}}

QListWidget::item:selected {{
    background-color: {colors['accent_primary']};
}}

/* Message Box */
QMessageBox {{
    background-color: {colors['bg_card']};
}}

QMessageBox QLabel {{
    color: {colors['text_primary']};
}}
"""

# Main Application Style (uses current COLORS)
MAIN_STYLE = f"""
QMainWindow {{
    background-color: {COLORS['bg_primary']};
}}

QWidget {{
    background-color: transparent;
    color: {COLORS['text_primary']};
    font-family: 'Segoe UI', 'SF Pro Display', system-ui, sans-serif;
    font-size: 13px;
}}

QLabel {{
    color: {COLORS['text_primary']};
    background: transparent;
    padding: 2px 0px;
}}

QLabel#title {{
    font-size: 24px;
    font-weight: bold;
    color: {COLORS['accent_primary']};
}}

QLabel#subtitle {{
    font-size: 14px;
    color: {COLORS['text_secondary']};
}}

/* Buttons */
QPushButton {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 {COLORS['accent_gradient_start']},
        stop:1 {COLORS['accent_gradient_end']});
    color: white;
    border: none;
    border-radius: 8px;
    padding: 10px 20px;
    font-weight: 600;
    font-size: 13px;
    min-width: 100px;
}}

QPushButton:hover {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 {COLORS['accent_secondary']},
        stop:1 {COLORS['accent_primary']});
}}

QPushButton:pressed {{
    background: {COLORS['accent_primary']};
}}

QPushButton:disabled {{
    background: {COLORS['bg_tertiary']};
    color: {COLORS['text_disabled']};
}}

QPushButton#secondary {{
    background: {COLORS['bg_tertiary']};
    border: 1px solid {COLORS['border']};
}}

QPushButton#secondary:hover {{
    background: {COLORS['bg_hover']};
    border-color: {COLORS['border_hover']};
}}

QPushButton#danger {{
    background: {COLORS['error']};
}}

QPushButton#danger:hover {{
    background: #dc2626;
}}

/* Input Fields */
QLineEdit, QTextEdit, QPlainTextEdit {{
    background-color: {COLORS['bg_tertiary']};
    border: 1px solid {COLORS['border']};
    border-radius: 8px;
    padding: 10px 12px;
    color: {COLORS['text_primary']};
    selection-background-color: {COLORS['accent_primary']};
}}

QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {{
    border-color: {COLORS['accent_primary']};
    outline: none;
}}

QLineEdit:hover, QTextEdit:hover, QPlainTextEdit:hover {{
    border-color: {COLORS['border_hover']};
}}

/* ComboBox */
QComboBox {{
    background-color: {COLORS['bg_tertiary']};
    border: 1px solid {COLORS['border']};
    border-radius: 8px;
    padding: 8px 12px;
    color: {COLORS['text_primary']};
    min-width: 120px;
}}

QComboBox:hover {{
    border-color: {COLORS['border_hover']};
}}

QComboBox:focus {{
    border-color: {COLORS['accent_primary']};
}}

QComboBox::drop-down {{
    border: none;
    padding-right: 10px;
}}

QComboBox::down-arrow {{
    image: none;
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-top: 6px solid {COLORS['text_secondary']};
    margin-right: 10px;
}}

QComboBox QAbstractItemView {{
    background-color: {COLORS['bg_card']};
    border: 1px solid {COLORS['border']};
    border-radius: 8px;
    selection-background-color: {COLORS['accent_primary']};
    outline: none;
}}

/* SpinBox */
QSpinBox, QDoubleSpinBox {{
    background-color: {COLORS['bg_tertiary']};
    border: 1px solid {COLORS['border']};
    border-radius: 4px;
    padding: 3px 6px;
    color: {COLORS['text_primary']};
    min-width: 45px;
}}

QSpinBox:hover, QDoubleSpinBox:hover {{
    border-color: {COLORS['border_hover']};
}}

QSpinBox:focus, QDoubleSpinBox:focus {{
    border-color: {COLORS['accent_primary']};
}}

QSpinBox::up-button, QDoubleSpinBox::up-button {{
    subcontrol-origin: border;
    subcontrol-position: top right;
    width: 16px;
    border-left: 1px solid {COLORS['border']};
    border-top-right-radius: 3px;
    background-color: #1a1a1a;
}}

QSpinBox::down-button, QDoubleSpinBox::down-button {{
    subcontrol-origin: border;
    subcontrol-position: bottom right;
    width: 16px;
    border-left: 1px solid {COLORS['border']};
    border-bottom-right-radius: 3px;
    background-color: #1a1a1a;
}}

QSpinBox::up-button:hover, QDoubleSpinBox::up-button:hover,
QSpinBox::down-button:hover, QDoubleSpinBox::down-button:hover {{
    background-color: #333333;
}}

/* Tab Widget */
QTabWidget::pane {{
    border: 1px solid {COLORS['border']};
    border-radius: 8px;
    background-color: {COLORS['bg_secondary']};
    margin-top: -1px;
}}

QTabBar::tab {{
    background-color: {COLORS['bg_tertiary']};
    color: {COLORS['text_secondary']};
    border: 1px solid {COLORS['border']};
    border-bottom: none;
    border-top-left-radius: 8px;
    border-top-right-radius: 8px;
    padding: 10px 20px;
    margin-right: 2px;
    font-weight: 500;
}}

QTabBar::tab:selected {{
    background-color: {COLORS['bg_secondary']};
    color: {COLORS['accent_primary']};
    border-bottom: 2px solid {COLORS['accent_primary']};
}}

QTabBar::tab:hover:!selected {{
    background-color: {COLORS['bg_hover']};
    color: {COLORS['text_primary']};
}}

/* Tree Widget */
QTreeWidget, QTreeView {{
    background-color: {COLORS['bg_tertiary']};
    border: 1px solid {COLORS['border']};
    border-radius: 8px;
    outline: none;
    padding: 5px;
}}

QTreeWidget::item, QTreeView::item {{
    padding: 8px 5px;
    border-radius: 4px;
}}

QTreeWidget::item:hover, QTreeView::item:hover {{
    background-color: {COLORS['bg_hover']};
}}

QTreeWidget::item:selected, QTreeView::item:selected {{
    background-color: {COLORS['accent_primary']};
    color: white;
}}

QTreeWidget::branch {{
    background: transparent;
}}

/* List Widget */
QListWidget {{
    background-color: {COLORS['bg_tertiary']};
    border: 1px solid {COLORS['border']};
    border-radius: 8px;
    outline: none;
    padding: 5px;
}}

QListWidget::item {{
    padding: 10px;
    border-radius: 4px;
    margin: 2px 0;
}}

QListWidget::item:hover {{
    background-color: {COLORS['bg_hover']};
}}

QListWidget::item:selected {{
    background-color: {COLORS['accent_primary']};
    color: white;
}}

/* Progress Bar */
QProgressBar {{
    background-color: {COLORS['bg_tertiary']};
    border: none;
    border-radius: 6px;
    height: 12px;
    text-align: center;
    color: {COLORS['text_primary']};
}}

QProgressBar::chunk {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 {COLORS['accent_gradient_start']},
        stop:1 {COLORS['accent_gradient_end']});
    border-radius: 6px;
}}

/* Scroll Bar */
QScrollBar:vertical {{
    background: {COLORS['scrollbar_bg']};
    width: 10px;
    border-radius: 5px;
    margin: 0;
}}

QScrollBar::handle:vertical {{
    background: {COLORS['scrollbar_handle']};
    border-radius: 5px;
    min-height: 30px;
}}

QScrollBar::handle:vertical:hover {{
    background: {COLORS['scrollbar_handle_hover']};
}}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0;
}}

QScrollBar:horizontal {{
    background: {COLORS['scrollbar_bg']};
    height: 10px;
    border-radius: 5px;
}}

QScrollBar::handle:horizontal {{
    background: {COLORS['scrollbar_handle']};
    border-radius: 5px;
    min-width: 30px;
}}

QScrollBar::handle:horizontal:hover {{
    background: {COLORS['scrollbar_handle_hover']};
}}

QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
    width: 0;
}}

/* Group Box */
QGroupBox {{
    background-color: {COLORS['bg_card']};
    border: 1px solid {COLORS['border']};
    border-radius: 12px;
    margin-top: 20px;
    padding: 20px;
    font-weight: 600;
}}

QGroupBox::title {{
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 0 10px;
    left: 15px;
    color: {COLORS['accent_primary']};
}}

/* Check Box */
QCheckBox {{
    spacing: 10px;
    color: {COLORS['text_primary']};
}}

QCheckBox::indicator {{
    width: 20px;
    height: 20px;
    border: 2px solid {COLORS['border']};
    border-radius: 4px;
    background: {COLORS['bg_tertiary']};
}}

QCheckBox::indicator:hover {{
    border-color: {COLORS['accent_primary']};
}}

QCheckBox::indicator:checked {{
    background: {COLORS['accent_primary']};
    border-color: {COLORS['accent_primary']};
}}

/* Radio Button */
QRadioButton {{
    spacing: 10px;
    color: {COLORS['text_primary']};
}}

QRadioButton::indicator {{
    width: 20px;
    height: 20px;
    border: 2px solid {COLORS['border']};
    border-radius: 10px;
    background: {COLORS['bg_tertiary']};
}}

QRadioButton::indicator:hover {{
    border-color: {COLORS['accent_primary']};
}}

QRadioButton::indicator:checked {{
    background: {COLORS['accent_primary']};
    border-color: {COLORS['accent_primary']};
}}

/* Splitter */
QSplitter::handle {{
    background: {COLORS['border']};
}}

QSplitter::handle:hover {{
    background: {COLORS['accent_primary']};
}}

/* Menu */
QMenuBar {{
    background-color: {COLORS['bg_secondary']};
    border-bottom: 1px solid {COLORS['border']};
    padding: 5px;
}}

QMenuBar::item {{
    padding: 8px 15px;
    border-radius: 4px;
}}

QMenuBar::item:selected {{
    background-color: {COLORS['bg_hover']};
}}

QMenu {{
    background-color: {COLORS['bg_card']};
    border: 1px solid {COLORS['border']};
    border-radius: 8px;
    padding: 5px;
}}

QMenu::item {{
    padding: 10px 30px;
    border-radius: 4px;
}}

QMenu::item:selected {{
    background-color: {COLORS['accent_primary']};
}}

QMenu::separator {{
    height: 1px;
    background: {COLORS['border']};
    margin: 5px 10px;
}}

/* Status Bar */
QStatusBar {{
    background-color: {COLORS['bg_secondary']};
    border-top: 1px solid {COLORS['border']};
    padding: 5px;
}}

/* Tool Tip */
QToolTip {{
    background-color: {COLORS['bg_card']};
    color: {COLORS['text_primary']};
    border: 1px solid {COLORS['border']};
    border-radius: 6px;
    padding: 8px;
}}

/* Dialogs */
QDialog {{
    background-color: {COLORS['bg_primary']};
}}

QMessageBox {{
    background-color: {COLORS['bg_primary']};
}}

/* File Dialog */
QFileDialog {{
    background-color: {COLORS['bg_primary']};
}}
"""

# Card Widget Style
CARD_STYLE = f"""
QFrame#card {{
    background-color: {COLORS['bg_card']};
    border: 1px solid {COLORS['border']};
    border-radius: 16px;
    padding: 20px;
}}

QFrame#card:hover {{
    border-color: {COLORS['border_hover']};
}}
"""

# Feature Card Style
FEATURE_CARD_STYLE = f"""
QFrame#featureCard {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 {COLORS['bg_card']},
        stop:1 {COLORS['bg_tertiary']});
    border: 1px solid {COLORS['border']};
    border-radius: 16px;
    padding: 25px;
}}

QFrame#featureCard:hover {{
    border-color: {COLORS['accent_primary']};
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 {COLORS['bg_tertiary']},
        stop:1 {COLORS['bg_hover']});
}}
"""

# Stats Card Style
STATS_CARD_STYLE = f"""
QFrame#statsCard {{
    background-color: {COLORS['bg_tertiary']};
    border: 1px solid {COLORS['border']};
    border-radius: 12px;
    padding: 15px;
}}
"""

# Log Viewer Style
LOG_VIEWER_STYLE = f"""
QPlainTextEdit#logViewer {{
    background-color: {COLORS['bg_primary']};
    color: {COLORS['text_secondary']};
    font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
    font-size: 12px;
    border: 1px solid {COLORS['border']};
    border-radius: 8px;
    padding: 10px;
}}
"""

# Syntax Highlighting Colors
SYNTAX_COLORS = {
    'keyword': '#c678dd',
    'string': '#98c379',
    'number': '#d19a66',
    'comment': '#5c6370',
    'function': '#61afef',
    'class': '#e5c07b',
    'operator': '#56b6c2',
    'variable': '#e06c75',
}
