# tsufutube/fetcher.py
"""
Fast Video Info Fetcher - Tiered Strategy
==========================================
Tier 1: Platform APIs (YouTube oEmbed, Bilibili API) - ~100-500ms
Tier 2: yt-dlp extract_flat                          - ~1-3s
Tier 3: Full yt-dlp extraction (fallback)            - ~5-10s
"""

import re
import json
import threading
from urllib.request import urlopen, Request
from urllib.parse import quote_plus, urlparse
from urllib.error import URLError, HTTPError

# --- LAZY IMPORT FOR YT-DLP ---
yt_dlp = None
_ytdlp_import_lock = threading.Lock()
_ytdlp_prewarmed = False

def _prewarm_ytdlp():
    """Import yt-dlp in background to avoid first-call delay."""
    global yt_dlp, _ytdlp_prewarmed
    if _ytdlp_prewarmed:
        return
    with _ytdlp_import_lock:
        if yt_dlp is None:
            try:
                import yt_dlp as _yt_dlp
                yt_dlp = _yt_dlp
                _ytdlp_prewarmed = True
            except ImportError:
                pass

def _ensure_ytdlp():
    """Ensure yt-dlp is loaded, blocking if necessary."""
    global yt_dlp
    if yt_dlp is None:
        _prewarm_ytdlp()
    return yt_dlp


