"""
Tests for bilibili_api.py module.
"""
import pytest
import os
import sys

# Import the module under test
from bilibili_api import BilibiliAPI


class TestBilibiliAPIMixinKey:
    """Tests for BilibiliAPI.get_mixin_key method."""
    
    @pytest.fixture
    def api(self):
        """Create a BilibiliAPI instance."""
        return BilibiliAPI()
    
    def test_mixin_key_returns_string(self, api):
        """get_mixin_key should return a string."""
        # Sample key (64 chars)
        orig = "a" * 64
        result = api.get_mixin_key(orig)
        assert isinstance(result, str)
    
    def test_mixin_key_length(self, api):
        """get_mixin_key should return 32-character string."""
        orig = "abcdefghijklmnopqrstuvwxyz0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ01"
        result = api.get_mixin_key(orig)
        assert len(result) == 32
    
    def test_mixin_key_deterministic(self, api):
        """get_mixin_key should be deterministic (same input = same output)."""
        orig = "a" * 64
        result1 = api.get_mixin_key(orig)
        result2 = api.get_mixin_key(orig)
        assert result1 == result2
    
    def test_mixin_key_different_inputs(self, api):
        """get_mixin_key should produce different outputs for different inputs."""
        orig1 = "a" * 64
        orig2 = "b" * 64
        result1 = api.get_mixin_key(orig1)
        result2 = api.get_mixin_key(orig2)
        assert result1 != result2


class TestBilibiliAPIEncWbi:
    """Tests for BilibiliAPI.enc_wbi method."""
    
    @pytest.fixture
    def api(self):
        return BilibiliAPI()
    
    def test_enc_wbi_adds_wts(self, api):
        """enc_wbi should add 'wts' timestamp to params."""
        params = {"bvid": "BV1test", "cid": 12345}
        img_key = "a" * 32
        sub_key = "b" * 32
        result = api.enc_wbi(params, img_key, sub_key)
        assert "wts" in result
    
    def test_enc_wbi_adds_w_rid(self, api):
        """enc_wbi should add 'w_rid' signature to params."""
        params = {"bvid": "BV1test", "cid": 12345}
        img_key = "a" * 32
        sub_key = "b" * 32
        result = api.enc_wbi(params, img_key, sub_key)
        assert "w_rid" in result
    
    def test_enc_wbi_signature_is_hex(self, api):
        """w_rid should be a valid MD5 hex string (32 chars)."""
        params = {"bvid": "BV1test"}
        img_key = "a" * 32
        sub_key = "b" * 32
        result = api.enc_wbi(params, img_key, sub_key)
        w_rid = result["w_rid"]
        assert len(w_rid) == 32
        assert all(c in "0123456789abcdef" for c in w_rid)
    
    def test_enc_wbi_preserves_original_params(self, api):
        """enc_wbi should preserve original parameters."""
        params = {"bvid": "BV1test", "cid": 12345, "qn": 80}
        img_key = "a" * 32
        sub_key = "b" * 32
        result = api.enc_wbi(params, img_key, sub_key)
        assert result["bvid"] == "BV1test"
        assert result["cid"] == "12345" or result["cid"] == 12345
        assert result["qn"] == "80" or result["qn"] == 80
    
    def test_enc_wbi_filters_special_chars(self, api):
        """enc_wbi should filter special characters from values."""
        params = {"title": "Test!'()*Video"}
        img_key = "a" * 32
        sub_key = "b" * 32
        result = api.enc_wbi(params, img_key, sub_key)
        # Special chars should be removed
        assert "!" not in result["title"]
        assert "'" not in result["title"]
        assert "(" not in result["title"]
        assert ")" not in result["title"]
        assert "*" not in result["title"]


class TestBilibiliAPIInit:
    """Tests for BilibiliAPI initialization."""
    
    def test_init_without_cookie(self):
        """BilibiliAPI should initialize without cookie."""
        api = BilibiliAPI()
        assert api.cookies == {}
    
    def test_init_with_nonexistent_cookie_path(self):
        """BilibiliAPI should handle non-existent cookie path."""
        api = BilibiliAPI(cookie_path="/nonexistent/path/cookies.txt")
        assert api.cookies == {}
    
    def test_user_agent_set(self):
        """BilibiliAPI should have user agent set."""
        api = BilibiliAPI()
        assert api.user_agent is not None
        assert "Mozilla" in api.user_agent


class TestBilibiliAPIHeaders:
    """Tests for BilibiliAPI._get_headers method."""
    
    @pytest.fixture
    def api(self):
        return BilibiliAPI()
    
    def test_headers_contain_user_agent(self, api):
        """Headers should contain User-Agent."""
        headers = api._get_headers()
        assert "User-Agent" in headers
        assert headers["User-Agent"] == api.user_agent
    
    def test_headers_contain_referer(self, api):
        """Headers should contain Referer."""
        headers = api._get_headers()
        assert "Referer" in headers
    
    def test_custom_referer(self, api):
        """Headers should use custom referer when provided."""
        custom_referer = "https://www.bilibili.com/video/BV1test"
        headers = api._get_headers(referer=custom_referer)
        assert headers["Referer"] == custom_referer
    
    def test_default_referer(self, api):
        """Headers should use default referer when not provided."""
        headers = api._get_headers()
        assert "bilibili.com" in headers["Referer"]
