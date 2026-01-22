"""
Shared pytest fixtures for Tsufutube Downloader tests.
"""
import pytest
import os
import sys
import tempfile

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def sample_youtube_urls():
    """Sample YouTube URLs for testing."""
    return [
        "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "https://youtu.be/dQw4w9WgXcQ",
        "https://www.youtube.com/watch?v=dQw4w9WgXcQ&list=PLtest",
        "https://youtube.com/shorts/dQw4w9WgXcQ",
        "https://www.youtube.com/embed/dQw4w9WgXcQ",
    ]


@pytest.fixture
def sample_bilibili_urls():
    """Sample Bilibili URLs for testing."""
    return [
        "https://www.bilibili.com/video/BV1xx411c7mu",
        "https://bilibili.com/video/BV1xx411c7mu",
        "https://b23.tv/BV1xx411c7mu",
    ]


@pytest.fixture
def sample_douyin_urls():
    """Sample Douyin/TikTok URLs for testing."""
    return [
        "https://www.douyin.com/video/1234567890",
        "https://v.douyin.com/abc123",
        "https://www.tiktok.com/@user/video/1234567890",
    ]


@pytest.fixture
def sample_dailymotion_urls():
    """Sample Dailymotion URLs for testing."""
    return [
        "https://www.dailymotion.com/video/x8test",
        "https://dai.ly/x8test",
    ]


@pytest.fixture
def mock_video_info():
    """Mock video info dictionary."""
    return {
        "id": "dQw4w9WgXcQ",
        "title": "Test Video Title",
        "duration": 212,
        "uploader": "Test Uploader",
        "thumbnail": "https://example.com/thumb.jpg",
        "formats": [
            {"format_id": "22", "ext": "mp4", "height": 720},
            {"format_id": "18", "ext": "mp4", "height": 360},
        ]
    }
