# Stracture-Master

<div align="center">

![Stracture-Master Logo](docs/logo.png)

**A comprehensive, intelligent, and extensible tool for project structure analysis, generation, and documentation.**

[![Python Version](https://img.shields.io/badge/python-3.9%2B-blue)](https://python.org)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Build Status](https://img.shields.io/badge/build-passing-brightgreen)](https://github.com/Stracture-Master/Stracture-Master)

</div>

---

## 🌟 Features

### Core Features
- 📁 **Structure Builder**: Create project structures from JSON, tree-like text, or clipboard
- 🔍 **Structure Extractor**: Extract and document existing project structures
- 📄 **Content Extractor**: Extract all file contents with full metadata

### Advanced Features
- 🔐 **AES-256 Encryption**: Secure your exports with military-grade encryption
- ☁️ **Cloud Sync**: Integrate with Git, GitHub, Dropbox, Google Drive, OneDrive
- 📊 **Analytics**: Code quality metrics, dependency analysis, charts
- 🔎 **Smart Search**: Regex search, content search, advanced filtering
- 🎨 **Beautiful GUI**: Modern dark theme with multiple customization options
- 🌐 **Web Interface**: Access via browser with REST API
- 🔌 **Plugin System**: Extend functionality with custom plugins

---

## 🚀 Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/Stracture-Master/Stracture-Master.git
cd Stracture-Master

# Install dependencies
pip install -r requirements.txt

# Install the package
pip install -e .
```

### CLI Usage

```bash
# Scan a project
Stracture-Master scan ./my-project --output=structure.json

# Build structure from file
Stracture-Master build structure.json --output=./new-project

# Extract content with encryption
Stracture-Master extract ./project --content --encrypt --password=MyPass123

# Compare two projects
Stracture-Master compare ./old ./new --output=diff.md

# Search in project
Stracture-Master search ./project --regex="TODO|FIXME" --output=results.txt
```

### GUI Usage

```bash
# Launch graphical interface
Stracture-Master-gui
# or
python -m src.gui.main_window
```

### Web Interface

```bash
# Start web server
python -m src.web.app
# Access at http://localhost:5000
```

---

## 📖 Documentation

- [Persian User Guide (راهنمای فارسی)](docs/README_FA.md)
- [File Specifications (مشخصات فایل‌ها)](docs/FILE_SPECS_FA.md)
- [Complete Tutorial (آموزش کامل)](docs/TUTORIAL_FA.md)

---

## 🛠️ CLI Commands

| Command | Description |
|---------|-------------|
| `scan` | Scan project and extract structure |
| `build` | Build project from structure file |
| `extract` | Extract content with metadata |
| `preview` | Preview structure from clipboard/file |
| `compare` | Compare two project structures |
| `search` | Search in project files |
| `analyze` | Analyze code quality and metrics |
| `sync` | Sync with cloud services |
| `export` | Export in various formats |
| `log` | View and export logs |

---

## 🎨 GUI Features

- Dark/Light/Custom themes
- Drag & drop support
- Interactive tree view
- Syntax highlighting preview
- Real-time log viewer
- Progress indicators
- Chart visualizations

---

## 📦 Supported Project Types

Automatic detection and optimized handling for:
- Laravel
- React / Vue / Angular
- Node.js
- Django
- Flask
- .NET
- Spring Boot
- Python
- Go
- Rust

---

## 🔒 Security

- AES-256 encryption for exports
- Sensitive data detection (API keys, passwords)
- Auto-sanitization option
- Digital signatures
- Checksum verification

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🤝 Contributing

Contributions are welcome! Please read our [Contributing Guide](CONTRIBUTING.md) for details.

---

<div align="center">
Made with ❤️ by Stracture-Master Team
</div>
