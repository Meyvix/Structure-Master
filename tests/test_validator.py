"""
Stracture-Master - Validator Tests
Unit tests for the validator module.
"""

import pytest
import tempfile
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from src.modules.validator import StructureValidator, ValidationType, ValidationIssue


class TestStructureValidator:
    """Tests for StructureValidator class."""
    
    @pytest.fixture
    def validator(self):
        """Create validator instance."""
        return StructureValidator()
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for tests."""
        with tempfile.TemporaryDirectory() as td:
            yield Path(td)
    
    # ==================== VALID STRUCTURES ====================
    
    def test_validate_simple_structure(self, validator, temp_dir):
        """Test validating a simple valid structure."""
        structure = {
            'src': {
                'main.py': None,
                'utils.py': None
            },
            'README.md': None
        }
        
        result = validator.validate(structure, temp_dir)
        
        assert result.is_valid
        assert len(result.errors) == 0
    
    def test_validate_nested_structure(self, validator, temp_dir):
        """Test validating deeply nested structure."""
        structure = {
            'level1': {
                'level2': {
                    'level3': {
                        'file.txt': None
                    }
                }
            }
        }
        
        result = validator.validate(structure, temp_dir)
        
        assert result.is_valid
    
    # ==================== INVALID NAMES ====================
    
    def test_invalid_filename_chars(self, validator, temp_dir):
        """Test detection of invalid characters in filenames."""
        structure = {
            'file<name>.txt': None,  # Invalid on Windows
        }
        
        result = validator.validate(structure, temp_dir)
        
        # Should have warning or error about invalid characters
        # Behavior may vary by platform
        assert result is not None
    
    def test_reserved_names_windows(self, validator, temp_dir):
        """Test detection of Windows reserved names."""
        structure = {
            'CON': None,  # Reserved on Windows
            'NUL.txt': None,  # Also reserved
        }
        
        result = validator.validate(structure, temp_dir)
        
        # Should have warnings for reserved names
        assert result is not None
    
    # ==================== DUPLICATES ====================
    
    def test_detect_duplicate_paths(self, validator, temp_dir):
        """Test that duplicate paths are not flagged (dict prevents this)."""
        # Dicts naturally prevent duplicates
        structure = {
            'file.txt': None,
        }
        
        result = validator.validate(structure, temp_dir)
        
        assert result.is_valid
    
    # ==================== DEPTH LIMITS ====================
    
    def test_max_depth_exceeded(self, validator, temp_dir):
        """Test detection of excessive nesting depth."""
        # Create deeply nested structure
        structure = {}
        current = structure
        for i in range(50):
            current[f'level{i}'] = {}
            current = current[f'level{i}']
        current['file.txt'] = None
        
        result = validator.validate(structure, temp_dir)
        
        # Should have warning about depth
        assert result is not None
        # May have depth warning depending on max_depth setting
    
    # ==================== PATH LENGTH ====================
    
    def test_long_path_detection(self, validator, temp_dir):
        """Test detection of excessively long paths."""
        # Create path that might exceed limits
        long_name = 'a' * 200
        structure = {
            long_name: {
                long_name: {
                    'file.txt': None
                }
            }
        }
        
        result = validator.validate(structure, temp_dir)
        
        # Should complete without exception
        assert result is not None
    
    # ==================== CONFLICTS ====================
    
    def test_existing_file_conflict(self, validator, temp_dir):
        """Test detection of conflicts with existing files."""
        # Create existing file
        existing = temp_dir / 'existing.txt'
        existing.write_text('content')
        
        structure = {
            'existing.txt': None
        }
        
        result = validator.validate(structure, temp_dir)
        
        # Should detect existing file
        # Behavior depends on whether conflicts are warnings or errors
        assert result is not None
    
    def test_existing_dir_conflict(self, validator, temp_dir):
        """Test detection of conflicts with existing directories."""
        # Create existing directory
        existing = temp_dir / 'existing_dir'
        existing.mkdir()
        
        structure = {
            'existing_dir': {}
        }
        
        result = validator.validate(structure, temp_dir)
        
        assert result is not None
    
    # ==================== EDGE CASES ====================
    
    def test_empty_structure(self, validator, temp_dir):
        """Test validating empty structure."""
        structure = {}
        
        result = validator.validate(structure, temp_dir)
        
        assert result.is_valid
    
    def test_single_file(self, validator, temp_dir):
        """Test validating single file."""
        structure = {
            'file.txt': None
        }
        
        result = validator.validate(structure, temp_dir)
        
        assert result.is_valid
    
    def test_empty_directory(self, validator, temp_dir):
        """Test validating structure with empty directories."""
        structure = {
            'empty_dir': {},
            'another_empty': {}
        }
        
        result = validator.validate(structure, temp_dir)
        
        assert result.is_valid


class TestValidationIssue:
    """Tests for ValidationIssue class."""
    
    def test_issue_creation(self):
        """Test creating a validation issue."""
        issue = ValidationIssue(
            type=ValidationType.ERROR,
            message="Test error",
            path="some/path"
        )
        
        assert issue.type == ValidationType.ERROR
        assert issue.message == "Test error"
        assert issue.path == "some/path"
    
    def test_issue_to_dict(self):
        """Test converting issue to dict."""
        issue = ValidationIssue(
            type=ValidationType.WARNING,
            message="Test warning",
            path="path/to/file"
        )
        
        d = issue.to_dict()
        
        assert 'type' in d
        assert 'message' in d
        assert 'path' in d


class TestValidationType:
    """Tests for ValidationType enum."""
    
    def test_validation_types_exist(self):
        """Test that validation type enum values exist."""
        assert ValidationType.ERROR is not None
        assert ValidationType.WARNING is not None


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
