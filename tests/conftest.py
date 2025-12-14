"""
StructureMaster - Test Configuration
Pytest configuration and fixtures.
"""

import pytest
import tempfile
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))


@pytest.fixture(scope='session')
def project_root():
    """Get project root directory."""
    return Path(__file__).parent.parent


@pytest.fixture
def sample_structure():
    """Create sample structure for testing."""
    return {
        'src': {
            'main.py': None,
            'utils': {
                'helpers.py': None,
                'config.py': None,
            },
            'models': {
                '__init__.py': None,
            }
        },
        'tests': {
            'test_main.py': None,
            'conftest.py': None,
        },
        'docs': {
            'README.md': None,
        },
        'requirements.txt': None,
        'setup.py': None,
        '.gitignore': None,
    }


@pytest.fixture
def sample_tree_text():
    """Create sample tree text for testing."""
    return '''├── src/
│   ├── main.py
│   └── utils/
│       ├── helpers.py
│       └── config.py
├── tests/
│   └── test_main.py
└── README.md'''


@pytest.fixture
def sample_json_structure():
    """Create sample JSON structure string."""
    import json
    return json.dumps({
        'src': {
            'main.py': None,
            'utils.py': None,
        },
        'tests': {},
    }, indent=2)


@pytest.fixture
def sample_plain_paths():
    """Create sample plain paths list."""
    return '''src/main.py
src/utils/helpers.py
src/utils/config.py
tests/test_main.py
README.md'''


@pytest.fixture
def temp_project_dir():
    """Create a temporary directory with sample project structure."""
    with tempfile.TemporaryDirectory() as td:
        base = Path(td)
        
        # Create structure
        (base / 'src').mkdir()
        (base / 'src' / 'main.py').write_text('# Main file\nprint("Hello")')
        (base / 'src' / 'utils').mkdir()
        (base / 'src' / 'utils' / 'helpers.py').write_text('# Helpers\n\ndef helper():\n    pass')
        
        (base / 'tests').mkdir()
        (base / 'tests' / 'test_main.py').write_text('# Tests\n\ndef test_example():\n    assert True')
        
        (base / 'README.md').write_text('# Test Project\n\nDescription here.')
        (base / 'requirements.txt').write_text('pytest>=7.0\nclick>=8.0')
        
        yield base


@pytest.fixture
def mock_git_repo(temp_project_dir):
    """Create a mock git repository."""
    git_dir = temp_project_dir / '.git'
    git_dir.mkdir()
    
    # Create minimal git structure
    (git_dir / 'HEAD').write_text('ref: refs/heads/main')
    (git_dir / 'config').write_text('[core]\n\trepositoryformatversion = 0')
    
    return temp_project_dir


# ==================== MARKERS ====================

def pytest_configure(config):
    """Configure pytest markers."""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "requires_git: marks tests that require git"
    )


# ==================== HOOKS ====================

def pytest_collection_modifyitems(config, items):
    """Modify test collection."""
    # Add slow marker to tests that take longer
    for item in items:
        if 'integration' in item.nodeid:
            item.add_marker(pytest.mark.integration)
        if 'git' in item.nodeid.lower():
            item.add_marker(pytest.mark.requires_git)
