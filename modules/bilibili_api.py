import hashlib
import urllib.request
import urllib.parse
import urllib.error
import json
import time
import os
import re
from functools import reduce

class BilibiliAPI:
    def __init__(self, cookie_path=None):
        self.user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        self.cookies = {}
        if cookie_path and os.path.exists(cookie_path):
            self.load_cookies(cookie_path)
            
    def load_cookies(self, path):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
                for line in content.splitlines():
                    if line.startswith('#') or not line.strip(): continue
                    parts = line.split('\t')
                    if len(parts) >= 7:
                        self.cookies[parts[5]] = parts[6]
        except: pass

    def _get_headers(self, referer=None):
        h = {
            'User-Agent': self.user_agent,
            'Referer': referer if referer else 'https://www.bilibili.com/',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.9',
        }
        if self.cookies:
            h['Cookie'] = '; '.join([f"{k}={v}" for k, v in self.cookies.items()])
        return h

    def _request(self, url, params=None, referer=None):
        if params:
            url += '?' + urllib.parse.urlencode(params)
        
        req = urllib.request.Request(url, headers=self._get_headers(referer))
        try:
            with urllib.request.urlopen(req, timeout=15) as response:
                return json.loads(response.read().decode('utf-8'))
        except urllib.error.HTTPError as e:
            try:
                body = e.read().decode('utf-8')
                return json.loads(body)
            except:
                return {'code': e.code, 'message': f"HTTP {e.code}"}
        except Exception as e:
            return {'code': -1, 'message': str(e)}

    # --- WBI SIGNING ALGORITHM ---
    def get_mixin_key(self, orig):
        mixinKeyEncTab = [
            46, 47, 18, 2, 53, 8, 23, 32, 15, 50, 10, 31, 58, 3, 45, 35, 27, 43, 5, 49,
            33, 9, 42, 19, 29, 28, 14, 39, 12, 38, 41, 13, 37, 48, 7, 16, 24, 55, 40,
            61, 26, 17, 0, 1, 60, 51, 30, 4, 22, 25, 54, 21, 56, 59, 6, 63, 57, 62, 11,
            36, 20, 34, 44, 52
        ]
        return reduce(lambda s, i: s + orig[i], mixinKeyEncTab, '')[:32]

    def enc_wbi(self, params: dict, img_key: str, sub_key: str):
        mixin_key = self.get_mixin_key(img_key + sub_key)
        curr_time = round(time.time())
        params['wts'] = curr_time
        params = dict(sorted(params.items()))
        # Filter invalid chars
        params = {k: ''.join(filter(lambda c: c not in "!'()*", str(v))) for k, v in params.items()}
        query = urllib.parse.urlencode(params)
        wbi_sign = hashlib.md5((query + mixin_key).encode()).hexdigest()
        params['w_rid'] = wbi_sign
        return params

    def get_wbi_keys(self):
        # customized request to allow ignoring cookies
        def fetch_nav(use_cookie=True):
            headers = self._get_headers()
            if not use_cookie:
                headers.pop('Cookie', None)
            
            try:
                req = urllib.request.Request('https://api.bilibili.com/x/web-interface/nav', headers=headers)
                with urllib.request.urlopen(req, timeout=10) as response:
                    return json.loads(response.read().decode('utf-8'))
            except: return None

        resp = fetch_nav(True)
        # If failed with cookies (e.g. -101 or expired), try without cookies
        if not resp or resp.get('code') != 0:
            print(f"WBI Nav with cookie failed: {resp.get('code') if resp else 'NetErr'}. Retrying no-cookie.")
            resp = fetch_nav(False)

        if not resp: 
            print(f"WBI Nav final fail: {resp}")
            return None, None
            
        # [FIX] Even if code is -101 (Not logged in), data often contains wbi_img
        wbi_img = resp.get('data', {}).get('wbi_img', {})
        img_url = wbi_img.get('img_url', '')
        sub_url = wbi_img.get('sub_url', '')
        
        if not img_url or not sub_url: 
            print(f"No WBI keys found in response: {resp}")
            return None, None
            
        img_key = img_url.split('/')[-1].split('.')[0]
        sub_key = sub_url.split('/')[-1].split('.')[0]
        return img_key, sub_key

    def get_video_info(self, bvid):
        # View API also needs WBI in some regions, but usually safe
        # Referer must be video link
        return self._request('https://api.bilibili.com/x/web-interface/view', {'bvid': bvid}, referer=f'https://www.bilibili.com/video/{bvid}')

    def get_play_url(self, bvid, cid, qn=80):
        img_key, sub_key = self.get_wbi_keys()
        if not img_key: return {'code': -999, 'message': 'Failed to get WBI keys'}
        
        params = {
            'bvid': bvid,
            'cid': cid,
            'qn': qn,
            'fnval': 4048, # Try 4048 for force DASH
            'fnver': 0,
            'fourk': 1,
            'platform': 'web',      # IMPORTANT for matching browser behavior
            'web_location': 1315873 # Common web location ID
        }
        signed_params = self.enc_wbi(params, img_key, sub_key)
        return self._request('https://api.bilibili.com/x/player/wbi/playurl', signed_params, referer=f'https://www.bilibili.com/video/{bvid}')
        
    def download_file(self, url, dest_path, referer, progress_callback=None):
        try:
            req = urllib.request.Request(url, headers=self._get_headers(referer))
            with urllib.request.urlopen(req, timeout=30) as u, open(dest_path, 'wb') as f:
                meta = u.info()
                file_size = int(meta.get("Content-Length", 0))
                downloaded = 0
                block_sz = 8192
                while True:
                    buffer = u.read(block_sz)
                    if not buffer: break
                    downloaded += len(buffer)
                    f.write(buffer)
                    if progress_callback and file_size:
                        progress_callback(downloaded, file_size)
            return True
        except Exception as e:
            print(f"DL Error: {e}")
            return False
