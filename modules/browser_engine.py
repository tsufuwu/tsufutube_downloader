# -*- coding: utf-8 -*-
"""
Browser-based video sniffer using DrissionPage.
Universal fallback for extracting video URLs from web pages.
Uses system Chrome/Edge browser.
"""
import os
import re
from datetime import datetime

# Lazy load DrissionPage
ChromiumPage = None
ChromiumOptions = None


class BrowserEngine:
    """
    Universal video sniffer using DrissionPage.
    Extracts video URLs from web pages via DOM inspection.
    """
    
    def __init__(self, headless=True):
        self.headless = headless
        self._check_dependencies()

    def _check_dependencies(self):
        global ChromiumPage, ChromiumOptions
        if ChromiumPage is None:
            try:
                from DrissionPage import ChromiumPage as _ChromiumPage
                from DrissionPage import ChromiumOptions as _ChromiumOptions
                ChromiumPage = _ChromiumPage
                ChromiumOptions = _ChromiumOptions
            except ImportError:
                ChromiumPage = None
                ChromiumOptions = None

    def sniff_video(self, url, timeout=45):
        """
        Universal fallback: Extract video URL from any webpage.
        Returns dict with url, title, ext, etc. or None.
        """
        if ChromiumPage is None:
            print("[BrowserEngine] DrissionPage not installed.")
            return None

        found_video = None
        
        try:
            print(f"[BrowserEngine] Launching browser for {url}...")
            
            # Configure browser
            co = ChromiumOptions()
            if self.headless:
                co.headless()
            
            co.set_argument('--disable-blink-features=AutomationControlled')
            co.set_argument('--disable-gpu')
            co.set_argument('--no-sandbox')
            co.set_argument('--autoplay-policy=no-user-gesture-required')
            
            page = ChromiumPage(co)
            
            # Navigate
            print(f"[BrowserEngine] Navigating to {url}...")
            page.get(url)
            page.wait.load_start()
            
            # Handle common popups
            self._handle_popups(page)
            
            # Wait a bit for video to load
            page.wait(2)
            
            # Scroll to trigger lazy loading
            try:
                page.scroll.down(500)
            except:
                pass
            
            page.wait(2)
            
            # --- STRATEGY: DOM Scanning ---
            print("[BrowserEngine] Scanning DOM for video...")
            found_video = self._extract_video_from_dom(page)
            
            # Get title
            title = self._extract_title(page)
            
            # Close browser
            try:
                page.quit()
            except:
                pass
            
            if found_video:
                found_video["title"] = title
                found_video["extractor_key"] = "BrowserEngine"
                print(f"[BrowserEngine] Success! Found: {found_video['url'][:50]}...")
                return found_video
            else:
                print("[BrowserEngine] No video found.")
                return None
                
        except Exception as e:
            error_str = str(e)
            print(f"[BrowserEngine] Error: {error_str}")
            
            # Check for browser not found
            if "chrome" in error_str.lower() and ("not found" in error_str.lower() or "没有找到" in error_str):
                return {"error": "BROWSER_NOT_FOUND", "message": error_str}
            if "edge" in error_str.lower() and "not found" in error_str.lower():
                return {"error": "BROWSER_NOT_FOUND", "message": error_str}
                
            return None

    def _handle_popups(self, page):
        """Handle common consent/cookie popups."""
        popup_selectors = [
            'button:contains("Accept")',
            'button:contains("Agree")',
            'button:contains("OK")',
            'button:contains("I agree")',
            '[aria-label="Accept"]',
            '[aria-label="Consent"]',
            '.cookie-accept',
            '#accept-cookies',
        ]
        
        for selector in popup_selectors:
            try:
                btn = page.ele(selector, timeout=1)
                if btn:
                    btn.click()
                    page.wait(0.5)
                    break
            except:
                pass
        
        # Try clicking play button
        play_selectors = [
            'button[aria-label="Play"]',
            '.player-poster',
            '.play-button',
            '[data-testid="play-button"]',
        ]
        
        for selector in play_selectors:
            try:
                btn = page.ele(selector, timeout=1)
                if btn:
                    btn.click()
                    page.wait(1)
                    break
            except:
                pass

    def _extract_video_from_dom(self, page):
        """Extract video URL from DOM."""
        try:
            # Method 1: Direct video element
            video_ele = page.ele('@tag()=video', timeout=5)
            if video_ele:
                src = video_ele.attr('src')
                if src and not src.startswith('blob:'):
                    return {
                        "url": src,
                        "ext": self._guess_ext(src),
                        "source": "dom"
                    }
                
                # Try source child
                source_ele = video_ele.ele('@tag()=source', timeout=2)
                if source_ele:
                    src = source_ele.attr('src')
                    if src and not src.startswith('blob:'):
                        return {
                            "url": src,
                            "ext": self._guess_ext(src),
                            "source": "dom"
                        }
            
            # Method 2: JavaScript extraction
            src = page.run_js("""
                const v = document.querySelector('video');
                if (!v) return null;
                if (v.src && !v.src.startsWith('blob:')) return v.src;
                const s = v.querySelector('source');
                if (s && s.src && !s.src.startsWith('blob:')) return s.src;
                return null;
            """)
            
            if src:
                return {
                    "url": src,
                    "ext": self._guess_ext(src),
                    "source": "js"
                }
            
            # Method 3: Look for video links in page content
            # (m3u8, mp4 links in scripts or data attributes)
            video_link = page.run_js("""
                const scripts = document.querySelectorAll('script');
                for (const s of scripts) {
                    const text = s.textContent || '';
                    const m3u8Match = text.match(/(https?:[^"'\\s]+\\.m3u8[^"'\\s]*)/);
                    if (m3u8Match) return m3u8Match[1];
                    const mp4Match = text.match(/(https?:[^"'\\s]+\\.mp4[^"'\\s]*)/);
                    if (mp4Match) return mp4Match[1];
                }
                return null;
            """)
            
            if video_link:
                return {
                    "url": video_link.replace('\\u002F', '/'),
                    "ext": "m3u8" if ".m3u8" in video_link else "mp4",
                    "source": "script"
                }
                
        except Exception as e:
            print(f"[BrowserEngine] DOM extraction error: {e}")
        
        return None

    def _extract_title(self, page):
        """Extract page title."""
        title = None
        
        try:
            # Priority 1: og:title
            og_title = page.ele('@@tag()=meta@@property=og:title', timeout=2)
            if og_title:
                title = og_title.attr('content')
            
            # Priority 2: twitter:title
            if not title:
                tw_title = page.ele('@@tag()=meta@@name=twitter:title', timeout=2)
                if tw_title:
                    title = tw_title.attr('content')
            
            # Priority 3: page title
            if not title:
                title = page.title
        except:
            title = page.title
        
        # Clean title
        if title:
            title = re.sub(r'\s*[-|–—]\s*(Dailymotion|YouTube|Vimeo|Facebook|Watch|Video|TikTok).*$', 
                          '', title, flags=re.IGNORECASE)
            title = title.strip()
        
        if not title or len(title) < 3:
            title = f"Video_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        return title

    def _guess_ext(self, url):
        """Guess file extension from URL."""
        url_lower = url.lower()
        if '.m3u8' in url_lower:
            return 'm3u8'
        elif '.mp4' in url_lower:
            return 'mp4'
        elif '.webm' in url_lower:
            return 'webm'
        else:
            return 'mp4'


# Compatibility alias for existing code that imports PlaywrightEngine
PlaywrightEngine = BrowserEngine
