"""
Stracture-Master - Configuration Module
Contains all configuration settings, constants, and default values.
"""

import os
from pathlib import Path
from typing import Dict, List, Set, Any, Optional
from dataclasses import dataclass, field
from enum import Enum, auto
import json


class LogLevel(Enum):
    """Log levels for the application."""
    TRACE = 0
    DEBUG = 1
    INFO = 2
    WARN = 3
    ERROR = 4
    CRITICAL = 5


class ProjectType(Enum):
    """Supported project types for auto-detection."""
    UNKNOWN = auto()
    LARAVEL = auto()
    REACT = auto()
    VUE = auto()
    ANGULAR = auto()
    NODEJS = auto()
    DJANGO = auto()
    FLASK = auto()
    DOTNET = auto()
    SPRING = auto()
    PYTHON = auto()
    GO = auto()
    RUST = auto()
    JAVA = auto()
    PHP = auto()
    RUBY = auto()


class ExportFormat(Enum):
    """Supported export formats."""
    TXT = "txt"
    JSON = "json"
    MARKDOWN = "md"
    YAML = "yaml"
    HTML = "html"
    ZIP = "zip"
    TAR_GZ = "tar.gz"


class Theme(Enum):
    """GUI themes."""
    DARK = "dark"
    LIGHT = "light"
    SOLARIZED_DARK = "solarized_dark"
    SOLARIZED_LIGHT = "solarized_light"
    CUSTOM = "custom"


@dataclass
class AppPaths:
    """Application paths configuration."""
    root: Path = field(default_factory=lambda: Path.cwd())
    logs: Path = field(default_factory=lambda: Path.cwd() / "logs")
    cache: Path = field(default_factory=lambda: Path.cwd() / "cache")
    history: Path = field(default_factory=lambda: Path.cwd() / "history")
    profiles: Path = field(default_factory=lambda: Path.cwd() / "profiles")
    plugins: Path = field(default_factory=lambda: Path.cwd() / "plugins")
    templates: Path = field(default_factory=lambda: Path.cwd() / "templates")
    exports: Path = field(default_factory=lambda: Path.cwd() / "exports")
    temp: Path = field(default_factory=lambda: Path.cwd() / "temp")
    
    def ensure_all(self) -> None:
        """Create all directories if they don't exist."""
        for path in [self.logs, self.cache, self.history, self.profiles, 
                     self.plugins, self.templates, self.exports, self.temp]:
            path.mkdir(parents=True, exist_ok=True)