class FastFetcher:
    """
    Fast video info fetcher with tiered strategy and caching.
    """
    
    def __init__(self, cache_size=50):
        self._cache = {}  # url -> info
        self._cache_size = cache_size
        
        # Start prewarming yt-dlp in background immediately
        threading.Thread(target=_prewarm_ytdlp, daemon=True).start()
    
    def fetch(self, url, timeout=10):
        """
        Fetch video info using tiered strategy.
        Returns: (info_dict, error_string) or (None, error_string) on failure.
        """
        url = url.strip()
        if not url:
            return None, "Empty URL"
        
        # Check cache first
        if url in self._cache:
            print(f"[Fetcher] Cache hit for {url[:50]}...")
            return self._cache[url], None
        
        platform = self._identify_platform(url)
        info = None
        error = None
        
        # Detect playlist (skip Tier 1 for playlists - oEmbed doesn't handle them well)
        is_playlist_url = 'list=' in url or '/playlist' in url
        
        # --- TIER 1: Fast Platform APIs (skip for playlists) ---
        if not is_playlist_url:
            if platform == "YOUTUBE":
                print(f"[Fetcher] Tier 1: YouTube oEmbed...")
                info, error = self._fetch_youtube_oembed(url, timeout)
                if info:
                    print(f"[Fetcher] Tier 1 SUCCESS: {info.get('title', '?')[:40]}")
            elif platform == "BILIBILI":
                print(f"[Fetcher] Tier 1: Bilibili API...")
                info, error = self._fetch_bilibili_api(url, timeout)
                if info:
                    print(f"[Fetcher] Tier 1 SUCCESS: {info.get('title', '?')[:40]}")
            elif platform == "DOUYIN":
                print(f"[Fetcher] Tier 1: Douyin API...")
                info, error = self._fetch_douyin_api(url)
                if info:
                    print(f"[Fetcher] Tier 1 SUCCESS: {info.get('title', '?')[:40]}")
            elif platform == "DAILYMOTION":
                print(f"[Fetcher] Tier 1: Dailymotion API...")
                info, error = self._fetch_dailymotion_api(url)
                if info:
                    print(f"[Fetcher] Tier 1 SUCCESS: {info.get('title', '?')[:40]}")
            elif platform == "TIKTOK":
                print(f"[Fetcher] Tier 1: TikTok API (SnapTik-like)...")
                info, error = self._fetch_tiktok_api(url)
                if info:
                    print(f"[Fetcher] Tier 1 SUCCESS: {info.get('title', '?')[:40]}")
        else:
            print(f"[Fetcher] Playlist detected, skipping Tier 1")
        
        # --- TIER 2: yt-dlp extract_flat (if Tier 1 failed or unsupported) ---
        if info is None:
            print(f"[Fetcher] Tier 2: yt-dlp flat... (Tier 1 error: {error})")
            info, error = self._fetch_ytdlp_flat(url, timeout=30)
            if info:
                print(f"[Fetcher] Tier 2 SUCCESS: {info.get('title', '?')[:40]}")
        
        # --- TIER 3: Full yt-dlp extraction (last resort) ---
        if info is None:
            print(f"[Fetcher] Tier 3: yt-dlp full... (Tier 2 error: {error})")
            info, error = self._fetch_ytdlp_full(url, timeout=60)
            if info:
                print(f"[Fetcher] Tier 3 SUCCESS: {info.get('title', '?')[:40]}")
        
        if info is None:
            print(f"[Fetcher] ALL TIERS FAILED. Final error: {error}")
        
        # Cache successful result
        if info:
            self._add_to_cache(url, info)
        
        return info, error
    
    def _identify_platform(self, url):
        """Identify platform from URL."""
        if not url:
            return "UNKNOWN"
        url_lower = url.lower()
        if "youtube.com" in url_lower or "youtu.be" in url_lower:
            return "YOUTUBE"
        if "bilibili.com" in url_lower:
            return "BILIBILI"
        if "instagram.com" in url_lower:
            return "INSTAGRAM"
        if "tiktok.com" in url_lower:
            return "TIKTOK"
        if "twitter.com" in url_lower or "x.com" in url_lower:
            return "TWITTER"
        if "douyin.com" in url_lower:
            return "DOUYIN"
        if "dailymotion.com" in url_lower or "dai.ly" in url_lower:
            return "DAILYMOTION"
        return "OTHER"
    
    def _add_to_cache(self, url, info):
        """Add to cache with size limit (LRU-like)."""
        if len(self._cache) >= self._cache_size:
            # Remove oldest entry
            try:
                oldest_key = next(iter(self._cache))
                del self._cache[oldest_key]
            except StopIteration:
                pass
        self._cache[url] = info
    
    # =========================================================================
    # TIER 1: Fast Platform APIs
    # =========================================================================
    
    def _fetch_youtube_oembed(self, url, timeout=10):
        """
        Fetch YouTube info using oEmbed API. VERY FAST (~100-300ms).
        Returns: (info_dict, error) or (None, error)
        """
        try:
            # Extract video ID for thumbnail
            video_id = self._extract_youtube_id(url)
            
            oembed_url = f"https://www.youtube.com/oembed?url={quote_plus(url)}&format=json"
            req = Request(oembed_url, headers={"User-Agent": "Mozilla/5.0"})
            
            with urlopen(req, timeout=timeout) as response:
                data = json.loads(response.read().decode('utf-8'))
            
            # Construct info dict compatible with existing code
            info = {
                "title": data.get("title", "Unknown"),
                "uploader": data.get("author_name", "Unknown"),
                "uploader_url": data.get("author_url", ""),
                "thumbnail": f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg" if video_id else data.get("thumbnail_url", ""),
                "duration_string": "??:??",  # oEmbed doesn't provide duration
                "duration": 0,
                "webpage_url": url,
                "extractor_key": "Youtube",
                "_fetcher_tier": 1,
            }
            return info, None
            
        except HTTPError as e:
            return None, f"HTTP {e.code}"
        except URLError as e:
            return None, f"Network error: {e.reason}"
        except Exception as e:
            return None, str(e)
    
    def _extract_youtube_id(self, url):
        """Extract YouTube video ID from URL."""
        patterns = [
            r'(?:v=|/v/|youtu\.be/)([a-zA-Z0-9_-]{11})',
            r'(?:embed/|shorts/)([a-zA-Z0-9_-]{11})',
        ]
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        return None
    
    def _fetch_bilibili_api(self, url, timeout=10):
        """
        Fetch Bilibili info using public API.
        """
        try:
            match = re.search(r'(BV\w+)', url)
            if not match:
                return None, "Invalid Bilibili URL (missing BV ID)"
            
            bvid = match.group(1)
            api_url = f"https://api.bilibili.com/x/web-interface/view?bvid={bvid}"
            req = Request(api_url, headers={
                "User-Agent": "Mozilla/5.0",
                "Referer": "https://www.bilibili.com/"
            })
            
            with urlopen(req, timeout=timeout) as response:
                data = json.loads(response.read().decode('utf-8'))
            
            if data.get('code') != 0:
                return None, f"Bilibili API error: {data.get('message', 'Unknown')}"
            
            d = data.get('data', {})
            duration = d.get('duration', 0)
            
            info = {
                "title": d.get("title", f"Bilibili {bvid}"),
                "uploader": d.get("owner", {}).get("name", "Unknown"),
                "thumbnail": d.get("pic", ""),
                "duration": duration,
                "duration_string": f"{duration // 60}:{duration % 60:02d}" if duration else "??:??",
                "webpage_url": f"https://www.bilibili.com/video/{bvid}",
                "extractor_key": "Bilibili",
                "_fetcher_tier": 1,
            }
            return info, None
            
        except Exception as e:
            return None, str(e)
    
    def _fetch_douyin_api(self, url):
        """
        Fetch Douyin info using custom DouyinDownloader (Playwright).
        """
        try:
            # Lazy import to avoid Playwright overhead if not used
            try:
                from .douyin_api import DouyinDownloader
            except ImportError:
                return None, "Module douyin_api missing"
                
            dd = DouyinDownloader(headless=True)
            info, error = dd.get_video_info(url)
            
            if info:
                # Normalize duration_string
                d = info.get('duration', 0)
                info['duration_string'] = f"{int(d) // 60}:{int(d) % 60:02d}" if d else "??:??"
                info['extractor_key'] = "Douyin"
                info['_fetcher_tier'] = 1
                return info, None
            
            # Check for browser not installed error - trigger install
            if error == "PLAYWRIGHT_BROWSER_NOT_INSTALLED":
                print("[Fetcher] Playwright browser not installed. Triggering auto-install...")
                try:
                    from .playwright_helper import install_playwright_chromium
                    success, msg = install_playwright_chromium()
                    if success:
                        print("[Fetcher] Playwright installed! Retrying Douyin fetch...")
                        # Retry once after install
                        dd2 = DouyinDownloader(headless=True)
                        info2, error2 = dd2.get_video_info(url)
                        if info2:
                            d = info2.get('duration', 0)
                            info2['duration_string'] = f"{int(d) // 60}:{int(d) % 60:02d}" if d else "??:??"
                            info2['extractor_key'] = "Douyin"
                            info2['_fetcher_tier'] = 1
                            return info2, None
                        return None, error2
                except Exception as install_err:
                    print(f"[Fetcher] Playwright install error: {install_err}")
            
            return None, error or "Douyin fetch failed"
            
        except Exception as e:
            return None, f"Douyin Fetch Error: {str(e)}"

    def _fetch_dailymotion_api(self, url):
        """
        Fetch Dailymotion info using Dailymotion Metadata API.
        """
        try:
            try:
                from .dailymotion_api import DailymotionDownloader
            except ImportError:
                return None, "Module dailymotion_api missing"
                
            dm = DailymotionDownloader()
            info, error = dm.get_video_info(url)
            
            if info:
                 # Clean up data for Fetcher format
                 d = info.get('duration', 0)
                 info['duration_string'] = f"{int(d) // 60}:{int(d) % 60:02d}" if d else "??:??"
                 info['_fetcher_tier'] = 1
                 return info, None
            
            return None, error or "Dailymotion fetch failed"
        except Exception as e:
            return None, f"Dailymotion Fetch Error: {str(e)}"

    def _fetch_tiktok_api(self, url):
        """
        Fetch TikTok info using custom TikTokDownloader (TikWM).
        """
        try:
            try:
                from .tiktok_api import TikTokDownloader
            except ImportError:
                return None, "Module tiktok_api missing"
            
            tt = TikTokDownloader()
            info, error = tt.get_video_info(url)
            
            if info:
                d = info.get('duration', 0)
                info['duration_string'] = f"{int(d) // 60}:{int(d) % 60:02d}" if d else "??:??"
                info['extractor_key'] = "TikTok"
                info['_fetcher_tier'] = 1
                return info, None
            
            return None, error or "TikTok fetch failed"
        except Exception as e:
            return None, f"TikTok Fetch Error: {str(e)}"

    # =========================================================================
    # TIER 2: yt-dlp extract_flat
    # =========================================================================
    
    def _fetch_ytdlp_flat(self, url, timeout=30):
        """
        Fetch using yt-dlp with extract_flat (faster, no format parsing).
        """
        print(f"[Fetcher T2] _fetch_ytdlp_flat: Ensuring yt-dlp loaded...")
        ytdlp = _ensure_ytdlp()
        if ytdlp is None:
            return None, "yt-dlp not available"
        
        print(f"[Fetcher T2] yt-dlp loaded. Creating YoutubeDL instance...")
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': 'in_playlist',  # Only flatten playlists, extract single video normally
            'skip_download': True,
            'noplaylist': True,
            'ignoreerrors': True,
            'socket_timeout': 15,  # Reduced from 30
            'extractor_retries': 1,
            'fragment_retries': 0,
        }
        
        try:
            print(f"[Fetcher T2] Starting extract_info for {url[:50]}...")
            with ytdlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
            print(f"[Fetcher T2] extract_info returned. Info: {bool(info)}")
            
            if info:
                info['_fetcher_tier'] = 2
                # Ensure duration_string exists
                if 'duration_string' not in info and 'duration' in info:
                    d = info['duration']
                    if d:
                        info['duration_string'] = f"{int(d) // 60}:{int(d) % 60:02d}"
                    else:
                        info['duration_string'] = "??:??"
                return info, None
            return None, "No info extracted"
            
        except Exception as e:
            print(f"[Fetcher T2] Exception: {e}")
            return None, str(e)
    
    # =========================================================================
    # TIER 3: Full yt-dlp extraction
    # =========================================================================
    
    def _fetch_ytdlp_full(self, url, timeout=60):
        """
        Full yt-dlp extraction. Slowest but most reliable.
        """
        ytdlp = _ensure_ytdlp()
        if ytdlp is None:
            return None, "yt-dlp not available"
        
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'skip_download': True,
            'noplaylist': True,
            'ignoreerrors': True,
            'socket_timeout': timeout,
        }
        
        try:
            with ytdlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
            
            if info:
                info['_fetcher_tier'] = 3
                # Ensure duration_string
                if 'duration_string' not in info and 'duration' in info:
                    d = info['duration']
                    if d:
                        info['duration_string'] = f"{int(d) // 60}:{int(d) % 60:02d}"
                    else:
                        info['duration_string'] = "??:??"
                return info, None
            return None, "No info extracted"
            
        except Exception as e:
            return None, str(e)
    
    def clear_cache(self):
        """Clear the info cache."""
        self._cache.clear()


# Singleton instance for easy access
_default_fetcher = None

def get_fetcher():
    """Get or create the default FastFetcher instance."""
    global _default_fetcher
    if _default_fetcher is None:
        _default_fetcher = FastFetcher()
    return _default_fetcher
