"""
Tests for utils.py module.
"""
import pytest
import os
import sys

# Import the module under test
from utils import resource_path, time_to_seconds


class TestResourcePath:
    """Tests for resource_path function."""
    
    def test_resource_path_returns_string(self):
        """resource_path should return a string."""
        result = resource_path("assets")
        assert isinstance(result, str)
    
    def test_resource_path_joins_correctly(self):
        """resource_path should join paths correctly."""
        result = resource_path("assets/icon.png")
        assert "assets" in result
        assert "icon.png" in result
    
    def test_resource_path_handles_subdirectories(self):
        """resource_path should handle nested paths."""
        result = resource_path("assets/locales/en.json")
        assert result.endswith("en.json") or "en.json" in result


class TestTimeToSeconds:
    """Tests for time_to_seconds function."""
    
    def test_hh_mm_ss_format(self):
        """Test HH:MM:SS format."""
        assert time_to_seconds("01:30:45") == 5445  # 1*3600 + 30*60 + 45
        assert time_to_seconds("00:00:00") == 0
        assert time_to_seconds("02:00:00") == 7200
    
    def test_mm_ss_format(self):
        """Test MM:SS format."""
        assert time_to_seconds("05:30") == 330  # 5*60 + 30
        assert time_to_seconds("00:00") == 0
        assert time_to_seconds("10:00") == 600
        assert time_to_seconds("59:59") == 3599
    
    def test_ss_format(self):
        """Test SS format (seconds only)."""
        assert time_to_seconds("45") == 45
        assert time_to_seconds("0") == 0
        assert time_to_seconds("120") == 120
    
    def test_with_whitespace(self):
        """Test time strings with whitespace."""
        assert time_to_seconds("  01:30  ") == 90
        assert time_to_seconds("\t00:45\n") == 45
    
    def test_invalid_format_returns_negative(self):
        """Test that invalid formats return -1."""
        assert time_to_seconds("invalid") == -1
        assert time_to_seconds("abc:def") == -1
        assert time_to_seconds("") == -1
    
    def test_edge_cases(self):
        """Test edge cases."""
        # Large numbers
        assert time_to_seconds("99:59:59") == 359999
        # Single digit
        assert time_to_seconds("1:2:3") == 3723  # 1*3600 + 2*60 + 3
