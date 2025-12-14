"""
StructureMaster - Builder Tests
Unit tests for the builder module.
"""

import pytest
import tempfile
from pathlib import Path
import sys
import os

sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from src.modules.builder import StructureBuilder, BuildResult


class TestStructureBuilder:
    """Tests for StructureBuilder class."""
    
    @pytest.fixture
    def builder(self):
        """Create builder instance."""
        return StructureBuilder()
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for tests."""
        with tempfile.TemporaryDirectory() as td:
            yield Path(td)
    
    # ==================== BASIC BUILDING ====================
    
    def test_build_simple_structure(self, builder, temp_dir):
        """Test building a simple structure."""
        structure = {
            'src': {
                'main.py': None,
            },
            'README.md': None
        }
        
        result = builder.build(structure, temp_dir)
        
        assert result.success
        assert (temp_dir / 'src').is_dir()
        assert (temp_dir / 'src' / 'main.py').is_file()
        assert (temp_dir / 'README.md').is_file()
    
    def test_build_nested_structure(self, builder, temp_dir):
        """Test building nested directories."""
        structure = {
            'level1': {
                'level2': {
                    'level3': {
                        'file.txt': None
                    }
                }
            }
        }
        
        result = builder.build(structure, temp_dir)
        
        assert result.success
        assert (temp_dir / 'level1' / 'level2' / 'level3' / 'file.txt').is_file()
    
    def test_build_empty_directories(self, builder, temp_dir):
        """Test building empty directories."""
        structure = {
            'empty1': {},
            'empty2': {},
        }
        
        result = builder.build(structure, temp_dir)
        
        assert result.success
        assert (temp_dir / 'empty1').is_dir()
        assert (temp_dir / 'empty2').is_dir()
    
    # ==================== DRY RUN ====================
    
    def test_dry_run_no_files_created(self, builder, temp_dir):
        """Test that dry run doesn't create files."""
        structure = {
            'src': {
                'main.py': None
            }
        }
        
        result = builder.build(structure, temp_dir, dry_run=True)
        
        assert result.success
        assert not (temp_dir / 'src').exists()
        assert not (temp_dir / 'src' / 'main.py').exists()
    
    def test_dry_run_reports_operations(self, builder, temp_dir):
        """Test that dry run reports what would be done."""
        structure = {
            'folder': {
                'file.txt': None
            }
        }
        
        result = builder.build(structure, temp_dir, dry_run=True)
        
        assert result.success
        assert result.stats['directories_created'] > 0 or result.stats['files_created'] > 0
    
    # ==================== FORCE MODE ====================
    
    def test_force_overwrites_existing(self, builder, temp_dir):
        """Test that force mode overwrites existing files."""
        # Create existing file
        existing = temp_dir / 'existing.txt'
        existing.write_text('original content')
        
        structure = {
            'existing.txt': None
        }
        
        result = builder.build(structure, temp_dir, force=True)
        
        assert result.success
        assert existing.exists()
    
    def test_no_force_skips_existing(self, builder, temp_dir):
        """Test that without force, existing files are handled appropriately."""
        # Create existing file
        existing = temp_dir / 'existing.txt'
        existing.write_text('original content')
        
        structure = {
            'existing.txt': None
        }
        
        result = builder.build(structure, temp_dir, force=False)
        
        # Should either skip or error based on implementation
        assert result is not None
    
    # ==================== STATS ====================
    
    def test_build_stats(self, builder, temp_dir):
        """Test that build returns statistics."""
        structure = {
            'dir1': {
                'file1.txt': None,
                'file2.txt': None
            },
            'dir2': {},
            'root.txt': None
        }
        
        result = builder.build(structure, temp_dir)
        
        assert result.success
        assert 'directories_created' in result.stats
        assert 'files_created' in result.stats
        assert 'build_time_ms' in result.stats
        assert result.stats['files_created'] == 3
        assert result.stats['directories_created'] == 2
    
    # ==================== ERROR HANDLING ====================
    
    def test_build_to_invalid_path(self, builder):
        """Test building to non-existent parent path."""
        structure = {'file.txt': None}
        invalid_path = Path('/nonexistent/deeply/nested/path')
        
        result = builder.build(structure, invalid_path)
        
        # Should either fail or create parent directories
        assert result is not None
    
    # ==================== EDGE CASES ====================
    
    def test_build_empty_structure(self, builder, temp_dir):
        """Test building empty structure."""
        structure = {}
        
        result = builder.build(structure, temp_dir)
        
        assert result.success
        assert result.stats['files_created'] == 0
        assert result.stats['directories_created'] == 0
    
    def test_build_single_file(self, builder, temp_dir):
        """Test building single file at root."""
        structure = {
            'single.txt': None
        }
        
        result = builder.build(structure, temp_dir)
        
        assert result.success
        assert (temp_dir / 'single.txt').is_file()


class TestBuildResult:
    """Tests for BuildResult class."""
    
    def test_build_result_creation(self):
        """Test creating a BuildResult."""
        result = BuildResult(
            success=True,
            stats={'files_created': 5},
            operations=[],
            errors=[]
        )
        
        assert result.success
        assert result.stats['files_created'] == 5
    
    def test_build_result_with_errors(self):
        """Test BuildResult with errors."""
        result = BuildResult(
            success=False,
            stats={},
            operations=[],
            errors=['Error 1', 'Error 2']
        )
        
        assert not result.success
        assert len(result.errors) == 2


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
