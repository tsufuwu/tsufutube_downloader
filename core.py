# tsufutube/core.py
import os
import time
import glob
from datetime import datetime
import subprocess
import re
import shutil
import sys

# --- LAZY IMPORT WRAPPER ---
yt_dlp = None
instaloader = None
# from bilibili_api import BilibiliAPI (Moved to lazy load)
BilibiliAPI = None

def lazy_import_ytdlp():
    global yt_dlp
    if yt_dlp is None:
        try:
            import yt_dlp
            import yt_dlp.utils
        except ImportError as e:
            raise ImportError(f"Missing 'yt_dlp'. Run: pip install -U yt-dlp\nError: {e}")

def lazy_import_extras():
    global instaloader
    if instaloader is None:
        try:
            import instaloader
        except ImportError:
            pass

class DownloaderEngine:
    def __init__(self, ffmpeg_path):
        self.ffmpeg_path = ffmpeg_path
        self.is_cancelled = False
        self.last_update_time = 0
        
        self.temp_dir = os.path.join(os.getcwd(), "temp_downloads")
        
        # Ensure temp directory exists with robust error handling
        try:
            os.makedirs(self.temp_dir, exist_ok=True)
        except PermissionError:
            # Fallback to user temp directory if permission denied
            import tempfile
            self.temp_dir = os.path.join(tempfile.gettempdir(), "tsufutube_temp")
            os.makedirs(self.temp_dir, exist_ok=True)
        except Exception as e:
            print(f"Warning: Could not create temp directory: {e}")
            # Use current directory as last resort
            self.temp_dir = os.path.join(os.getcwd(), "temp")
            try:
                os.makedirs(self.temp_dir, exist_ok=True)
            except:
                pass  # If this also fails, operations will fail later with clear error
            
        self.temp_cookie_file = os.path.join(self.temp_dir, "browser_cookies.txt")


    # =========================================================================
    #  PHẦN 1: UTILS & FFmpeg
    # =========================================================================
    
    def get_duration(self, input_path):
        if not os.path.exists(self.ffmpeg_path): return 0
        try:
            cmd = [self.ffmpeg_path, '-i', input_path]
            creation_flags = subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
            result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding='utf-8', errors='ignore', creationflags=creation_flags)
            match = re.search(r"Duration:\s*(\d{2}):(\d{2}):(\d{2}\.\d+)", result.stderr)
            if match:
                h, m, s = map(float, match.groups())
                return h * 3600 + m * 60 + s
        except: pass
        return 0

    def execute_ffmpeg_cmd(self, cmd_args, duration=0, callback=None):
        if not os.path.exists(self.ffmpeg_path): return False, "FFmpeg not found"
        full_cmd = [self.ffmpeg_path] + cmd_args
        startupinfo = None
        if sys.platform == 'win32':
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        
        try:
            creation_flags = subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
            process = subprocess.Popen(
                full_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                universal_newlines=True, encoding='utf-8', errors='ignore',
                startupinfo=startupinfo, 
                creationflags=creation_flags
            )
            while True:
                line = process.stderr.readline()
                if not line and process.poll() is not None: break
                if line and duration > 0 and callback and "time=" in line:
                    match = re.search(r"time=(\d{2}):(\d{2}):(\d{2})", line)
                    if match:
                        h, m, s = map(int, match.groups())
                        percent = ((h * 3600 + m * 60 + s) / duration) * 100
                        callback(min(percent, 99))

            if process.returncode == 0:
                if callback: callback(100) 
                return True, "Success"
            else: return False, "FFmpeg Error"
        except Exception as e: return False, str(e)

    def cancel(self):
        self.is_cancelled = True

    # =========================================================================
    #  PHẦN 2: ROUTER & HELPERS
    # =========================================================================

    def _identify_platform(self, url):
        if not url: return "UNKNOWN"
        if "instagram.com" in url: return "INSTAGRAM"
        if "bilibili.com" in url: return "BILIBILI_CN"
        if "facebook.com" in url and ("stories" in url or "your_story" in url): return "FACEBOOK_STORY"
        return "GENERAL"
    
    def _auto_extract_cookies(self, browser_name, callbacks):
        if not browser_name or browser_name.lower() == "none": return None
        if os.path.exists(self.temp_cookie_file) and (time.time() - os.path.getmtime(self.temp_cookie_file)) < 1800:
            return self.temp_cookie_file

        callbacks.get('on_status', lambda x: None)(f"Trích xuất Cookies từ {browser_name}...")
        try:
            cmd = [sys.executable, "-m", "yt_dlp", "--cookies-from-browser", browser_name, "--cookies", self.temp_cookie_file, "--skip-download", "https://www.youtube.com", "--quiet"]
            subprocess.run(cmd, check=True, creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0)
            if os.path.exists(self.temp_cookie_file): return self.temp_cookie_file
        except: return None
        return None

    def fetch_info(self, url):
        platform = self._identify_platform(url)
        if platform in ["INSTAGRAM", "FACEBOOK_STORY"]:
            return {"title": f"[{platform}] Content", "extractor_key": platform}
        
        # [BILIBILI CN] Use Custom API for Info
        if platform == "BILIBILI_CN" and BilibiliAPI:
            match = re.search(r'(BV\w+)', url)
            if match:
                bvid = match.group(1)
                try:
                    # Initialize with NO COOKIE first to avoid slow file read, or read if efficient
                    client = BilibiliAPI(cookie_path=os.path.join(self.temp_dir, "browser_cookies.txt"))
                    info = client.get_video_info(bvid)
                    if info and info.get('code') == 0:
                        d = info['data']
                        return {
                            "title": d.get("title", f"Bilibili {bvid}"),
                            "uploader": d.get("owner", {}).get("name", "Bilibili User"),
                            "duration": d.get("duration", 0),
                            "thumbnail": d.get("pic", ""),
                            "webpage_url": f"https://www.bilibili.com/video/{bvid}",
                            "extractor_key": "Bilibili"
                        }
                except: pass

        lazy_import_ytdlp()
        ydl_opts = {'quiet': True, 'skip_download': True, 'noplaylist': True, 'ignoreerrors': True, 'socket_timeout': 30}
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl: 
                result = ydl.extract_info(url, download=False)
                return result, None
        except Exception as e:
            # Return None for result, and error string
            return None, str(e)

    def _classify_error(self, e):
        msg = str(e).lower()
        if "412" in msg: return "ERR_WBI", "Bilibili chặn (Lỗi 412). Vui lòng cập nhật Cookie."
        if any(k in msg for k in ["sign in", "confirm your age", "member-only", "private"]): return "ERR_LOGIN", "Video yêu cầu đăng nhập/Cookie."
        if "ffmpeg" in msg: return "ERR_SYSTEM", "Thiếu file ffmpeg.exe."
        return "ERR_UNKNOWN", f"Lỗi: {msg[:100]}..."

    # =========================================================================
    #  PHẦN 3: ENGINE LOGIC (ĐÃ SỬA LỖI BUG POSTPROCESSORS)
    # =========================================================================

    
    def extract_playlist_flat(self, url):
        lazy_import_ytdlp()
        ydl_opts = {
            'extract_flat': True, 
            'quiet': True, 
            'ignoreerrors': True,
            'skip_download': True
        }
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                return ydl.extract_info(url, download=False)
        except Exception as e:
            print(f"Playlist error: {e}")
            return None

    def download_single(self, task, settings, callbacks):
        self.is_cancelled = False
        
        # Auto Cookies
        browser_source = settings.get("browser_source", "none")
        if browser_source and browser_source != "none" and not settings.get("cookie_file"):
            auto_cookie = self._auto_extract_cookies(browser_source, callbacks)
            if auto_cookie: settings["cookie_file"] = auto_cookie
        
        platform = self._identify_platform(task["url"])
        if platform == "INSTAGRAM": return self._download_instagram(task, settings, callbacks)
        elif platform == "BILIBILI_CN":
            # [BILIBILI CN] Custom API Downloader (Fixed 412)
            global BilibiliAPI
            if BilibiliAPI is None:
                try: from bilibili_api import BilibiliAPI
                except ImportError: pass

            if BilibiliAPI:
                return self._download_bilibili(task, settings, callbacks)
            else:
                return False, "Thiếu module bilibili_api.py", None
        elif platform == "FACEBOOK_STORY": return self._download_facebook_story(task, settings, callbacks)
        
        return self._download_general_ytdlp(task, settings, callbacks)

    def _download_general_ytdlp(self, task, settings, callbacks, extra_opts=None):
        lazy_import_ytdlp()
        if not os.path.exists(self.ffmpeg_path): return False, "Thiếu file ffmpeg.exe", None

        # Prioritize Task Settings -> Global Settings
        save_path = task.get("save_path") or settings.get("save_path", ".")
        dtype = task.get("dtype", "video_1080")
        
        # --- [FIX-2] POSTPROCESSOR HOOKS (CUT PROGRESS) ---
        def pp_hook(d):
            if d['status'] == 'started':
                msg = f"Đang xử lý: {d.get('postprocessor', 'Unknown').replace('FFmpeg', '')}..."
                callbacks.get('on_status', lambda x:None)(msg)
                # [RESET BAR] Reset to 0% when entering post-processing (merging/cutting)
                callbacks.get('on_progress', lambda x,y:None)(0, msg)
        
        # Hooks Progress
        def progress_hook(d):
            if self.is_cancelled: raise yt_dlp.utils.DownloadError("Cancelled")
            if d['status'] == 'downloading':
                cur_time = time.time()
                if cur_time - self.last_update_time < 0.1: return
                self.last_update_time = cur_time
                total = d.get('total_bytes') or d.get('total_bytes_estimate')
                if total:
                    per = (d.get('downloaded_bytes', 0)/total)*100
                    callbacks.get('on_progress', lambda x,y:None)(per, f"{per:.1f}% | {d.get('eta', '?')}s")

        # --- CẤU HÌNH CƠ BẢN ---
        ydl_opts = {
            'progress_hooks': [progress_hook],
            'postprocessor_hooks': [pp_hook], # Báo status khi cắt/gộp
            'noplaylist': not task.get("is_plist"),
            'force_overwrites': True, # Ta sẽ quản lý tên file thủ công nên để True để yt-dlp ghi vào đích đã chọn
            'ignoreerrors': False,
            'ffmpeg_location': self.ffmpeg_path,
            'socket_timeout': 30,
            'addmetadata': settings.get("add_metadata", False),
            'writethumbnail': settings.get("embed_thumbnail", False),
            'geo_bypass': True,
            'live_from_start': True,
            # [REMOVED] sleep_interval settings were causing extra delays
        }
        
        # Geo / Proxy
        geo = settings.get("geo_bypass_country", "None")
        if geo and isinstance(geo, str) and geo != "None": ydl_opts['geo_bypass_country'] = geo
        
        proxy = settings.get("proxy_url")
        if proxy and isinstance(proxy, str) and proxy.strip(): ydl_opts['proxy'] = proxy.strip()

        # Archive
        if settings.get("use_archive", False):
            ydl_opts['download_archive'] = os.path.join(settings.get("config_path", "."), "archive.txt")

        # SponsorBlock
        sb_cats = []
        if settings.get("sb_sponsor"): sb_cats.append('sponsor')
        if settings.get("sb_intro"): sb_cats.append('intro')
        if settings.get("sb_outro"): sb_cats.append('outro')
        if settings.get("sb_selfpromo"): sb_cats.append('selfpromo')
        if settings.get("sb_interaction"): sb_cats.append('interaction')
        if settings.get("sb_music_offtopic"): sb_cats.append('music_offtopic')
        if settings.get("sb_preview"): sb_cats.append('preview')

        if sb_cats:
            ydl_opts.setdefault('postprocessors', []).append({
                'key': 'SponsorBlock',
                'categories': sb_cats,
                'when': 'after_filter', 
            })

        # Chapters
        if settings.get("split_chapters", False):
            ydl_opts['split_chapters'] = True
            ydl_opts.setdefault('postprocessors', []).append({'key': 'FFmpegSplitChapters', 'force_keyframes': False})
        elif settings.get("add_metadata", False):
            ydl_opts['embed_chapters'] = True

        # Cookie (Task -> Global)
        user_cookie = task.get("cookie_file") or settings.get("cookie_file", "")
        if user_cookie and os.path.exists(user_cookie): ydl_opts['cookiefile'] = user_cookie

        # Cut Mode
        if task.get("cut_mode"):
            ydl_opts['download_ranges'] = yt_dlp.utils.download_range_func(None, [(task.get("start_time", 0), task.get("end_time", float('inf')))])
            ydl_opts['force_keyframes_at_cuts'] = True

        # Config Format
        self._configure_format(ydl_opts, dtype, task.get("subs", []), task.get("download_sub", False), settings)

        try:
            # --- [FIX-1] UNIQUE FILENAME LOGIC ---
            # 1. Peek Info (Không tải)
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(task["url"], download=False)
            
            if not info: return False, "Không lấy được info", None

            # 2. Tính toán tên file đích
            # Ưu tiên Name người dùng nhập -> Title
            base_name = task.get("name", "") if task.get("name") else info.get('title', 'video')
            if task.get("cut_mode"): base_name += " (Cut)"
            
            # Xác định Extension dự kiến
            final_ext = info.get('ext', 'mp4')
            # Nếu có merge_output_format (do user chọn video ext), dùng nó làm ext chuẩn check trùng
            if 'merge_output_format' in ydl_opts:
                final_ext = ydl_opts['merge_output_format']
            elif dtype == "audio_mp3": final_ext = "mp3"
            elif dtype == "audio_lossless": final_ext = settings.get("default_audio_ext", "flac")
            
            # 3. Check trùng lặp và tạo tên mới (1), (2)...
            def get_unique_name(directory, filename, ext):
                counter = 1
                new_filename = filename
                while True:
                    # Check cả file
                    cand_path = os.path.join(directory, f"{new_filename}.{ext}")
                    if not os.path.exists(cand_path):
                        return new_filename
                    new_filename = f"{filename} ({counter})"
                    counter += 1
            
            unique_base_name = get_unique_name(save_path, base_name, final_ext)
            
            # 4. Gán lại vào outtmpl để yt-dlp dùng tên này
            ydl_opts['outtmpl'] = os.path.join(save_path, f'{unique_base_name}.%(ext)s')
            
            # --- [FIX-3] REAL-TIME CUT PROGRESS LOGGER ---
            if task.get("cut_mode"):
                start_s = task.get("start_time", 0)
                end_s = task.get("end_time", float('inf'))
                real_dur = info.get('duration', 0)
                
                # Cap end_time at actual duration if needed
                if end_s == float('inf') or (real_dur > 0 and end_s > real_dur):
                    end_s = real_dur if real_dur > 0 else end_s
                
                total_cut_duration = end_s - start_s
                
                if total_cut_duration > 0:
                    class YtDlpLogger:
                        def debug(self, msg):
                            # Parse ffmpeg output: time=00:00:13.18
                            if "time=" in msg:
                                match = re.search(r'time=(\d{2}):(\d{2}):(\d{2}\.\d+)', msg)
                                if match:
                                    h, m, s = map(float, match.groups())
                                    cur_seconds = h*3600 + m*60 + s
                                    # Elapsed time in ffmpeg cut is relative to the output file (starts at 0)
                                    percent = (cur_seconds / total_cut_duration) * 100
                                    if percent > 99: percent = 99 # Keep 100 for final success
                                    callbacks.get('on_progress', lambda x,y:None)(percent, f"Cutting... {percent:.1f}%")
                        def warning(self, msg): pass
                        def error(self, msg): print(f"YtDlp Error: {msg}")
                    
                    ydl_opts['logger'] = YtDlpLogger()

            # 5. Tải thật
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # Lưu ý: Pass 'info' dict vào process_ie_result để bypass extraction
                # Điều này giúp skip qua bước "Downloading webpage..." và "Solving JS challenges..." lần 2
                info = ydl.process_ie_result(ie_result=info, download=True)
                final_path = self._get_final_path(ydl, info)
                
                # Logic Convert Sub (nếu sub_only)
                if dtype == "sub_only":
                    final_path = self._handle_sub_conversion(final_path, task.get("sub_format", "srt"), callbacks)

                # History Item
                history_item = None
                if final_path and os.path.exists(final_path):
                    size_mb = os.path.getsize(final_path) / (1024 * 1024)
                    history_item = {
                        "platform": info.get('extractor_key', 'Web'),
                        "title": unique_base_name, # Dùng tên đã unique
                        "path": final_path,
                        "format": os.path.splitext(final_path)[1].replace(".", "").upper(),
                        "size": f"{size_mb:.2f} MB",
                        "date": datetime.now().strftime("%Y-%m-%d %H:%M")
                    }
                return True, "Success", history_item

        except Exception as e:
            if self.is_cancelled: return False, "Đã hủy", None
            err_type, friendly_msg = self._classify_error(e)
            return False, friendly_msg, None

    def _configure_format(self, opts, dtype, subs, dl_sub, settings):
        if dtype == "sub_only":
            opts.update({'skip_download': True, 'writesubtitles': True, 'subtitleslangs': subs if subs else ['all'], 'writethumbnail': False})
        elif "audio" in dtype:
            if dtype == "audio_opus": target = "opus"
            elif dtype == "audio_mp3": target = "mp3"
            elif dtype == "audio_lossless": target = settings.get("default_audio_ext", "flac")
            else: target = "m4a" # Default for AAC

            opts['format'] = 'bestaudio/best'
            # FIX LỖI: Dùng setdefault và append thay vì update (tránh xóa mất SponsorBlock/SplitChapters)
            opts.setdefault('postprocessors', []).append({
                'key': 'FFmpegExtractAudio',
                'preferredcodec': target
            })
        else: # Video
            # Parse limits based on dtype which contains strings like "video_720", "video_480" etc.
            limit = 1080 # Default
            if "4k" in dtype: limit = 2160
            elif "2k" in dtype: limit = 1440
            elif "1080" in dtype: limit = 1080
            elif "720" in dtype: limit = 720
            elif "480" in dtype: limit = 480
            elif "360" in dtype: limit = 360
            elif "240" in dtype: limit = 240
            elif "144" in dtype: limit = 144

            ext = settings.get("default_video_ext", "mp4")
            
            # [FIX CODEC] Priority Logic
            codec_pref = settings.get("video_codec_priority", "auto")
            
            # Base format string
            if codec_pref == "h264":
                # Prioritize H.264 (avc1) and AAC (mp4a)
                # Fallback to any best video if h264 not present (rare) but safest strictly is:
                # bestvideo[height<=...][vcodec^=avc]+bestaudio[acodec^=mp4a]
                fmt_str = f"bestvideo[height<={limit}][vcodec^=avc]+bestaudio[acodec^=mp4a] / bestvideo[height<={limit}][vcodec^=avc]+bestaudio / best[height<={limit}][vcodec^=avc] / bestvideo[height<={limit}]+bestaudio"
            elif codec_pref == "av1":
                # Prioritize AV1 (av01)
                fmt_str = f"bestvideo[height<={limit}][vcodec^=av01]+bestaudio / bestvideo[height<={limit}]+bestaudio"
            else:
                # Auto
                fmt_str = f"bestvideo[height<={limit}]+bestaudio / best"

            opts.update({'format': fmt_str, 'merge_output_format': ext})
            if dl_sub:
                opts.update({'writesubtitles': True, 'subtitleslangs': subs if subs else ['all']})
                if ext in ["mkv", "mp4"]: opts['embedsub'] = True

    def _get_final_path(self, ydl, info):
        if 'requested_downloads' in info: return info['requested_downloads'][0].get('filepath')
        return ydl.prepare_filename(info)

    def _handle_sub_conversion(self, path, fmt, callbacks):
        if not path: return None
        base = os.path.splitext(os.path.basename(path))[0]
        d = os.path.dirname(path) or "."
        candidates = glob.glob(os.path.join(d, f"{base}*"))
        subs = [f for f in candidates if not f.endswith(('.mp4','.mkv','.webm','.mp3'))]
        if not subs: return path
        best_sub = max(subs, key=os.path.getctime)
        if best_sub.endswith(f".{fmt}"): return best_sub
        callbacks.get('on_status', lambda x:None)(f"Đổi đuôi sub sang .{fmt}...")
        new_path = os.path.splitext(best_sub)[0] + f".{fmt}"
        self.convert_subtitle(best_sub, new_path)
        try: os.remove(best_sub)
        except: pass
        return new_path

    # --- OTHER PLATFORM DOWNLOADERS ---
    def _download_instagram(self, task, settings, callbacks):
        lazy_import_extras()
        if not instaloader: return False, "Thiếu instaloader", None
        try:
            L = instaloader.Instaloader(dirname_pattern=self.temp_dir, save_metadata=False, download_video_thumbnails=False)
            if settings.get("ig_user") and settings.get("ig_pass"):
                try: L.login(settings.get("ig_user"), settings.get("ig_pass"))
                except: pass
            url = task["url"]
            shortcode = url.split("/reel/")[-1].split("/")[0] if "/reel/" in url else url.split("/p/")[-1].split("/")[0]
            if not shortcode: return False, "Link lỗi", None
            callbacks.get('on_status', lambda x:None)("Instagram Downloading...")
            post = instaloader.Post.from_shortcode(L.context, shortcode)
            L.download_post(post, target=shortcode)
            target_dir = os.path.join(self.temp_dir, shortcode)
            vids = glob.glob(os.path.join(target_dir, "*.mp4"))
            if vids:
                final = max(vids, key=os.path.getctime)
                dest = os.path.join(settings.get("save_path", "."), f"{task.get('name', f'Insta_{shortcode}')}.mp4")
                shutil.move(final, dest)
                try: shutil.rmtree(target_dir)
                except: pass
                return True, "Success", {"path": dest, "format": "MP4", "platform": "Instagram", "size": "N/A"}
            return False, "Không thấy video", None
        except Exception as e: return False, str(e), None

    def _download_facebook_story(self, task, settings, callbacks):
        return False, "Chưa hỗ trợ FB Story", None

    # =========================================================================
    #  PHẦN 4: CUSTOM BILIBILI HANDLER
    # =========================================================================
    def _download_bilibili(self, task, settings, callbacks):
        url = task["url"]
        callbacks.get('on_status', lambda x: None)("Đang kết nối Bilibili API...")
        
        # Regex BVID
        match = re.search(r'(BV\w+)', url)
        if not match: return False, "Link không hợp lệ (Thiếu BV ID)", None
        bvid = match.group(1)
        video_referer = f"https://www.bilibili.com/video/{bvid}"
        
        try:
            client = BilibiliAPI(cookie_path=settings.get("cookie_file"))
            
            # 1. Get Info
            info = client.get_video_info(bvid)
            if not info: return False, "Lỗi mạng hoặc API change", None
            if info.get('code') != 0:
                return False, f"Lỗi lấy thông tin (Code {info.get('code')}): {info.get('message')}", None
                
            v_data = info['data']
            title = v_data['title']
            cid = v_data['cid']
            duration = v_data['duration']
            
            # 2. Get Play URL
            callbacks.get('on_status', lambda x: None)("Đang lấy link tải (WBI Signed)...")
            play = client.get_play_url(bvid, cid, qn=80) # 1080p target
            
            if not play or play.get('code') != 0:
                 return False, f"Lỗi lấy playurl (Code {play.get('code') if play else 'None'}): {play.get('message') if play else 'Unknown'}", None
            
            dash = play['data'].get('dash')
            if not dash: return False, "Không tìm thấy luồng DASH (Cần Video+Audio). Có thể cần Cookie.", None
            
            # Select best video/audio
            video_url = dash['video'][0]['baseUrl']
            audio_url = dash['audio'][0]['baseUrl']
            
            # 3. Download
            save_path = settings.get("save_path", ".")
            safe_title = "".join([c for c in title if c.isalpha() or c.isdigit() or c==' ']).strip()
            
            # Determine Output Type
            dtype = task.get("dtype", "video_1080")
            is_audio_only = "audio" in dtype
            
            # Extensions
            if is_audio_only:
                if "mp3" in dtype: target_ext = "mp3"
                elif "m4a" in dtype: target_ext = "m4a" 
                elif "wav" in dtype: target_ext = "wav"
                elif "lossless" in dtype or "flac" in dtype: target_ext = "flac"
                else: target_ext = settings.get("default_audio_ext", "mp3")
                final_ext = target_ext
            else:
                final_ext = "mp4" # Force mp4 for video merge

            # Unique Name
            base_name = f"{safe_title} [Bilibili]"
            counter = 1
            while os.path.exists(os.path.join(save_path, f"{base_name}.{final_ext}")):
                 base_name = f"{safe_title} [Bilibili] ({counter})"
                 counter += 1
            
            final_path = os.path.join(save_path, f"{base_name}.{final_ext}")
            
            # Temppaths
            v_tmp = os.path.join(self.temp_dir, "bili_vid.m4s")
            a_tmp = os.path.join(self.temp_dir, "bili_aud.m4s")
            
            def report_progress(curr, total, label):
                 per = (curr/total)*100
                 callbacks.get('on_progress', lambda x,y:None)(per, f"{label}: {per:.1f}%")

            if is_audio_only:
                # --- AUDIO MODE ---
                callbacks.get('on_status', lambda x: None)("Đang tải Audio track...")
                if not client.download_file(audio_url, a_tmp, video_referer, lambda c,t: report_progress(c,t,"Audio")):
                     return False, "Lỗi tải Audio track", None
                
                callbacks.get('on_status', lambda x: None)(f"Đang convert sang {final_ext.upper()}...")
                
                # Convert using existing tool helper or raw command
                self.extract_audio(a_tmp, final_path, format=final_ext, bitrate="192k")
                
                if os.path.exists(a_tmp): os.remove(a_tmp)
                
                return True, "Thành công", {
                    "platform": "Bilibili", "title": base_name, "path": final_path,
                    "format": final_ext.upper(), "size": "Unknown", "date": datetime.now().strftime("%Y-%m-%d %H:%M")
                }
            
            else:
                # --- VIDEO MODE ---
                # DL Video (Pass referer)
                callbacks.get('on_status', lambda x: None)("Đang tải Video track...")
                if not client.download_file(video_url, v_tmp, video_referer, lambda c,t: report_progress(c,t,"Video")):
                     return False, "Lỗi tải Video track (403/412?). Update Cookie.", None
                
                # DL Audio (Pass referer)
                callbacks.get('on_status', lambda x: None)("Đang tải Audio track...")
                if not client.download_file(audio_url, a_tmp, video_referer, lambda c,t: report_progress(c,t,"Audio")):
                     return False, "Lỗi tải Audio track", None
                
                # Merge
                callbacks.get('on_status', lambda x: None)("Đang ghép file (FFmpeg)...")
                cmd = [
                    self.ffmpeg_path, "-y",
                    "-i", v_tmp, "-i", a_tmp,
                    "-c:v", "copy", "-c:a", "aac",
                    final_path
                ]
                subprocess.run(cmd, check=True, creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0)
                
                # Cleanup
                if os.path.exists(v_tmp): os.remove(v_tmp)
                if os.path.exists(a_tmp): os.remove(a_tmp)
                
                return True, "Thành công", {
                    "platform": "Bilibili", "title": base_name, "path": final_path,
                    "format": "MP4", "size": "Unknown", "date": datetime.now().strftime("%Y-%m-%d %H:%M")
                }

        except Exception as e:
            return False, f"Lỗi Bilibili: {str(e)}", None

    def _download_facebook_story(self, task, settings, callbacks):
        if not settings.get("cookie_file"): return False, "FB Story cần Cookie", None
        return self._download_general_ytdlp(task, settings, callbacks)

    # --- TOOLS (FFMPEG WRAPPERS) ---
    def change_video_format(self, i, o, duration=0, callback=None):
        return self.execute_ffmpeg_cmd(['-i', i, '-c:v', 'libx264', '-preset', 'fast', '-crf', '23', '-c:a', 'aac', o, '-y'], duration, callback)
    def compress_video(self, i, o, crf=28, duration=0, callback=None):
        return self.execute_ffmpeg_cmd(['-i', i, '-vcodec', 'libx264', '-crf', str(crf), '-preset', 'fast', o, '-y'], duration, callback)
    def extract_audio(self, i, o, format="mp3", bitrate="192k", duration=0, callback=None):
        cmd = ['-i', i, '-vn']
        if format=="mp3": cmd.extend(['-acodec', 'libmp3lame', '-b:a', bitrate])
        elif format=="copy": cmd.extend(['-acodec', 'copy'])
        else: cmd.extend(['-acodec', 'aac'])
        return self.execute_ffmpeg_cmd(cmd + [o, '-y'], duration, callback)
    def fast_cut(self, i, o, s, e, duration=0, callback=None):
        # -ss before -i for fast seek, -to after -i for accurate end
        return self.execute_ffmpeg_cmd(['-ss', s, '-i', i, '-to', e, '-c', 'copy', '-avoid_negative_ts', 'make_zero', o, '-y'], duration, callback)
    def convert_subtitle(self, i, o): return self.execute_ffmpeg_cmd(['-i', i, o, '-y'])
    def fix_rotation(self, i, o, rot="90"):
        vf = "transpose=1" # 90 Clockwise
        r = str(rot)
        if r == "270": vf = "transpose=2" # 90 CCW
        elif r == "180": vf = "transpose=1,transpose=1"
        return self.execute_ffmpeg_cmd(['-i', i, '-vf', vf, '-c:v', 'libx264', '-preset', 'fast', '-c:a', 'copy', o, '-y'])
    def normalize_audio(self, i, o): return self.execute_ffmpeg_cmd(['-i', i, '-c:v', 'copy', '-af', "loudnorm=I=-14:TP=-1.5:LRA=11", o, '-y'])
    def remove_audio(self, i, o): return self.execute_ffmpeg_cmd(['-i', i, '-c:v', 'copy', '-an', o, '-y'])
    def embed_subtitle(self, v, s, o): return self.execute_ffmpeg_cmd(['-i', v, '-i', s, '-c', 'copy', '-c:s', 'mov_text', o, '-y'])
    def burn_subtitle(self, v, s, o):
        escaped_s = s.replace(':', '\\:')
        return self.execute_ffmpeg_cmd(['-i', v, '-vf', f"subtitles='{escaped_s}'", '-c:v', 'libx264', o, '-y'])
    def embed_cover(self, m, i, o): return self.execute_ffmpeg_cmd(['-i', m, '-i', i, '-map', '0', '-map', '1', '-c', 'copy', '-disposition:v:1', 'attached_pic', o, '-y'])
    def video_to_gif(self, i, o): return self.execute_ffmpeg_cmd(['-i', i, '-vf', "fps=15,scale=480:-1:flags=lanczos", '-c:v', 'gif', o, '-y'])
    def video_to_gif_range(self, i, o, start, end): 
        return self.execute_ffmpeg_cmd(['-ss', start, '-to', end, '-i', i, '-vf', "fps=15,scale=480:-1:flags=lanczos", '-c:v', 'gif', o, '-y'])
    def gif_to_video(self, i, o): 
        return self.execute_ffmpeg_cmd(['-i', i, '-movflags', 'faststart', '-pix_fmt', 'yuv420p', '-vf', "scale=trunc(iw/2)*2:trunc(ih/2)*2", o, '-y'])