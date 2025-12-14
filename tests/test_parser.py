"""
StructureMaster - Parser Tests
Unit tests for the parser module.
"""

import pytest
import json
import tempfile
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from src.modules.parser import StructureParser, ParseFormat


class TestStructureParser:
    """Tests for StructureParser class."""
    
    @pytest.fixture
    def parser(self):
        """Create parser instance."""
        return StructureParser()
    
    # ==================== JSON PARSING ====================
    
    def test_parse_nested_json(self, parser):
        """Test parsing nested JSON structure."""
        json_input = '''
        {
            "src": {
                "main.py": null,
                "utils": {
                    "helpers.py": null
                }
            }
        }
        '''
        result = parser.parse(json_input)
        
        assert result.success
        assert result.format_detected == ParseFormat.JSON
        assert 'src' in result.structure
        assert 'main.py' in result.structure['src']
        assert 'utils' in result.structure['src']
    
    def test_parse_flat_json_array(self, parser):
        """Test parsing flat JSON array of paths."""
        json_input = '["src/main.py", "src/utils/helpers.py", "tests/test_main.py"]'
        result = parser.parse(json_input)
        
        assert result.success
        assert result.format_detected == ParseFormat.JSON
        assert 'src' in result.structure
        assert 'tests' in result.structure
    
    def test_parse_invalid_json(self, parser):
        """Test parsing invalid JSON."""
        result = parser.parse('{invalid json}')
        
        # Should try other formats
        assert result is not None
    
    # ==================== TREE PARSING ====================
    
    def test_parse_tree_text(self, parser):
        """Test parsing tree-like text structure."""
        tree_input = '''
├── src/
│   ├── main.py
│   └── utils/
│       └── helpers.py
└── tests/
    └── test_main.py
'''
        result = parser.parse(tree_input)
        
        assert result.success
        assert result.format_detected == ParseFormat.TREE
        assert 'src' in result.structure
        assert 'tests' in result.structure
    
    def test_parse_simple_tree(self, parser):
        """Test parsing simple tree with just dashes."""
        tree_input = '''
── src/
   ── main.py
   ── utils/
      ── helpers.py
'''
        result = parser.parse(tree_input)
        
        assert result.success
    
    # ==================== PLAIN PATH PARSING ====================
    
    def test_parse_plain_paths(self, parser):
        """Test parsing plain path list."""
        plain_input = '''
src/main.py
src/utils/helpers.py
tests/test_main.py
config/settings.yaml
'''
        result = parser.parse(plain_input)
        
        assert result.success
        assert 'src' in result.structure
        assert 'tests' in result.structure
        assert 'config' in result.structure
    
    def test_parse_mixed_slashes(self, parser):
        """Test parsing paths with mixed slashes."""
        plain_input = '''
src\\main.py
src/utils/helpers.py
config\\settings.yaml
'''
        result = parser.parse(plain_input)
        
        assert result.success
        assert 'src' in result.structure
    
    # ==================== FILE PARSING ====================
    
    def test_parse_file(self, parser):
        """Test parsing from file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump({'src': {'main.py': None}}, f)
            temp_path = Path(f.name)
        
        try:
            result = parser.parse_file(temp_path)
            assert result.success
            assert 'src' in result.structure
        finally:
            temp_path.unlink()
    
    def test_parse_nonexistent_file(self, parser):
        """Test parsing non-existent file."""
        result = parser.parse_file(Path('/nonexistent/path/file.json'))
        
        assert not result.success
        assert len(result.errors) > 0
    
    # ==================== FORMAT DETECTION ====================
    
    def test_detect_json_format(self, parser):
        """Test format detection for JSON."""
        json_input = '{"key": "value"}'
        result = parser.parse(json_input)
        
        assert result.format_detected == ParseFormat.JSON
    
    def test_detect_tree_format(self, parser):
        """Test format detection for tree text."""
        tree_input = '├── folder/'
        result = parser.parse(tree_input)
        
        assert result.format_detected == ParseFormat.TREE
    
    # ==================== STATS ====================
    
    def test_parse_stats(self, parser):
        """Test that parsing includes statistics."""
        json_input = '''
        {
            "src": {
                "main.py": null,
                "utils.py": null
            },
            "tests": {}
        }
        '''
        result = parser.parse(json_input)
        
        assert result.success
        assert 'files' in result.stats
        assert 'directories' in result.stats
        assert result.stats['files'] == 2
        assert result.stats['directories'] == 2
    
    # ==================== EDGE CASES ====================
    
    def test_parse_empty_input(self, parser):
        """Test parsing empty input."""
        result = parser.parse('')
        
        assert not result.success
    
    def test_parse_whitespace_only(self, parser):
        """Test parsing whitespace only."""
        result = parser.parse('   \n\n   ')
        
        assert not result.success
    
    def test_parse_single_file(self, parser):
        """Test parsing single file path."""
        result = parser.parse('main.py')
        
        assert result.success
        assert 'main.py' in result.structure


class TestParseFormat:
    """Tests for ParseFormat enum."""
    
    def test_format_values(self):
        """Test format enum values exist."""
        assert ParseFormat.JSON is not None
        assert ParseFormat.TREE is not None
        assert ParseFormat.PLAIN is not None
        assert ParseFormat.UNKNOWN is not None


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
