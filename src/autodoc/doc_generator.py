"""
Stracture-Master - Documentation Generator Module
Automatically generate project documentation.
"""

import os
import re
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class DocSection:
    """A documentation section."""
    title: str
    content: str
    level: int = 2
    
    def to_markdown(self) -> str:
        return f"{'#' * self.level} {self.title}\n\n{self.content}\n"


@dataclass
class ProjectDoc:
    """Complete project documentation."""
    name: str
    description: str = ""
    version: str = "1.0.0"
    sections: List[DocSection] = field(default_factory=list)
    
    def to_markdown(self) -> str:
        lines = [f"# {self.name}\n"]
        
        if self.description:
            lines.append(f"\n{self.description}\n")
        
        if self.version:
            lines.append(f"\n**Version:** {self.version}\n")
        
        for section in self.sections:
            lines.append(f"\n{section.to_markdown()}")
        
        return '\n'.join(lines)


class DocGenerator:
    """
    Automatic documentation generator.
    Generates README, CHANGELOG, API docs, and more.
    """
    
    # Language comment patterns
    COMMENT_PATTERNS = {
        'python': (r'"""[\s\S]*?"""', r"'''[\s\S]*?'''", r'#.*'),
        'javascript': (r'/\*[\s\S]*?\*/', r'//.*'),
        'typescript': (r'/\*[\s\S]*?\*/', r'//.*'),
        'java': (r'/\*[\s\S]*?\*/', r'//.*'),
        'go': (r'/\*[\s\S]*?\*/', r'//.*'),
        'rust': (r'/\*[\s\S]*?\*/', r'//.*', r'///.*'),
        'php': (r'/\*[\s\S]*?\*/', r'//.*', r'#.*'),
        'ruby': (r'=begin[\s\S]*?=end', r'#.*'),
    }
    
    def __init__(self):
        """Initialize documentation generator."""
        pass
    
    def generate_readme(self, 
                        project_path: Path,
                        project_name: Optional[str] = None,
                        template: str = 'default') -> str:
        """
        Generate README.md for a project.
        
        Args:
            project_path: Path to project
            project_name: Project name (default: directory name)
            template: Template to use
            
        Returns:
            README content
        """
        name = project_name or project_path.name
        
        # Detect project type and gather info
        info = self._analyze_project(project_path)
        
        doc = ProjectDoc(
            name=name,
            description=info.get('description', 'A project'),
            version=info.get('version', '1.0.0')
        )
        
        # Features section
        doc.sections.append(DocSection(
            title="Features",
            content=self._generate_features_section(info),
            level=2
        ))
        
        # Installation section
        doc.sections.append(DocSection(
            title="Installation",
            content=self._generate_install_section(info),
            level=2
        ))
        
        # Usage section
        doc.sections.append(DocSection(
            title="Usage",
            content=self._generate_usage_section(info),
            level=2
        ))
        
        # Structure section
        doc.sections.append(DocSection(
            title="Project Structure",
            content=self._generate_structure_section(project_path),
            level=2
        ))
        
        # License section
        doc.sections.append(DocSection(
            title="License",
            content=info.get('license', 'MIT License'),
            level=2
        ))
        
        return doc.to_markdown()
    
    def generate_changelog(self,
                           project_path: Path,
                           git_log: bool = True) -> str:
        """
        Generate CHANGELOG.md from git history.
        
        Args:
            project_path: Path to project
            git_log: Use git log for history
            
        Returns:
            CHANGELOG content
        """
        lines = [
            "# Changelog\n",
            "All notable changes to this project will be documented in this file.\n",
            "\nThe format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).\n",
        ]
        
        if git_log:
            # Try to get git history
            try:
                from src.cloud.git_integration import GitIntegration
                git = GitIntegration(project_path)
                commits = git.get_commit_history(limit=100)
                
                # Group by version/date
                current_version = "[Unreleased]"
                lines.append(f"\n## {current_version}\n")
                
                current_date = None
                for commit in commits:
                    commit_date = commit.date.strftime('%Y-%m-%d')
                    if commit_date != current_date:
                        current_date = commit_date
                        lines.append(f"\n### {current_date}\n")
                    
                    # Categorize message
                    msg = commit.message
                    category = self._categorize_commit(msg)
                    lines.append(f"- **{category}**: {msg}\n")
            except:
                lines.append("\n## [1.0.0] - Initial Release\n")
                lines.append("\n### Added\n")
                lines.append("- Initial project setup\n")
        else:
            lines.append("\n## [1.0.0] - " + datetime.now().strftime('%Y-%m-%d') + "\n")
            lines.append("\n### Added\n")
            lines.append("- Initial project setup\n")
        
        return ''.join(lines)
    
    def generate_api_docs(self,
                          project_path: Path,
                          language: str = 'python') -> str:
        """
        Generate API documentation from source code.
        
        Args:
            project_path: Path to project
            language: Programming language
            
        Returns:
            API documentation
        """
        lines = [
            "# API Documentation\n",
            f"\nGenerated: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n",
        ]
        
        # Find source files
        extensions = {
            'python': ['.py'],
            'javascript': ['.js', '.jsx'],
            'typescript': ['.ts', '.tsx'],
            'java': ['.java'],
            'go': ['.go'],
            'rust': ['.rs'],
            'php': ['.php'],
            'ruby': ['.rb'],
        }
        
        exts = extensions.get(language, ['.py'])
        
        for ext in exts:
            for file_path in project_path.rglob(f'*{ext}'):
                if self._should_skip_file(file_path):
                    continue
                
                docs = self._extract_docs_from_file(file_path, language)
                if docs:
                    rel_path = file_path.relative_to(project_path)
                    lines.append(f"\n## {rel_path}\n")
                    
                    for item in docs:
                        lines.append(f"\n### `{item['name']}`\n")
                        if item.get('signature'):
                            lines.append(f"\n```{language}\n{item['signature']}\n```\n")
                        if item.get('docstring'):
                            lines.append(f"\n{item['docstring']}\n")
        
        return ''.join(lines)
    
    def generate_structure_doc(self, project_path: Path) -> str:
        """
        Generate structure documentation.
        
        Args:
            project_path: Path to project
            
        Returns:
            Structure documentation
        """
        lines = [
            "# Project Structure\n",
            f"\n**Root:** `{project_path.name}/`\n",
            "\n```\n",
        ]
        
        tree = self._build_tree(project_path, prefix="")
        lines.append(tree)
        lines.append("```\n")
        
        # Add descriptions for key directories
        lines.append("\n## Directory Descriptions\n")
        
        key_dirs = {
            'src': 'Source code files',
            'lib': 'Library files',
            'tests': 'Test files',
            'test': 'Test files',
            'docs': 'Documentation',
            'config': 'Configuration files',
            'scripts': 'Utility scripts',
            'public': 'Public assets',
            'assets': 'Asset files',
            'static': 'Static files',
        }
        
        for item in project_path.iterdir():
            if item.is_dir() and not item.name.startswith('.'):
                desc = key_dirs.get(item.name.lower(), 'Project directory')
                lines.append(f"\n### `{item.name}/`\n{desc}\n")
        
        return ''.join(lines)
    
    def _analyze_project(self, project_path: Path) -> Dict[str, Any]:
        """Analyze project to gather information."""
        info = {
            'description': '',
            'version': '1.0.0',
            'license': 'MIT',
            'project_type': 'unknown',
            'dependencies': [],
            'scripts': [],
        }
        
        # Check package.json
        package_json = project_path / 'package.json'
        if package_json.exists():
            try:
                import json
                with open(package_json, 'r', encoding='utf-8') as f:
                    pkg = json.load(f)
                info['description'] = pkg.get('description', '')
                info['version'] = pkg.get('version', '1.0.0')
                info['license'] = pkg.get('license', 'MIT')
                info['project_type'] = 'node'
                info['dependencies'] = list(pkg.get('dependencies', {}).keys())
                info['scripts'] = list(pkg.get('scripts', {}).keys())
            except:
                pass
        
        # Check setup.py or pyproject.toml
        setup_py = project_path / 'setup.py'
        pyproject = project_path / 'pyproject.toml'
        
        if setup_py.exists():
            info['project_type'] = 'python'
        elif pyproject.exists():
            info['project_type'] = 'python'
            try:
                with open(pyproject, 'r', encoding='utf-8') as f:
                    content = f.read()
                    # Simple extraction
                    if 'version' in content:
                        match = re.search(r'version\s*=\s*"([^"]+)"', content)
                        if match:
                            info['version'] = match.group(1)
            except:
                pass
        
        # Check requirements.txt
        requirements = project_path / 'requirements.txt'
        if requirements.exists():
            try:
                with open(requirements, 'r', encoding='utf-8') as f:
                    info['dependencies'] = [
                        line.strip().split('=')[0].split('>')[0].split('<')[0]
                        for line in f if line.strip() and not line.startswith('#')
                    ]
            except:
                pass
        
        return info
    
    def _generate_features_section(self, info: Dict[str, Any]) -> str:
        """Generate features section."""
        features = [
            "- Core functionality",
            "- Easy to use",
            "- Well documented",
        ]
        return '\n'.join(features)
    
    def _generate_install_section(self, info: Dict[str, Any]) -> str:
        """Generate installation section."""
        project_type = info.get('project_type', 'unknown')
        
        if project_type == 'python':
            return """```bash
# Clone the repository
git clone https://github.com/user/repo.git
cd repo

# Install dependencies
pip install -r requirements.txt

# Install package
pip install -e .
```"""
        elif project_type == 'node':
            return """```bash
# Clone the repository
git clone https://github.com/user/repo.git
cd repo

# Install dependencies
npm install
```"""
        else:
            return """```bash
# Clone the repository
git clone https://github.com/user/repo.git
cd repo

# Follow the setup instructions
```"""
    
    def _generate_usage_section(self, info: Dict[str, Any]) -> str:
        """Generate usage section."""
        return """```bash
# Run the application
# Add your usage instructions here
```"""
    
    def _generate_structure_section(self, project_path: Path) -> str:
        """Generate structure section."""
        lines = ["```"]
        lines.append(self._build_tree(project_path, max_depth=2))
        lines.append("```")
        return '\n'.join(lines)
    
    def _build_tree(self, 
                    path: Path, 
                    prefix: str = "", 
                    max_depth: int = 3,
                    current_depth: int = 0) -> str:
        """Build tree string for directory."""
        if current_depth >= max_depth:
            return ""
        
        lines = []
        
        try:
            items = sorted(path.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower()))
        except PermissionError:
            return ""
        
        # Filter items
        items = [i for i in items if not self._should_skip_file(i)]
        
        for i, item in enumerate(items[:15]):  # Limit to 15 items per level
            is_last = i == len(items) - 1 or i == 14
            current_prefix = "└── " if is_last else "├── "
            
            if item.is_dir():
                lines.append(f"{prefix}{current_prefix}{item.name}/")
                extension = "    " if is_last else "│   "
                subtree = self._build_tree(
                    item, 
                    prefix + extension, 
                    max_depth, 
                    current_depth + 1
                )
                if subtree:
                    lines.append(subtree)
            else:
                lines.append(f"{prefix}{current_prefix}{item.name}")
        
        if len(items) > 15:
            lines.append(f"{prefix}└── ... ({len(items) - 15} more)")
        
        return '\n'.join(lines)
    
    def _should_skip_file(self, path: Path) -> bool:
        """Check if file/directory should be skipped."""
        skip_names = {
            'node_modules', 'vendor', '.git', '.svn', '__pycache__',
            '.idea', '.vscode', 'venv', '.venv', 'build', 'dist',
            '.DS_Store', 'Thumbs.db', '.cache', '.pytest_cache',
        }
        return path.name in skip_names or path.name.startswith('.')
    
    def _categorize_commit(self, message: str) -> str:
        """Categorize commit message."""
        msg_lower = message.lower()
        
        if any(kw in msg_lower for kw in ['add', 'new', 'feature', 'implement']):
            return 'Added'
        elif any(kw in msg_lower for kw in ['fix', 'bug', 'patch', 'resolve']):
            return 'Fixed'
        elif any(kw in msg_lower for kw in ['change', 'update', 'modify', 'refactor']):
            return 'Changed'
        elif any(kw in msg_lower for kw in ['remove', 'delete', 'drop']):
            return 'Removed'
        elif any(kw in msg_lower for kw in ['deprecat']):
            return 'Deprecated'
        elif any(kw in msg_lower for kw in ['secur', 'vulnerab']):
            return 'Security'
        else:
            return 'Changed'
    
    def _extract_docs_from_file(self, 
                                file_path: Path,
                                language: str) -> List[Dict[str, Any]]:
        """Extract documentation from source file."""
        docs = []
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            if language == 'python':
                docs = self._extract_python_docs(content)
            elif language in ['javascript', 'typescript']:
                docs = self._extract_js_docs(content)
            # Add more languages as needed
            
        except Exception:
            pass
        
        return docs
    
    def _extract_python_docs(self, content: str) -> List[Dict[str, Any]]:
        """Extract documentation from Python file."""
        docs = []
        
        # Find classes and functions with docstrings
        patterns = [
            (r'class\s+(\w+)[^:]*:\s*(?:"""([\s\S]*?)"""|\'\'\'([\s\S]*?)\'\'\')?', 'class'),
            (r'def\s+(\w+)\s*\([^)]*\)[^:]*:\s*(?:"""([\s\S]*?)"""|\'\'\'([\s\S]*?)\'\'\')?', 'function'),
        ]
        
        for pattern, item_type in patterns:
            for match in re.finditer(pattern, content):
                name = match.group(1)
                docstring = match.group(2) or match.group(3) or ''
                
                # Get signature
                full_match = match.group(0)
                sig_match = re.match(r'((?:class|def)\s+\w+[^:]*)', full_match)
                signature = sig_match.group(1) if sig_match else name
                
                docs.append({
                    'name': name,
                    'type': item_type,
                    'signature': signature,
                    'docstring': docstring.strip(),
                })
        
        return docs
    
    def _extract_js_docs(self, content: str) -> List[Dict[str, Any]]:
        """Extract documentation from JavaScript/TypeScript file."""
        docs = []
        
        # Find JSDoc comments and following functions/classes
        jsdoc_pattern = r'/\*\*([\s\S]*?)\*/\s*((?:export\s+)?(?:async\s+)?(?:function|class|const|let|var)\s+\w+[^{]*)'
        
        for match in re.finditer(jsdoc_pattern, content):
            jsdoc = match.group(1).strip()
            signature = match.group(2).strip()
            
            # Extract name
            name_match = re.search(r'(?:function|class|const|let|var)\s+(\w+)', signature)
            name = name_match.group(1) if name_match else 'unknown'
            
            docs.append({
                'name': name,
                'type': 'function' if 'function' in signature else 'class',
                'signature': signature[:100],
                'docstring': jsdoc.replace('* ', '').replace('*', '').strip(),
            })
        
        return docs


# Singleton instance
doc_generator = DocGenerator()
