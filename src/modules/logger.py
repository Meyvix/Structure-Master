"""
StructureMaster - Logger Module
Provides multi-level logging functionality with file and console output.
Supports log export to TXT, JSON, and HTML formats.
"""

import os
import sys
import json
import logging
import threading
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict, Any, Union
from enum import Enum
from dataclasses import dataclass, field, asdict
from collections import deque
import html


class LogLevel(Enum):
    """Log levels for the application."""
    TRACE = 5
    DEBUG = 10
    INFO = 20
    WARN = 30
    ERROR = 40
    CRITICAL = 50
    
    @classmethod
    def from_string(cls, level_str: str) -> 'LogLevel':
        """Convert string to LogLevel."""
        level_map = {
            'trace': cls.TRACE,
            'debug': cls.DEBUG,
            'info': cls.INFO,
            'warn': cls.WARN,
            'warning': cls.WARN,
            'error': cls.ERROR,
            'critical': cls.CRITICAL,
        }
        return level_map.get(level_str.lower(), cls.INFO)


@dataclass
class LogEntry:
    """Represents a single log entry."""
    timestamp: datetime
    level: LogLevel
    message: str
    module: str = ''
    function: str = ''
    line: int = 0
    extra: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'timestamp': self.timestamp.isoformat(),
            'level': self.level.name,
            'message': self.message,
            'module': self.module,
            'function': self.function,
            'line': self.line,
            'extra': self.extra,
        }
    
    def to_string(self, include_location: bool = False) -> str:
        """Convert to formatted string."""
        ts = self.timestamp.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
        level = f"[{self.level.name:8}]"
        
        if include_location and self.module:
            location = f" ({self.module}:{self.function}:{self.line})"
        else:
            location = ''
        
        return f"{ts} {level} {self.message}{location}"


class ColorFormatter(logging.Formatter):
    """Colored formatter for console output."""
    
    COLORS = {
        'TRACE': '\033[90m',      # Gray
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Green
        'WARN': '\033[33m',       # Yellow
        'WARNING': '\033[33m',    # Yellow
        'ERROR': '\033[31m',      # Red
        'CRITICAL': '\033[35m',   # Magenta
        'RESET': '\033[0m',       # Reset
    }
    
    def __init__(self, use_colors: bool = True):
        super().__init__()
        self.use_colors = use_colors and sys.platform != 'win32'
        # Try to enable colors on Windows
        if sys.platform == 'win32':
            try:
                import colorama
                colorama.init()
                self.use_colors = use_colors
            except ImportError:
                pass
    
    def format(self, record: logging.LogRecord) -> str:
        timestamp = datetime.fromtimestamp(record.created).strftime('%Y-%m-%d %H:%M:%S')
        level_name = record.levelname
        
        if self.use_colors:
            color = self.COLORS.get(level_name, self.COLORS['RESET'])
            reset = self.COLORS['RESET']
            return f"{timestamp} {color}[{level_name:8}]{reset} {record.getMessage()}"
        else:
            return f"{timestamp} [{level_name:8}] {record.getMessage()}"


