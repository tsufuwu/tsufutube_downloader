import os
import time
import json
import re
from datetime import datetime

# Lazy load playwright to avoid heavy startup if not used
playwright = None
sync_playwright = None

class DouyinDownloader:
    def __init__(self, headless=True):
        self.headless = headless
        self.browser = None
        self.playwright = None
        self._check_dependencies()

    def _check_dependencies(self):
        global playwright, sync_playwright
        if sync_playwright is None:
            try:
                from playwright.sync_api import sync_playwright as _sync_playwright
                sync_playwright = _sync_playwright
            except ImportError:
                print("Playwright not installed.")
                sync_playwright = None

    def get_video_info(self, url):
        """
        Main entry point. Tries Method B (Network) first, then Method A (DOM).
        Returns dict with keys: title, url, thumbnail, duration, author, extractor_key
        """
        if sync_playwright is None:
            return None, "Module 'playwright' missing. Run: pip install playwright && playwright install chromium"

        try:
            with sync_playwright() as p:
                # Launch Browser
                # Use robust args to avoid detection and improve stability
                browser_args = [
                    '--disable-blink-features=AutomationControlled',
                    '--disable-gpu',
                    '--no-sandbox',
                    '--disable-dev-shm-usage'
                ]
                
                print(f"[Douyin] Launching browser (Headless: {self.headless})...")
                browser = p.chromium.launch(
                    headless=self.headless, 
                    args=browser_args
                )
                
                # Create Context with mobile emulation potentially? 
                # No, desktop usually gets better quality JSON.
                # Use Stealth if available
                context = browser.new_context(
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                    viewport={'width': 1920, 'height': 1080},
                    locale="en-US"
                )
                
                try:
                    from playwright_stealth import stealth_sync
                    stealth_sync(context)
                except ImportError:
                    pass # Optional
                
                page = context.new_page()
                
                # --- METHOD B: NETWORK INTERCEPTION (Best Quality) ---
                print("[Douyin] Trying Method B: Network Interception...")
                result_b = self._fetch_network(page, url)
                
                if result_b:
                    print("[Douyin] Method B Success!")
                    browser.close()
                    return result_b, None
                
                # --- METHOD A: DOM SCRAPING (Fallback) ---
                print("[Douyin] Method B failed/timeout. Trying Method A: DOM Scraping...")
                result_a = self._fetch_dom(page, url)
                
                browser.close()
                
                if result_a:
                    return result_a, None
                else:
                    return None, "Failed to extract video by any method."

        except Exception as e:
            return None, f"Playwright Error: {str(e)}"

    def _fetch_network(self, page, url):
        """
        Method B: Intercept JSON response for high quality video
        Target API: /aweme/v1/web/aweme/detail/
        """
        final_data = {}
        found_event = False
        
        def handle_response(response):
            nonlocal found_event, final_data
            if found_event: return
            
            if "/aweme/v1/web/aweme/detail/" in response.url and response.status == 200:
                try:
                    json_data = response.json()
                    aweme_detail = json_data.get("aweme_detail")
                    if aweme_detail:
                        # Extract Info
                        video_obj = aweme_detail.get("video", {})
                        play_addr = video_obj.get("play_addr", {})
                        url_list = play_addr.get("url_list", [])
                        
                        # Get best URL (usually last one is highest quality or main CDN)
                        # We specifically look for the one NOT starting with 'p' (preview) if possible, 
                        # but Douyin usually gives good ones here.
                        # Usually the 3rd or 4th link is best, or just pick the first valid one.
                        # Let's take the first one that is non-empty.
                        video_url = next((u for u in url_list if u), None)
                        
                        if video_url:
                            final_data = {
                                "title": aweme_detail.get("desc", f"Douyin {aweme_detail.get('aweme_id')}"),
                                "url": video_url,
                                "thumbnail": video_obj.get("cover", {}).get("url_list", [""])[0],
                                "duration": video_obj.get("duration", 0) / 1000.0, # ms to sec
                                "uploader": aweme_detail.get("author", {}).get("nickname", "Douyin User"),
                                "extractor_key": "Douyin (API)"
                            }
                            found_event = True
                except:
                    pass

        # Attach listener
        page.on("response", handle_response)
        
        try:
            page.goto(url, timeout=30000)
            # Wait a bit for requests to fly
            # Sometimes we need to scroll or wait for initial load
            page.wait_for_timeout(5000) 
            
            # Anti-bot: Random scroll
            page.mouse.wheel(0, 500)
            page.wait_for_timeout(2000)
            
            if found_event: return final_data
            
        except Exception as e:
            print(f"[Douyin] Net wait err: {e}")
            
        return None

    def _fetch_dom(self, page, url):
        """
        Method A: Scrape <video> tag from DOM
        """
        try:
            # If we are already on the page from Method B, we don't need to goto again 
            # unless Method B crashed early.
            if page.url == "about:blank":
                page.goto(url, timeout=30000)
            
            # Wait for video tag
            video_element = page.wait_for_selector("video", timeout=15000)
            if not video_element: return None
            
            # Get properties
            # 1. SRC list
            src_url = video_element.get_attribute("src")
            # Sometimes src is blob, then we scrape source tags
            if not src_url or "blob:" in src_url:
                src_url = page.evaluate("""() => {
                    const v = document.querySelector('video');
                    const s = v.querySelector('source');
                    return s ? s.src : v.src;
                }""")
            
            if not src_url: return None
            
            # 2. Description
            # Douyin title is usually in a p tag or h1
            # Selectors vary, generic attempt:
            title = page.title()
            try:
                # Try to find specific description container
                desc_el = page.query_selector('.desc-wrapper span') 
                if desc_el: title = desc_el.inner_text()
            except: pass
            
            return {
                "title": title,
                "url": src_url,
                "thumbnail": "", # Hard to get efficient cover from DOM without complex selectors
                "duration": 0, # Not easily available in DOM unless scraping duration span
                "uploader": "Douyin User",
                "extractor_key": "Douyin (DOM)"
            }
            
        except Exception as e:
            print(f"[Douyin] DOM err: {e}")
            return None
