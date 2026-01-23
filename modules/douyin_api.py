# -*- coding: utf-8 -*-
"""
Douyin video extractor using DrissionPage.
Uses system Chrome/Edge browser for automation.
"""
import os
import re
from datetime import datetime

# Lazy load DrissionPage
ChromiumPage = None


class DouyinDownloader:
    def __init__(self, headless=True):
        self.headless = headless
        self.page = None
        self._check_dependencies()

    def _check_dependencies(self):
        global ChromiumPage
        if ChromiumPage is None:
            try:
                from DrissionPage import ChromiumPage as _ChromiumPage
                ChromiumPage = _ChromiumPage
            except ImportError:
                print("[Douyin] DrissionPage not installed.")
                ChromiumPage = None

    def get_video_info(self, url):
        """
        Main entry point. Extracts video info from Douyin URL.
        Returns dict with keys: title, url, thumbnail, duration, uploader, extractor_key
        """
        if ChromiumPage is None:
            return None, "Module 'DrissionPage' missing. Run: pip install DrissionPage"

        try:
            print(f"[Douyin] Launching browser (Headless: {self.headless})...")
            
            # Configure browser options
            from DrissionPage import ChromiumOptions
            
            co = ChromiumOptions()
            if self.headless:
                co.headless()
            
            # Anti-detection settings
            co.set_argument('--disable-blink-features=AutomationControlled')
            co.set_argument('--disable-gpu')
            co.set_argument('--no-sandbox')
            co.set_argument('--disable-dev-shm-usage')
            
            # Create page
            page = ChromiumPage(co)
            
            # Navigate to URL
            print(f"[Douyin] Navigating to {url}...")
            page.get(url)
            
            # Wait for page to load
            page.wait.load_start()
            
            # Try Method A: DOM Scraping (primary for DrissionPage)
            print("[Douyin] Extracting video info from DOM...")
            result = self._fetch_dom(page, url)
            
            # Close browser
            try:
                page.quit()
            except:
                pass
            
            if result:
                return result, None
            else:
                return None, "Failed to extract video info."

        except Exception as e:
            error_str = str(e)
            print(f"[Douyin] Error: {error_str}")
            
            # Check for browser not found error
            if "chrome" in error_str.lower() and ("not found" in error_str.lower() or "没有找到" in error_str):
                return None, "BROWSER_NOT_FOUND"
            if "edge" in error_str.lower() and "not found" in error_str.lower():
                return None, "BROWSER_NOT_FOUND"
            
            return None, f"DrissionPage Error: {error_str}"

    def _clean_title(self, text):
        """Sanitize title: remove hashtags, newlines, and suffix."""
        if not text:
            return "Douyin Video"
        
        # Remove suffix
        text = text.replace(" - 抖音", "").replace(" - Douyin", "")
        
        # Remove hashtags (e.g. #fyp #funny)
        text = re.sub(r'#\S+', '', text)
        
        # Remove newlines and extra spaces
        text = text.replace('\n', ' ').replace('\r', '')
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text if text else "Douyin Video"

    def _fetch_dom(self, page, url):
        """
        Extract video info from DOM using DrissionPage.
        """
        try:
            # Wait for video element to appear
            video_ele = page.ele('@tag()=video', timeout=15)
            
            if not video_ele:
                print("[Douyin] No video element found")
                return None
            
            # Get video source URL
            src_url = video_ele.attr('src')
            
            # If src is blob, try to find source tag
            if not src_url or "blob:" in src_url:
                source_ele = page.ele('tag:video@|tag:source')
                if source_ele:
                    src_url = source_ele.attr('src')
            
            # Still no URL? Try JavaScript extraction
            if not src_url or "blob:" in src_url:
                try:
                    src_url = page.run_js("""
                        const v = document.querySelector('video');
                        const s = v ? v.querySelector('source') : null;
                        return s ? s.src : (v ? v.src : null);
                    """)
                except:
                    pass
            
            if not src_url or "blob:" in src_url:
                print("[Douyin] Could not extract non-blob video URL")
                return None
            
            # Extract title
            title = ""
            try:
                # Try specific Douyin selectors
                desc_ele = page.ele('[data-e2e="video-desc"]', timeout=2)
                if desc_ele:
                    title = desc_ele.text
                else:
                    # Fallback to meta description
                    meta_ele = page.ele('@@tag()=meta@@name=description', timeout=2)
                    if meta_ele:
                        title = meta_ele.attr('content')
                    else:
                        # Final fallback: page title
                        title = page.title
            except:
                title = page.title
            
            clean_title = self._clean_title(title)
            
            # Try to get thumbnail
            thumbnail = ""
            try:
                poster = video_ele.attr('poster')
                if poster:
                    thumbnail = poster
                else:
                    # Try og:image meta tag
                    og_img = page.ele('@@tag()=meta@@property=og:image', timeout=2)
                    if og_img:
                        thumbnail = og_img.attr('content')
            except:
                pass
            
            # Try to get uploader
            uploader = "Douyin User"
            try:
                # Common Douyin author selectors
                author_ele = page.ele('[data-e2e="video-author-name"]', timeout=2)
                if author_ele:
                    uploader = author_ele.text
            except:
                pass
            
            return {
                "title": clean_title,
                "url": src_url,
                "thumbnail": thumbnail,
                "duration": 0,  # Hard to get from DOM
                "uploader": uploader,
                "extractor_key": "Douyin (DrissionPage)"
            }
            
        except Exception as e:
            print(f"[Douyin] DOM extraction error: {e}")
            return None
