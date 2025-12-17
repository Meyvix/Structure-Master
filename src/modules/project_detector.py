"""
Stracture-Master - Project Detector Module
Automatically detects project types based on file markers and patterns.
"""

from pathlib import Path
from typing import Dict, List, Optional, Tuple
import fnmatch

from ..config import Config, ProjectType


class ProjectDetector:
    """
    Detects project type based on marker files and patterns.
    """
    
    # Project markers with confidence weights
    PROJECT_INDICATORS: Dict[ProjectType, List[Tuple[str, int]]] = {
        ProjectType.LARAVEL: [
            ('artisan', 100),
            ('composer.json', 30),
            ('app/Http/Kernel.php', 80),
            ('bootstrap/app.php', 50),
            ('config/app.php', 40),
            ('routes/web.php', 40),
        ],
        ProjectType.REACT: [
            ('src/App.jsx', 90),
            ('src/App.tsx', 90),
            ('src/App.js', 80),
            ('src/index.jsx', 70),
            ('src/index.tsx', 70),
            ('public/index.html', 30),
        ],
        ProjectType.VUE: [
            ('vue.config.js', 90),
            ('nuxt.config.js', 90),
            ('nuxt.config.ts', 90),
            ('src/App.vue', 80),
            ('src/main.js', 30),
        ],
        ProjectType.ANGULAR: [
            ('angular.json', 100),
            ('src/app/app.module.ts', 80),
            ('src/app/app.component.ts', 70),
        ],
        ProjectType.NODEJS: [
            ('package.json', 20),
            ('server.js', 50),
            ('app.js', 40),
            ('index.js', 30),
            ('src/server.js', 50),
            ('src/index.js', 40),
        ],
        ProjectType.DJANGO: [
            ('manage.py', 90),
            ('wsgi.py', 40),
            ('settings.py', 50),
            ('urls.py', 40),
            ('**/settings.py', 30),
        ],
        ProjectType.FLASK: [
            ('app.py', 50),
            ('wsgi.py', 40),
            ('application.py', 50),
            ('requirements.txt', 10),
        ],
        ProjectType.DOTNET: [
            ('*.csproj', 90),
            ('*.sln', 80),
            ('Program.cs', 70),
            ('Startup.cs', 60),
            ('appsettings.json', 40),
        ],
        ProjectType.SPRING: [
            ('pom.xml', 60),
            ('build.gradle', 60),
            ('src/main/java/**/*.java', 40),
            ('application.properties', 50),
            ('application.yml', 50),
        ],
        ProjectType.PYTHON: [
            ('setup.py', 70),
            ('pyproject.toml', 70),
            ('setup.cfg', 60),
            ('requirements.txt', 30),
            ('Pipfile', 50),
            ('poetry.lock', 50),
        ],
        ProjectType.GO: [
            ('go.mod', 100),
            ('go.sum', 50),
            ('main.go', 60),
            ('cmd/main.go', 50),
        ],
        ProjectType.RUST: [
            ('Cargo.toml', 100),
            ('src/main.rs', 60),
            ('src/lib.rs', 60),
        ],
        ProjectType.JAVA: [
            ('pom.xml', 40),
            ('build.gradle', 40),
            ('*.java', 30),
            ('src/main/java', 50),
        ],
        ProjectType.PHP: [
            ('composer.json', 30),
            ('index.php', 40),
            ('*.php', 20),
        ],
        ProjectType.RUBY: [
            ('Gemfile', 80),
            ('Rakefile', 50),
            ('config.ru', 50),
            ('*.rb', 20),
        ],
    }
    
    def __init__(self):
        """Initialize detector."""
        self._cache: Dict[str, ProjectType] = {}
    
    def detect(self, path: Path) -> ProjectType:
        """
        Detect project type for a directory.
        
        Args:
            path: Project root path
            
        Returns:
            Detected ProjectType
        """
        path = Path(path).resolve()
        
        # Check cache
        cache_key = str(path)
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        if not path.exists() or not path.is_dir():
            return ProjectType.UNKNOWN
        
        # Calculate scores for each project type
        scores: Dict[ProjectType, int] = {}
        
        for project_type, indicators in self.PROJECT_INDICATORS.items():
            score = 0
            for pattern, weight in indicators:
                if self._check_pattern(path, pattern):
                    score += weight
            
            if score > 0:
                scores[project_type] = score
        
        # Return highest scoring type
        if not scores:
            return ProjectType.UNKNOWN
        
        detected = max(scores, key=scores.get)
        
        # Special case: distinguish between similar types
        detected = self._refine_detection(path, detected, scores)
        
        # Cache result
        self._cache[cache_key] = detected
        
        return detected
    
    def _check_pattern(self, root: Path, pattern: str) -> bool:
        """Check if pattern matches any file in project."""
        # Handle glob patterns
        if '*' in pattern:
            if '**' in pattern:
                # Recursive glob
                matches = list(root.glob(pattern))
            else:
                # Single-level glob
                parts = pattern.split('/')
                if len(parts) > 1:
                    matches = list(root.glob(pattern))
                else:
                    matches = list(root.glob(f'**/{pattern}'))
            return len(matches) > 0
        else:
            # Direct path check
            return (root / pattern).exists()
    
    def _refine_detection(self, path: Path, detected: ProjectType, 
                         scores: Dict[ProjectType, int]) -> ProjectType:
        """Refine detection for ambiguous cases."""
        
        # React vs Vue vs Angular (all use package.json)
        if detected == ProjectType.NODEJS and ProjectType.REACT in scores:
            if scores[ProjectType.REACT] >= 80:
                return ProjectType.REACT
        
        if detected == ProjectType.NODEJS and ProjectType.VUE in scores:
            if scores[ProjectType.VUE] >= 80:
                return ProjectType.VUE
        
        if detected == ProjectType.NODEJS and ProjectType.ANGULAR in scores:
            if scores[ProjectType.ANGULAR] >= 80:
                return ProjectType.ANGULAR
        
        # Django vs Flask (both Python)
        if detected == ProjectType.PYTHON:
            if ProjectType.DJANGO in scores and scores[ProjectType.DJANGO] >= 90:
                return ProjectType.DJANGO
            if ProjectType.FLASK in scores and scores[ProjectType.FLASK] >= 50:
                return ProjectType.FLASK
        
        # Java vs Spring
        if detected == ProjectType.JAVA and ProjectType.SPRING in scores:
            if scores[ProjectType.SPRING] >= 80:
                return ProjectType.SPRING
        
        # PHP vs Laravel
        if detected == ProjectType.PHP and ProjectType.LARAVEL in scores:
            if scores[ProjectType.LARAVEL] >= 100:
                return ProjectType.LARAVEL
        
        return detected
    
    def get_project_info(self, path: Path) -> Dict:
        """
        Get detailed project information.
        
        Args:
            path: Project root path
            
        Returns:
            Dictionary with project details
        """
        path = Path(path).resolve()
        project_type = self.detect(path)
        
        info = {
            'type': project_type.name,
            'path': str(path),
            'name': path.name,
            'markers_found': [],
            'config_files': [],
        }
        
        # Find which markers were matched
        if project_type in self.PROJECT_INDICATORS:
            for pattern, _ in self.PROJECT_INDICATORS[project_type]:
                if self._check_pattern(path, pattern):
                    info['markers_found'].append(pattern)
        
        # Find common config files
        common_configs = [
            'package.json', 'composer.json', 'requirements.txt',
            'Pipfile', 'Gemfile', 'pom.xml', 'build.gradle',
            'cargo.toml', 'go.mod', '.env', 'docker-compose.yml',
            'Dockerfile', 'Makefile', 'README.md',
        ]
        
        for config in common_configs:
            if (path / config).exists():
                info['config_files'].append(config)
        
        return info
    
    def get_ignore_patterns(self, project_type: ProjectType) -> List[str]:
        """
        Get ignore patterns for a project type.
        
        Args:
            project_type: Project type
            
        Returns:
            List of ignore patterns
        """
        return Config.get_ignore_patterns(project_type)
    
    def clear_cache(self) -> None:
        """Clear detection cache."""
        self._cache.clear()


# Create singleton instance
detector = ProjectDetector()
