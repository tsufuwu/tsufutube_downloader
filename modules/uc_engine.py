# -*- coding: utf-8 -*-
"""
Undetected Chromedriver Engine - Last Resort Fallback
Uses undetected-chromedriver to bypass strict anti-bot measures.
"""
import time
import os
import shutil

class UndetectedChromeEngine:
    def __init__(self, headless=True):
        self.headless = headless
        self.driver = None

    def sniff_video(self, url, timeout=60):
        """
        Attempt to extract video using undetected-chromedriver.
        Captures performance logs or searches DOM.
        """
        try:
            import undetected_chromedriver as uc
            from selenium.webdriver.common.by import By
        except ImportError:
            return {"error": "MODULE_MISSING", "message": "undetected-chromedriver not installed"}

        try:
            options = uc.ChromeOptions()
            if self.headless:
                options.add_argument('--headless=new')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            
            # Enable logging for network capture (optional, UC makes this tricky sometimes)
            # options.set_capability('goog:loggingPrefs', {'performance': 'ALL'})

            print("[UC] Starting Undetected Chrome...")
            self.driver = uc.Chrome(options=options, use_subprocess=True)
            
            print(f"[UC] Navigating to {url}...")
            self.driver.get(url)
            
            # Smart wait
            time.sleep(5)
            
            # 1. Try DOM Video Tag
            video_url = self._extract_from_dom()
            if video_url:
                print(f"[UC] Found in DOM: {video_url[:50]}...")
                return {"url": video_url, "ext": "mp4", "extractor": "UC_DOM"}

            # 2. Try scrolling
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight/2);")
            time.sleep(3)
            
            video_url = self._extract_from_dom()
            if video_url:
                return {"url": video_url, "ext": "mp4", "extractor": "UC_DOM_SCROLL"}

            return None

        except Exception as e:
            print(f"[UC] Error: {e}")
            return {"error": "UC_ERROR", "message": str(e)}
        finally:
            if self.driver:
                try: 
                    self.driver.quit()
                except: pass

    def _extract_from_dom(self):
        try:
            from selenium.webdriver.common.by import By
            
            # Check <video> src
            videos = self.driver.find_elements(By.TAG_NAME, "video")
            for v in videos:
                src = v.get_attribute("src")
                if src and "blob:" not in src:
                    return src
                # Check <source> children
                sources = v.find_elements(By.TAG_NAME, "source")
                for s in sources:
                    src = s.get_attribute("src")
                    if src and "blob:" not in src:
                        return src
            
            # Check for common m3u8 in page source
            page_source = self.driver.page_source
            if ".m3u8" in page_source:
                import re
                match = re.search(r'(https?://[^"\']+\.m3u8[^"\']*)', page_source)
                if match:
                    return match.group(1)
                    
            return None
        except:
            return None
