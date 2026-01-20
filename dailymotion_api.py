import requests
import re
import json

class DailymotionDownloader:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
             'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
             'Referer': 'https://www.dailymotion.com/'
        })

    def get_video_info(self, url):
        """
        Extract video info using Dailymotion Metadata API.
        Returns: (info_dict, error_string)
        """
        try:
            # 1. Extract ID
            video_id = self._extract_id(url)
            if not video_id:
                return None, "Invalid Dailymotion URL (ID not found)"

            # 2. Call API
            api_url = f"https://www.dailymotion.com/player/metadata/video/{video_id}"
            res = self.session.get(api_url, timeout=10)
            
            if res.status_code != 200:
                return None, f"API Error {res.status_code}"
                
            data = res.json()
            
            # 3. Parse Data
            title = data.get('title', f"Dailymotion {video_id}")
            poster = data.get('posters', {}).get('600', '')
            duration = data.get('duration', 0)
            owner = data.get('owner', {}).get('screenname', 'Dailymotion User')
            
            qualities = data.get('qualities', {})
            m3u8_url = None
            
            # Prefer 'auto'
            if 'auto' in qualities:
                m3u8_url = qualities['auto'][0].get('url')
            else:
                # Fallback to any valid stream
                for q in qualities.values():
                    if q and isinstance(q, list) and q[0].get('url'):
                        m3u8_url = q[0]['url']
                        break
            
            if not m3u8_url:
                return None, "No video stream found in metadata"
                
            return {
                "id": video_id,
                "title": title,
                "url": m3u8_url,
                "thumbnail": poster,
                "duration": duration,
                "uploader": owner,
                "extractor_key": "Dailymotion (API)",
                "protocol": "m3u8"
            }, None

        except Exception as e:
            return None, f"Dailymotion API Exception: {str(e)}"

    def _extract_id(self, url):
        # Support various formats:
        # https://www.dailymotion.com/video/x9y5x54
        # https://dai.ly/x9y5x54
        # https://www.dailymotion.com/embed/video/x9y5x54
        patterns = [
            r'video/([a-z0-9]+)',
            r'dai\.ly/([a-z0-9]+)',
            r'embed/video/([a-z0-9]+)'
        ]
        
        for p in patterns:
            match = re.search(p, url)
            if match: return match.group(1)
            
        return None