class Config:
    """Main configuration class for Stracture-Master."""
    
    # Application Info
    APP_NAME = "Stracture-Master"
    APP_VERSION = "1.0.0"
    APP_DESCRIPTION = "A comprehensive tool for project structure analysis, generation, and documentation"
    
    # Default Settings
    DEFAULT_OUTPUT_FORMAT = ExportFormat.JSON
    DEFAULT_LOG_LEVEL = LogLevel.INFO
    DEFAULT_THEME = Theme.DARK
    DEFAULT_ENCODING = "utf-8"
    DEFAULT_HASH_ALGORITHM = "sha256"
    DEFAULT_ENCRYPTION_ALGORITHM = "AES-256-CBC"
    DEFAULT_KEY_DERIVATION = "PBKDF2"
    DEFAULT_KEY_ITERATIONS = 100000
    
    # File Size Limits
    MAX_FILE_SIZE_MB = 100  # Maximum file size to process (MB)
    MAX_CONTENT_PREVIEW_LINES = 1000  # Maximum lines for content preview
    CHUNK_SIZE = 8192  # Bytes for file reading
    
    # Threading Configuration
    MAX_WORKERS = os.cpu_count() or 4
    SCAN_BATCH_SIZE = 100
    
    # Cache Configuration
    CACHE_ENABLED = True
    CACHE_TTL_SECONDS = 3600  # 1 hour
    CACHE_MAX_SIZE_MB = 500
    
    # Binary File Extensions (will not extract content)
    BINARY_EXTENSIONS: Set[str] = {
        # Images
        '.png', '.jpg', '.jpeg', '.gif', '.bmp', '.ico', '.svg', '.webp',
        '.tiff', '.tif', '.psd', '.ai', '.eps', '.raw', '.cr2', '.nef',
        # Audio
        '.mp3', '.wav', '.ogg', '.flac', '.aac', '.wma', '.m4a', '.aiff',
        # Video
        '.mp4', '.avi', '.mov', '.wmv', '.flv', '.mkv', '.webm', '.m4v',
        '.mpeg', '.mpg', '.3gp',
        # Archives
        '.zip', '.rar', '.7z', '.tar', '.gz', '.bz2', '.xz', '.iso',
        # Documents
        '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx',
        '.odt', '.ods', '.odp',
        # Executables
        '.exe', '.dll', '.so', '.dylib', '.bin', '.msi', '.deb', '.rpm',
        '.app', '.dmg',
        # Compiled
        '.pyc', '.pyo', '.class', '.o', '.obj', '.a', '.lib',
        # Fonts
        '.ttf', '.otf', '.woff', '.woff2', '.eot',
        # Database
        '.db', '.sqlite', '.sqlite3', '.mdb', '.accdb',
        # Other
        '.lock', '.map',
    }
    
    # Text File Extensions (will extract content)
    TEXT_EXTENSIONS: Set[str] = {
        # Programming Languages
        '.py', '.js', '.ts', '.jsx', '.tsx', '.java', '.c', '.cpp', '.h',
        '.hpp', '.cs', '.go', '.rs', '.rb', '.php', '.swift', '.kt', '.scala',
        '.pl', '.pm', '.r', '.lua', '.dart', '.elm', '.ex', '.exs', '.erl',
        '.hrl', '.clj', '.cljs', '.fs', '.fsx', '.vb', '.asm', '.s',
        # Web
        '.html', '.htm', '.css', '.scss', '.sass', '.less', '.vue', '.svelte',
        # Data/Config
        '.json', '.xml', '.yaml', '.yml', '.toml', '.ini', '.cfg', '.conf',
        '.env', '.properties', '.plist',
        # Documentation
        '.md', '.markdown', '.rst', '.txt', '.rtf', '.tex', '.adoc',
        # Shell/Scripts
        '.sh', '.bash', '.zsh', '.fish', '.ps1', '.psm1', '.bat', '.cmd',
        # Build/Config
        '.dockerfile', '.containerfile', '.makefile', '.cmake', '.gradle',
        '.sbt', '.maven', '.npm', '.yarn',
        # Templates
        '.ejs', '.hbs', '.handlebars', '.mustache', '.pug', '.jade', '.jinja',
        '.jinja2', '.twig', '.blade.php', '.erb',
        # SQL
        '.sql', '.mysql', '.pgsql', '.sqlite',
        # GraphQL
        '.graphql', '.gql',
        # Misc
        '.csv', '.tsv', '.log', '.gitignore', '.gitattributes', '.editorconfig',
        '.prettierrc', '.eslintrc', '.babelrc',
    }
    
    # Default Ignore Patterns (global)
    DEFAULT_IGNORE_PATTERNS: List[str] = [
        # Version Control
        '.git/', '.svn/', '.hg/', '.bzr/',
        # Dependencies
        'node_modules/', 'vendor/', 'bower_components/', 'packages/',
        'venv/', '.venv/', 'env/', '.env/', '__pycache__/',
        # Build Output
        'dist/', 'build/', 'out/', 'target/', 'bin/', 'obj/',
        # Cache
        '.cache/', '.sass-cache/', '.parcel-cache/',
        # IDE
        '.idea/', '.vscode/', '*.swp', '*.swo',
        # OS
        '.DS_Store', 'Thumbs.db', 'desktop.ini',
        # Logs
        '*.log',
    ]
    
    # Project-Specific Ignore Patterns
    PROJECT_IGNORE_PATTERNS: Dict[ProjectType, List[str]] = {
        ProjectType.LARAVEL: [
            'storage/framework/', 'storage/logs/', 'bootstrap/cache/',
            'vendor/', 'node_modules/', 'public/storage', 'public/hot',
        ],
        ProjectType.REACT: [
            'node_modules/', 'build/', 'coverage/', '.next/', 'out/',
        ],
        ProjectType.VUE: [
            'node_modules/', 'dist/', 'coverage/', '.nuxt/',
        ],
        ProjectType.ANGULAR: [
            'node_modules/', 'dist/', 'coverage/', '.angular/',
        ],
        ProjectType.NODEJS: [
            'node_modules/', 'dist/', 'coverage/', 'build/',
        ],
        ProjectType.DJANGO: [
            '__pycache__/', 'venv/', '.venv/', '*.pyc', 'staticfiles/',
            'mediafiles/', '*.sqlite3', 'db.sqlite3',
        ],
        ProjectType.FLASK: [
            '__pycache__/', 'venv/', '.venv/', '*.pyc', 'instance/',
        ],
        ProjectType.DOTNET: [
            'bin/', 'obj/', 'packages/', '*.user', '*.suo', '.vs/',
        ],
        ProjectType.SPRING: [
            'target/', 'build/', '.gradle/', '*.class', '*.jar', '*.war',
        ],
        ProjectType.PYTHON: [
            '__pycache__/', 'venv/', '.venv/', '*.pyc', '*.pyo',
            'dist/', 'build/', '*.egg-info/',
        ],
        ProjectType.GO: [
            'vendor/', 'bin/',
        ],
        ProjectType.RUST: [
            'target/', 'Cargo.lock',
        ],
    }
    
    # Project Detection Markers
    PROJECT_MARKERS: Dict[ProjectType, List[str]] = {
        ProjectType.LARAVEL: ['artisan', 'composer.json', 'app/Http/Kernel.php'],
        ProjectType.REACT: ['package.json', 'src/App.js', 'src/App.jsx', 'src/App.tsx'],
        ProjectType.VUE: ['package.json', 'vue.config.js', 'nuxt.config.js', 'src/App.vue'],
        ProjectType.ANGULAR: ['angular.json', 'package.json'],
        ProjectType.NODEJS: ['package.json', 'index.js', 'server.js', 'app.js'],
        ProjectType.DJANGO: ['manage.py', 'settings.py', 'wsgi.py'],
        ProjectType.FLASK: ['app.py', 'wsgi.py', 'requirements.txt'],
        ProjectType.DOTNET: ['*.csproj', '*.sln', 'Program.cs'],
        ProjectType.SPRING: ['pom.xml', 'build.gradle', 'src/main/java'],
        ProjectType.PYTHON: ['setup.py', 'pyproject.toml', 'requirements.txt'],
        ProjectType.GO: ['go.mod', 'go.sum', 'main.go'],
        ProjectType.RUST: ['Cargo.toml', 'src/main.rs', 'src/lib.rs'],
    }
    
    # MIME Type Mappings
    MIME_TYPES: Dict[str, str] = {
        '.py': 'text/x-python',
        '.js': 'application/javascript',
        '.ts': 'application/typescript',
        '.jsx': 'text/jsx',
        '.tsx': 'text/tsx',
        '.java': 'text/x-java-source',
        '.c': 'text/x-c',
        '.cpp': 'text/x-c++',
        '.h': 'text/x-c',
        '.hpp': 'text/x-c++',
        '.cs': 'text/x-csharp',
        '.go': 'text/x-go',
        '.rs': 'text/x-rust',
        '.rb': 'text/x-ruby',
        '.php': 'text/x-php',
        '.html': 'text/html',
        '.htm': 'text/html',
        '.css': 'text/css',
        '.scss': 'text/x-scss',
        '.sass': 'text/x-sass',
        '.less': 'text/x-less',
        '.json': 'application/json',
        '.xml': 'application/xml',
        '.yaml': 'application/x-yaml',
        '.yml': 'application/x-yaml',
        '.md': 'text/markdown',
        '.txt': 'text/plain',
        '.sh': 'application/x-sh',
        '.bash': 'application/x-sh',
        '.sql': 'application/sql',
        '.graphql': 'application/graphql',
        '.vue': 'text/x-vue',
        '.svelte': 'text/x-svelte',
    }
    
    # Sensitive File Patterns (for security warnings)
    SENSITIVE_PATTERNS: List[str] = [
        '*.pem', '*.key', '*.crt', '*.cer', '*.p12', '*.pfx',
        '.env', '.env.*', 'credentials.json', 'secrets.yaml',
        'id_rsa', 'id_dsa', 'id_ecdsa', 'id_ed25519',
        '.aws/credentials', '.ssh/config',
        'wp-config.php', 'config/database.php',
        '.htpasswd', 'shadow', 'passwd',
    ]
    
    # Sensitive Content Patterns (regex)
    SENSITIVE_CONTENT_PATTERNS: List[str] = [
        r'(?i)(api[_-]?key|apikey)\s*[:=]\s*["\']?[\w-]+',
        r'(?i)(secret|password|passwd|pwd)\s*[:=]\s*["\']?[\w-]+',
        r'(?i)(token|access[_-]?token|auth[_-]?token)\s*[:=]\s*["\']?[\w-]+',
        r'(?i)(aws[_-]?access[_-]?key[_-]?id)\s*[:=]\s*["\']?[\w-]+',
        r'(?i)(aws[_-]?secret[_-]?access[_-]?key)\s*[:=]\s*["\']?[\w-]+',
        r'(?i)(private[_-]?key)\s*[:=]\s*["\']?[\w-]+',
        r'(?i)(database[_-]?url|db[_-]?url)\s*[:=]\s*["\']?[\w:/.-]+',
        r'(?i)(mongodb|mysql|postgres|redis)://[\w:@.-]+',
    ]
    
    # GUI Configuration
    GUI_SETTINGS = {
        'window_width': 1400,
        'window_height': 900,
        'min_width': 1000,
        'min_height': 700,
        'font_family': 'Segoe UI',
        'font_size': 10,
        'icon_size': 24,
        'tree_indent': 20,
    }
    
    # Output Template
    OUTPUT_TEMPLATE = """
================================================================================
FILE: {filename}
PATH: {filepath}
TYPE: {filetype}
SIZE: {filesize} bytes
MIME: {mime_type}
SHA256: {sha256_hash}
PERMISSIONS: {permissions}
CREATED: {created_date}
MODIFIED: {modified_date}
================================================================================

{content}

"""
    
    # Application instance paths
    _paths: Optional[AppPaths] = None
    
    @classmethod
    def get_paths(cls) -> AppPaths:
        """Get application paths, creating default if not set."""
        if cls._paths is None:
            cls._paths = AppPaths()
        return cls._paths
    
    @classmethod
    def set_root_path(cls, root: Path) -> None:
        """Set the root path and update all derived paths."""
        cls._paths = AppPaths(
            root=root,
            logs=root / "logs",
            cache=root / "cache",
            history=root / "history",
            profiles=root / "profiles",
            plugins=root / "plugins",
            templates=root / "templates",
            exports=root / "exports",
            temp=root / "temp",
        )
        cls._paths.ensure_all()
    
    @classmethod
    def is_binary_file(cls, filepath: str) -> bool:
        """Check if a file is binary based on extension."""
        ext = Path(filepath).suffix.lower()
        return ext in cls.BINARY_EXTENSIONS
    
    @classmethod
    def is_text_file(cls, filepath: str) -> bool:
        """Check if a file is text-based on extension."""
        ext = Path(filepath).suffix.lower()
        return ext in cls.TEXT_EXTENSIONS
    
    @classmethod
    def get_mime_type(cls, filepath: str) -> str:
        """Get MIME type for a file based on extension."""
        ext = Path(filepath).suffix.lower()
        return cls.MIME_TYPES.get(ext, 'application/octet-stream')
    
    @classmethod
    def get_ignore_patterns(cls, project_type: ProjectType) -> List[str]:
        """Get ignore patterns for a specific project type."""
        patterns = cls.DEFAULT_IGNORE_PATTERNS.copy()
        if project_type in cls.PROJECT_IGNORE_PATTERNS:
            patterns.extend(cls.PROJECT_IGNORE_PATTERNS[project_type])
        return patterns
    
    @classmethod
    def load_config_file(cls, filepath: Path) -> Dict[str, Any]:
        """Load configuration from a JSON file."""
        if filepath.exists():
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    
    @classmethod
    def save_config_file(cls, filepath: Path, config: Dict[str, Any]) -> None:
        """Save configuration to a JSON file."""
        filepath.parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)


# Default configuration instance
DEFAULT_CONFIG = Config()
