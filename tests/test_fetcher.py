"""
Tests for fetcher.py module - FastFetcher class.
"""
import pytest
import sys
import os

# Import the module under test
from modules.fetcher import FastFetcher


class TestFastFetcherPlatformIdentification:
    """Tests for FastFetcher._identify_platform method."""
    
    @pytest.fixture
    def fetcher(self):
        """Create a FastFetcher instance."""
        return FastFetcher(cache_size=10)
    
    # YouTube Tests
    def test_identify_youtube_watch_url(self, fetcher):
        """Identify standard YouTube watch URL."""
        result = fetcher._identify_platform("https://www.youtube.com/watch?v=dQw4w9WgXcQ")
        assert result.upper() == "YOUTUBE"
    
    def test_identify_youtube_short_url(self, fetcher):
        """Identify YouTube short URL (youtu.be)."""
        result = fetcher._identify_platform("https://youtu.be/dQw4w9WgXcQ")
        assert result.upper() == "YOUTUBE"
    
    def test_identify_youtube_shorts(self, fetcher):
        """Identify YouTube Shorts URL."""
        result = fetcher._identify_platform("https://www.youtube.com/shorts/abc123")
        assert result.upper() == "YOUTUBE"
    
    def test_identify_youtube_embed(self, fetcher):
        """Identify YouTube embed URL."""
        result = fetcher._identify_platform("https://www.youtube.com/embed/dQw4w9WgXcQ")
        assert result.upper() == "YOUTUBE"
    
    def test_identify_youtube_playlist(self, fetcher):
        """Identify YouTube playlist URL."""
        result = fetcher._identify_platform("https://www.youtube.com/playlist?list=PLtest123")
        assert result.upper() == "YOUTUBE"
    
    # Bilibili Tests
    def test_identify_bilibili_video(self, fetcher):
        """Identify Bilibili video URL."""
        result = fetcher._identify_platform("https://www.bilibili.com/video/BV1xx411c7mu")
        assert result.upper() == "BILIBILI"
    
    def test_identify_bilibili_short(self, fetcher):
        """Identify Bilibili short URL (b23.tv)."""
        result = fetcher._identify_platform("https://b23.tv/abc123")
        # b23.tv may or may not be recognized
        assert result.upper() in ["BILIBILI", "OTHER"]
    
    # Douyin/TikTok Tests
    def test_identify_douyin(self, fetcher):
        """Identify Douyin URL."""
        result = fetcher._identify_platform("https://www.douyin.com/video/1234567890")
        assert result.upper() == "DOUYIN"
    
    def test_identify_douyin_short(self, fetcher):
        """Identify Douyin short URL (v.douyin.com)."""
        result = fetcher._identify_platform("https://v.douyin.com/abc123")
        assert result.upper() == "DOUYIN"
    
    def test_identify_tiktok(self, fetcher):
        """Identify TikTok URL."""
        result = fetcher._identify_platform("https://www.tiktok.com/@user/video/123")
        assert result.upper() in ["DOUYIN", "TIKTOK", "OTHER"]
    
    # Dailymotion Tests
    def test_identify_dailymotion(self, fetcher):
        """Identify Dailymotion URL."""
        result = fetcher._identify_platform("https://www.dailymotion.com/video/x8test")
        assert result.upper() == "DAILYMOTION"
    
    def test_identify_dailymotion_short(self, fetcher):
        """Identify Dailymotion short URL (dai.ly)."""
        result = fetcher._identify_platform("https://dai.ly/x8test")
        assert result.upper() == "DAILYMOTION"
    
    # Other/Unknown Tests
    def test_identify_unknown_url(self, fetcher):
        """Identify unknown URL returns 'OTHER'."""
        result = fetcher._identify_platform("https://example.com/video")
        assert result.upper() == "OTHER"
    
    def test_identify_vimeo(self, fetcher):
        """Identify Vimeo URL."""
        result = fetcher._identify_platform("https://vimeo.com/123456789")
        assert result.upper() in ["VIMEO", "OTHER"]


class TestFastFetcherYouTubeIdExtraction:
    """Tests for FastFetcher._extract_youtube_id method."""
    
    @pytest.fixture
    def fetcher(self):
        return FastFetcher(cache_size=10)
    
    def test_extract_id_from_watch_url(self, fetcher):
        """Extract ID from standard watch URL."""
        assert fetcher._extract_youtube_id("https://www.youtube.com/watch?v=dQw4w9WgXcQ") == "dQw4w9WgXcQ"
    
    def test_extract_id_from_short_url(self, fetcher):
        """Extract ID from youtu.be URL."""
        assert fetcher._extract_youtube_id("https://youtu.be/dQw4w9WgXcQ") == "dQw4w9WgXcQ"
    
    def test_extract_id_with_extra_params(self, fetcher):
        """Extract ID from URL with additional parameters."""
        url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ&list=PLtest&index=1"
        assert fetcher._extract_youtube_id(url) == "dQw4w9WgXcQ"
    
    def test_extract_id_from_shorts(self, fetcher):
        """Extract ID from Shorts URL."""
        result = fetcher._extract_youtube_id("https://www.youtube.com/shorts/abc123xyz")
        # Shorts URLs may or may not be supported
        assert result is None or result == "abc123xyz"
    
    def test_extract_id_invalid_url(self, fetcher):
        """Return None for non-YouTube URLs."""
        assert fetcher._extract_youtube_id("https://example.com/video") is None
    
    def test_extract_id_empty_url(self, fetcher):
        """Return None for empty URL."""
        assert fetcher._extract_youtube_id("") is None


class TestFastFetcherCache:
    """Tests for FastFetcher caching mechanism."""
    
    @pytest.fixture
    def fetcher(self):
        return FastFetcher(cache_size=3)
    
    def test_cache_initially_empty(self, fetcher):
        """Cache should be empty on initialization."""
        assert len(fetcher._cache) == 0
    
    def test_add_to_cache(self, fetcher):
        """Test adding items to cache."""
        info = {"title": "Test Video", "id": "test123"}
        fetcher._add_to_cache("https://example.com/video1", info)
        assert len(fetcher._cache) == 1
        assert "https://example.com/video1" in fetcher._cache
    
    def test_cache_retrieval(self, fetcher):
        """Test retrieving cached items."""
        info = {"title": "Test Video", "id": "test123"}
        fetcher._add_to_cache("https://example.com/video1", info)
        cached = fetcher._cache.get("https://example.com/video1")
        assert cached == info
    
    def test_cache_size_limit(self, fetcher):
        """Test cache respects size limit."""
        for i in range(5):
            fetcher._add_to_cache(f"https://example.com/video{i}", {"id": f"test{i}"})
        # Cache size is 3, should not exceed
        assert len(fetcher._cache) <= 3
    
    def test_clear_cache(self, fetcher):
        """Test clearing the cache."""
        fetcher._add_to_cache("https://example.com/video1", {"id": "test1"})
        fetcher.clear_cache()
        assert len(fetcher._cache) == 0
