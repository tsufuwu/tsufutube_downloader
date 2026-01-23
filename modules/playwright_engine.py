import os
import re
import time
from datetime import datetime

# Lazy load logic
playwright = None
sync_playwright = None

class PlaywrightEngine:
    def __init__(self, headless=True):
        self.headless = headless
        self._check_dependencies()

    def _check_dependencies(self):
        global sync_playwright
        if sync_playwright is None:
            try:
                from playwright.sync_api import sync_playwright as _sync_playwright
                sync_playwright = _sync_playwright
            except ImportError:
                sync_playwright = None

    def sniff_video(self, url, timeout=45000):
        """
        Universal fallback: Sniff network and DOM for video links.
        Returns dict or None.
        """
        if sync_playwright is None:
            print("[PlaywrightEngine] Playwright not installed.")
            return None

        # Container for results
        found_video = None
        
        try:
            with sync_playwright() as p:
                print(f"[PlaywrightFallback] Launching browser for {url}...")
                
                # Launch args for stealth/stability
                launch_args = [
                        '--disable-blink-features=AutomationControlled',
                        '--disable-gpu',
                        '--no-sandbox',
                        '--autoplay-policy=no-user-gesture-required'
                ]
                
                try:
                    browser = p.chromium.launch(
                        headless=self.headless,
                        args=launch_args
                    )
                except Exception as e:
                    # Fallback for missing headless shell
                    error_msg = str(e).lower()
                    if "executable doesn't exist" in error_msg and "headless_shell" in error_msg:
                        print("[PlaywrightFallback] Chrome-headless-shell missing. Retrying with standard Chromium binary...")
                        launch_args.append('--headless=new')
                        browser = p.chromium.launch(
                            headless=False, # Use standard binary
                            args=launch_args
                        )
                    else:
                        raise e
                
                context = browser.new_context(
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                    viewport={'width': 1280, 'height': 720},
                    locale="en-US"
                )
                
                # Try stealth
                try:
                    from playwright_stealth import stealth_sync
                    stealth_sync(context)
                except ImportError: pass

                page = context.new_page()
                
                # --- STRATEGY A: Network Sniffing ---
                # We listen for video content types
                video_patterns = [
                    r'video/.*',
                    r'application/x-mpegURL',
                    r'application/vnd.apple.mpegurl',
                    r'.*\.m3u8',
                    r'.*\.mp4'
                ]
                
                def handle_response(response):
                    nonlocal found_video
                    if found_video: return
                    
                    try:
                        # Check URL extension
                        u = response.url.lower()
                        
                        # [TikTok Fix] Filter out login/captcha videos
                        # TikTok often returns a 'playback1.mp4' on the login page or captcha
                        if "playback1.mp4" in u or "login" in u or "captcha" in u:
                            return

                        if ".m3u8" in u or ".mp4" in u:
                                    # Filter out small segments if possible, but hard to know size yet
                            # Just capture it.
                            
                            # [FIX] Capture all relevant headers with simpler logic
                            all_h = response.request.all_headers()
                            
                            found_video = {
                                "url": response.url,
                                "ext": "mp4" if ".mp4" in u else "m3u8",
                                "source": "network",
                                "headers": {
                                    "User-Agent": all_h.get("user-agent", ""),
                                    "Cookie": all_h.get("cookie", ""),
                                    "Referer": all_h.get("referer", "https://www.tiktok.com/"),
                                    "Origin": all_h.get("origin", "https://www.tiktok.com"),
                                    # Accept?
                                }
                            }
                            return

                        # Check Content-Type header
                        ctype = response.header_value("content-type")
                        if ctype:
                            if "video/" in ctype or "mpegurl" in ctype.lower():
                                all_h = response.request.all_headers()
                                found_video = {
                                    "url": response.url,
                                    "ext": "mp4" if "mp4" in ctype else "m3u8",
                                    "source": "network",
                                    "headers": {
                                        "User-Agent": all_h.get("user-agent", ""),
                                        "Cookie": all_h.get("cookie", ""),
                                        "Referer": all_h.get("referer", "https://www.tiktok.com/"),
                                        "Origin": all_h.get("origin", "https://www.tiktok.com"),
                                    }
                                }
                    except: pass

                page.on("response", handle_response)
                
                # Navigate
                try:
                    # [FIX] Dailymotion/Generic Interaction Logic
                    page.goto(url, timeout=timeout, wait_until="domcontentloaded")
                    
                    # 1. Handle Cookie/Consent Popups
                    try:
                        # Common selector for "Accept All" buttons
                        page.click('button:has-text("Accept")', timeout=2000)
                        page.click('button:has-text("Agree")', timeout=2000)
                        page.click('div[aria-label="Consent"]', timeout=2000)
                    except: pass

                    # 2. Handle "Tap to Unmute" or big Play buttons
                    try:
                        page.click('button[aria-label="Play"]', timeout=2000)
                        page.click('.player-poster', timeout=2000)
                        page.click('video', timeout=2000)
                    except: pass
                    
                    # Wait/Scroll
                    page.mouse.wheel(0, 500)
                    page.wait_for_timeout(3000)
                except Exception as e:
                    print(f"[PlaywrightFallback] Nav error: {e}")
                
                # Wait more if nothing found yet
                if not found_video:
                    page.wait_for_timeout(5000)
                
                # --- STRATEGY B: DOM Scanning ---
                if not found_video:
                    print("[PlaywrightFallback] Network sniff empty. Scanning DOM...")
                    
                    # 1. Check <video src="..."> using multiple strategies
                    # Dailymotion uses blob usually, which this won't catch directly, 
                    # hence why Network Sniffing is crucial.
                    try:
                         # Force evaluate to find any video tag
                         src = page.evaluate("""() => {
                            const v = document.querySelector('video');
                            if (v && v.src) return v.src;
                            const s = document.querySelector('video source');
                            return s ? s.src : null;
                        }""")
                    except: src = None
                    
                    if src and not src.startswith("blob:"):
                        found_video = {
                            "url": src,
                            "ext": "mp4", # Assume mp4 for direct src
                            "source": "dom"
                        }
                
                # Harvest Title - try multiple sources for better title
                title = None
                try:
                    # Priority 1: og:title meta tag (most reliable for video title)
                    title = page.evaluate("""() => {
                        const ogTitle = document.querySelector('meta[property="og:title"]');
                        if (ogTitle) return ogTitle.getAttribute('content');
                        const twitterTitle = document.querySelector('meta[name="twitter:title"]');
                        if (twitterTitle) return twitterTitle.getAttribute('content');
                        return null;
                    }""")
                except: pass
                
                # Priority 2: page title, but clean it
                if not title or len(title.strip()) < 3:
                    title = page.title()
                    
                # Clean title - remove common website suffixes
                if title:
                    # Remove common patterns like "- Dailymotion", "| YouTube", etc.
                    import re as _re
                    title = _re.sub(r'\s*[-|–—]\s*(Dailymotion|YouTube|Vimeo|Facebook|Watch|Video|Watch Video).*$', '', title, flags=_re.IGNORECASE)
                    title = title.strip()
                
                if not title or len(title.strip()) < 3:
                    title = f"Video_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                
                browser.close()
                
                if found_video:
                    found_video["title"] = title
                    # Add extractor key just in case
                    found_video["extractor_key"] = "PlaywrightFallback"
                    print(f"[PlaywrightFallback] Success! Found: {found_video['url'][:50]}...")
                    return found_video
                else:
                    print("[PlaywrightFallback] No video found.")
                    return None
                    
        except Exception as e:
            error_str = str(e)
            print(f"[PlaywrightFallback] Error: {error_str}")
            # Check if this is a "browser not installed" error
            if "executable doesn't exist" in error_str.lower() or "executable does not exist" in error_str.lower():
                # Return a special dict indicating browser needs install
                return {"error": "PLAYWRIGHT_BROWSER_NOT_INSTALLED", "message": error_str}
            return None
