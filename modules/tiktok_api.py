import requests
import json
import time

class TikTokDownloader:
    def __init__(self):
        self.api_url = "https://www.tikwm.com/api/"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/json",
        }

    def get_video_info(self, url):
        """
        Fetch TikTok video info using public API (SnapTik-like approach).
        Returns (info_dict, error_message).
        """
        try:
            # Method 1: POST
            params = {"url": url, "count": 12, "cursor": 0, "web": 1, "hd": 1}
            try:
                response = requests.post(self.api_url, data=params, headers=self.headers, timeout=15)
                data = response.json()
            except:
                data = {"code": -1}

            # Method 2: GET Fallback
            if data.get("code") != 0:
                print("[TikTokAPI] POST failed, trying GET...")
                try:
                    query = f"{self.api_url}?url={url}&hd=1"
                    response = requests.get(query, headers=self.headers, timeout=15)
                    data = response.json()
                except Exception as e:
                    return None, f"API Request Failed: {e}"
            
            if data.get("code") != 0:
                msg = data.get("msg", "Unknown error")
                return None, f"API Error: {msg}"
            
            video_data = data.get("data", {})
            
            # Construct standard info dict
            info = {
                "id": video_data.get("id", ""),
                "title": video_data.get("title", "TikTok Video"),
                "url": video_data.get("play", ""), # Watermark-free link
                "thumbnail": video_data.get("cover", ""),
                "duration": video_data.get("duration", 0),
                "author": video_data.get("author", {}).get("nickname", ""),
                "extractor_key": "TikTok",
                "ext": "mp4"
            }
            
            # Prefer HD link if available
            if video_data.get("hdplay"):
                info["url"] = video_data.get("hdplay")
                
            return info, None

        except Exception as e:
            return None, str(e)