class Logger:
    """
    Advanced logger with multi-level support, file/console output,
    and export capabilities.
    """
    
    _instance: Optional['Logger'] = None
    _lock = threading.Lock()
    
    def __new__(cls, *args, **kwargs):
        """Singleton pattern."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self, 
                 name: str = 'StructureMaster',
                 log_dir: Optional[Path] = None,
                 level: LogLevel = LogLevel.INFO,
                 console_output: bool = True,
                 file_output: bool = True,
                 max_entries: int = 10000):
        """
        Initialize the logger.
        
        Args:
            name: Logger name
            log_dir: Directory for log files
            level: Minimum log level
            console_output: Enable console output
            file_output: Enable file output
            max_entries: Maximum entries to keep in memory
        """
        # Only initialize once
        if hasattr(self, '_initialized'):
            return
        
        self._initialized = True
        self.name = name
        self.log_dir = log_dir or Path.cwd() / 'logs'
        self.level = level
        self.console_output = console_output
        self.file_output = file_output
        self.max_entries = max_entries
        
        # In-memory log storage
        self._entries: deque = deque(maxlen=max_entries)
        self._lock = threading.Lock()
        
        # Setup Python logging
        self._setup_logging()
        
        # Create log directory
        if self.file_output:
            self.log_dir.mkdir(parents=True, exist_ok=True)
    
    def _setup_logging(self) -> None:
        """Setup Python logging handlers."""
        # Add custom TRACE level
        logging.addLevelName(5, 'TRACE')
        
        # Create logger
        self._logger = logging.getLogger(self.name)
        self._logger.setLevel(self.level.value)
        self._logger.handlers = []  # Clear existing handlers
        
        # Console handler
        if self.console_output:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setFormatter(ColorFormatter(use_colors=True))
            console_handler.setLevel(self.level.value)
            self._logger.addHandler(console_handler)
        
        # File handler
        if self.file_output:
            log_file = self.log_dir / f"{self.name}_{datetime.now().strftime('%Y%m%d')}.log"
            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            file_handler.setFormatter(logging.Formatter(
                '%(asctime)s [%(levelname)-8s] %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            ))
            file_handler.setLevel(self.level.value)
            self._logger.addHandler(file_handler)
    
    def _add_entry(self, level: LogLevel, message: str, **kwargs) -> None:
        """Add entry to in-memory storage."""
        entry = LogEntry(
            timestamp=datetime.now(),
            level=level,
            message=message,
            module=kwargs.get('module', ''),
            function=kwargs.get('function', ''),
            line=kwargs.get('line', 0),
            extra=kwargs.get('extra', {}),
        )
        with self._lock:
            self._entries.append(entry)
    
    def set_level(self, level: Union[LogLevel, str]) -> None:
        """Set the minimum log level."""
        if isinstance(level, str):
            level = LogLevel.from_string(level)
        self.level = level
        self._logger.setLevel(level.value)
        for handler in self._logger.handlers:
            handler.setLevel(level.value)
    
    def trace(self, message: str, **kwargs) -> None:
        """Log TRACE level message."""
        if self.level.value <= LogLevel.TRACE.value:
            self._logger.log(5, message)
            self._add_entry(LogLevel.TRACE, message, **kwargs)
    
    def debug(self, message: str, **kwargs) -> None:
        """Log DEBUG level message."""
        if self.level.value <= LogLevel.DEBUG.value:
            self._logger.debug(message)
            self._add_entry(LogLevel.DEBUG, message, **kwargs)
    
    def info(self, message: str, **kwargs) -> None:
        """Log INFO level message."""
        if self.level.value <= LogLevel.INFO.value:
            self._logger.info(message)
            self._add_entry(LogLevel.INFO, message, **kwargs)
    
    def warn(self, message: str, **kwargs) -> None:
        """Log WARN level message."""
        if self.level.value <= LogLevel.WARN.value:
            self._logger.warning(message)
            self._add_entry(LogLevel.WARN, message, **kwargs)
    
    def warning(self, message: str, **kwargs) -> None:
        """Alias for warn()."""
        self.warn(message, **kwargs)
    
    def error(self, message: str, **kwargs) -> None:
        """Log ERROR level message."""
        if self.level.value <= LogLevel.ERROR.value:
            self._logger.error(message)
            self._add_entry(LogLevel.ERROR, message, **kwargs)
    
    def critical(self, message: str, **kwargs) -> None:
        """Log CRITICAL level message."""
        if self.level.value <= LogLevel.CRITICAL.value:
            self._logger.critical(message)
            self._add_entry(LogLevel.CRITICAL, message, **kwargs)
    
    def exception(self, message: str, exc_info: bool = True, **kwargs) -> None:
        """Log exception with traceback."""
        self._logger.exception(message, exc_info=exc_info)
        self._add_entry(LogLevel.ERROR, message, **kwargs)
    
    def get_entries(self, 
                   level: Optional[LogLevel] = None,
                   start_time: Optional[datetime] = None,
                   end_time: Optional[datetime] = None,
                   limit: Optional[int] = None) -> List[LogEntry]:
        """Get log entries with optional filtering."""
        with self._lock:
            entries = list(self._entries)
        
        # Filter by level
        if level is not None:
            entries = [e for e in entries if e.level.value >= level.value]
        
        # Filter by time range
        if start_time is not None:
            entries = [e for e in entries if e.timestamp >= start_time]
        if end_time is not None:
            entries = [e for e in entries if e.timestamp <= end_time]
        
        # Apply limit
        if limit is not None:
            entries = entries[-limit:]
        
        return entries
    
    def clear(self) -> None:
        """Clear in-memory log entries."""
        with self._lock:
            self._entries.clear()
    
    def export_txt(self, filepath: Union[str, Path], 
                  entries: Optional[List[LogEntry]] = None) -> bool:
        """Export logs to TXT file."""
        try:
            entries = entries or self.get_entries()
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(f"StructureMaster Log Export\n")
                f.write(f"Generated: {datetime.now().isoformat()}\n")
                f.write(f"Total Entries: {len(entries)}\n")
                f.write("=" * 80 + "\n\n")
                
                for entry in entries:
                    f.write(entry.to_string(include_location=True) + "\n")
            
            return True
        except (OSError, IOError):
            return False
    
    def export_json(self, filepath: Union[str, Path],
                   entries: Optional[List[LogEntry]] = None) -> bool:
        """Export logs to JSON file."""
        try:
            entries = entries or self.get_entries()
            data = {
                'name': self.name,
                'exported_at': datetime.now().isoformat(),
                'total_entries': len(entries),
                'entries': [e.to_dict() for e in entries],
            }
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            return True
        except (OSError, IOError):
            return False
    
    def export_html(self, filepath: Union[str, Path],
                   entries: Optional[List[LogEntry]] = None) -> bool:
        """Export logs to HTML file."""
        try:
            entries = entries or self.get_entries()
            
            level_colors = {
                LogLevel.TRACE: '#888888',
                LogLevel.DEBUG: '#00bcd4',
                LogLevel.INFO: '#4caf50',
                LogLevel.WARN: '#ff9800',
                LogLevel.ERROR: '#f44336',
                LogLevel.CRITICAL: '#9c27b0',
            }
            
            html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>StructureMaster Log Export</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background-color: #1e1e1e;
            color: #d4d4d4;
            margin: 0;
            padding: 20px;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 20px;
        }}
        .header h1 {{
            margin: 0;
            color: white;
        }}
        .header p {{
            margin: 5px 0 0 0;
            color: rgba(255,255,255,0.8);
        }}
        .log-entry {{
            background: #2d2d2d;
            border-radius: 4px;
            padding: 10px 15px;
            margin-bottom: 8px;
            border-left: 4px solid;
            font-family: 'Consolas', 'Monaco', monospace;
            font-size: 13px;
        }}
        .timestamp {{
            color: #888;
            margin-right: 10px;
        }}
        .level {{
            font-weight: bold;
            padding: 2px 8px;
            border-radius: 3px;
            margin-right: 10px;
        }}
        .message {{
            white-space: pre-wrap;
            word-break: break-word;
        }}
        .filters {{
            margin-bottom: 20px;
            padding: 15px;
            background: #2d2d2d;
            border-radius: 8px;
        }}
        .filters select, .filters input {{
            background: #1e1e1e;
            color: #d4d4d4;
            border: 1px solid #444;
            padding: 8px;
            border-radius: 4px;
            margin-right: 10px;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>📋 StructureMaster Log Export</h1>
        <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        <p>Total Entries: {len(entries)}</p>
    </div>
    
    <div class="filters">
        <label>Filter by Level: </label>
        <select id="levelFilter" onchange="filterLogs()">
            <option value="all">All Levels</option>
            <option value="TRACE">TRACE</option>
            <option value="DEBUG">DEBUG</option>
            <option value="INFO">INFO</option>
            <option value="WARN">WARN</option>
            <option value="ERROR">ERROR</option>
            <option value="CRITICAL">CRITICAL</option>
        </select>
        <input type="text" id="searchFilter" placeholder="Search messages..." oninput="filterLogs()">
    </div>
    
    <div id="logContainer">
"""
            
            for entry in entries:
                color = level_colors.get(entry.level, '#888')
                escaped_msg = html.escape(entry.message)
                html_content += f"""
        <div class="log-entry" data-level="{entry.level.name}" style="border-left-color: {color};">
            <span class="timestamp">{entry.timestamp.strftime('%Y-%m-%d %H:%M:%S')}</span>
            <span class="level" style="background: {color}; color: white;">{entry.level.name}</span>
            <span class="message">{escaped_msg}</span>
        </div>
"""
            
            html_content += """
    </div>
    
    <script>
        function filterLogs() {
            const levelFilter = document.getElementById('levelFilter').value;
            const searchFilter = document.getElementById('searchFilter').value.toLowerCase();
            const entries = document.querySelectorAll('.log-entry');
            
            entries.forEach(entry => {
                const level = entry.getAttribute('data-level');
                const message = entry.querySelector('.message').textContent.toLowerCase();
                
                const levelMatch = levelFilter === 'all' || level === levelFilter;
                const searchMatch = !searchFilter || message.includes(searchFilter);
                
                entry.style.display = (levelMatch && searchMatch) ? 'block' : 'none';
            });
        }
    </script>
</body>
</html>
"""
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            return True
        except (OSError, IOError):
            return False
    
    def get_log_files(self) -> List[Path]:
        """Get list of log files."""
        if not self.log_dir.exists():
            return []
        return sorted(self.log_dir.glob('*.log'), reverse=True)
    
    @classmethod
    def get_instance(cls) -> 'Logger':
        """Get the singleton logger instance."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance


# Global logger instance
logger = Logger.get_instance()
