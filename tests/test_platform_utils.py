"""
Tests for platform_utils.py module.
"""
import pytest
import os
import sys
import platform

# Import the module under test
import modules.platform_utils as platform_utils


class TestPlatformConstants:
    """Tests for platform detection constants."""
    
    def test_is_windows_type(self):
        """IS_WINDOWS should be boolean."""
        assert isinstance(platform_utils.IS_WINDOWS, bool)
    
    def test_is_macos_type(self):
        """IS_MACOS should be boolean."""
        assert isinstance(platform_utils.IS_MACOS, bool)
    
    def test_is_linux_type(self):
        """IS_LINUX should be boolean."""
        assert isinstance(platform_utils.IS_LINUX, bool)
    
    def test_exactly_one_platform_true(self):
        """Exactly one platform constant should be True."""
        platforms = [
            platform_utils.IS_WINDOWS,
            platform_utils.IS_MACOS,
            platform_utils.IS_LINUX
        ]
        assert sum(platforms) == 1, "Exactly one platform should be detected"
    
    def test_platform_matches_system(self):
        """Platform constants should match actual system."""
        system = platform.system()
        if system == "Windows":
            assert platform_utils.IS_WINDOWS is True
        elif system == "Darwin":
            assert platform_utils.IS_MACOS is True
        elif system == "Linux":
            assert platform_utils.IS_LINUX is True


class TestGetAppDataDir:
    """Tests for get_app_data_dir function."""
    
    def test_returns_string(self):
        """get_app_data_dir should return a string."""
        result = platform_utils.get_app_data_dir()
        assert isinstance(result, str)
    
    def test_returns_absolute_path(self):
        """get_app_data_dir should return an absolute path."""
        result = platform_utils.get_app_data_dir()
        assert os.path.isabs(result)
    
    def test_custom_app_name(self):
        """get_app_data_dir should use custom app name."""
        result = platform_utils.get_app_data_dir("TestApp")
        assert "TestApp" in result
    
    def test_default_app_name(self):
        """get_app_data_dir should use default app name."""
        result = platform_utils.get_app_data_dir()
        assert "Tsufutube" in result
    
    def test_path_structure_windows(self):
        """On Windows, path should contain AppData or config."""
        if platform_utils.IS_WINDOWS:
            result = platform_utils.get_app_data_dir()
            assert "AppData" in result or "config" in result.lower()
    
    def test_path_structure_macos(self):
        """On macOS, path should contain Application Support."""
        if platform_utils.IS_MACOS:
            result = platform_utils.get_app_data_dir()
            assert "Application Support" in result
    
    def test_path_structure_linux(self):
        """On Linux, path should contain .config."""
        if platform_utils.IS_LINUX:
            result = platform_utils.get_app_data_dir()
            assert ".config" in result


class TestGetTempDir:
    """Tests for get_temp_dir function."""
    
    def test_returns_string(self):
        """get_temp_dir should return a string."""
        result = platform_utils.get_temp_dir()
        assert isinstance(result, str)
    
    def test_returns_absolute_path(self):
        """get_temp_dir should return an absolute path."""
        result = platform_utils.get_temp_dir()
        assert os.path.isabs(result)


class TestGetExecutableDir:
    """Tests for get_executable_dir function."""
    
    def test_returns_string(self):
        """get_executable_dir should return a string."""
        result = platform_utils.get_executable_dir()
        assert isinstance(result, str)
    
    def test_returns_absolute_path(self):
        """get_executable_dir should return an absolute path."""
        result = platform_utils.get_executable_dir()
        assert os.path.isabs(result)
    
    def test_directory_exists(self):
        """get_executable_dir should return an existing directory."""
        result = platform_utils.get_executable_dir()
        assert os.path.isdir(result)


class TestGetFFmpegPath:
    """Tests for get_ffmpeg_path function."""
    
    def test_returns_string_or_none(self):
        """get_ffmpeg_path should return a string or None."""
        result = platform_utils.get_ffmpeg_path()
        assert result is None or isinstance(result, str)
    
    def test_path_contains_ffmpeg(self):
        """If path is returned, it should contain 'ffmpeg'."""
        result = platform_utils.get_ffmpeg_path()
        if result:
            assert "ffmpeg" in result.lower()


class TestGetSubprocessCreationFlags:
    """Tests for get_subprocess_creation_flags function."""
    
    def test_returns_integer(self):
        """get_subprocess_creation_flags should return an integer."""
        result = platform_utils.get_subprocess_creation_flags()
        assert isinstance(result, int)
    
    def test_windows_returns_nonzero(self):
        """On Windows, should return non-zero flag."""
        if platform_utils.IS_WINDOWS:
            result = platform_utils.get_subprocess_creation_flags()
            assert result != 0
    
    def test_non_windows_returns_zero(self):
        """On non-Windows, should return 0."""
        if not platform_utils.IS_WINDOWS:
            result = platform_utils.get_subprocess_creation_flags()
            assert result == 0


class TestGetSubprocessStartupinfo:
    """Tests for get_subprocess_startupinfo function."""
    
    def test_returns_correct_type(self):
        """get_subprocess_startupinfo should return correct type."""
        result = platform_utils.get_subprocess_startupinfo()
        if platform_utils.IS_WINDOWS:
            # On Windows, should return STARTUPINFO or None
            assert result is None or hasattr(result, 'dwFlags')
        else:
            # On non-Windows, should return None
            assert result is None


class TestStartupEntryPath:
    """Tests for get_startup_entry_path function."""
    
    def test_returns_string(self):
        """get_startup_entry_path should return a string."""
        result = platform_utils.get_startup_entry_path()
        assert isinstance(result, str)
    
    def test_macos_plist_path(self):
        """On macOS, should return .plist path."""
        if platform_utils.IS_MACOS:
            result = platform_utils.get_startup_entry_path()
            assert result.endswith(".plist")
    
    def test_linux_desktop_path(self):
        """On Linux, should return .desktop path."""
        if platform_utils.IS_LINUX:
            result = platform_utils.get_startup_entry_path()
            assert result.endswith(".desktop")
