import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import os
import sys
import time
import re
import ctypes
import webbrowser
import json
import urllib.request
from datetime import datetime
from io import BytesIO

# Try importing PIL for images
HAS_PIL = False
try:
    from PIL import Image, ImageTk
    HAS_PIL = True
except ImportError:
    pass

# --- CONFIG & CONSTANTS ---
APP_TITLE = "Tsufutube Downloader Pro"
APP_SLOGAN = "All-in-One Media Solution"
VERSION = "v1.0"
REPO_API_URL = "https://api.github.com/repos/tsufuwu/tsufutube_downloader/releases/latest"

# --- TRANSLATIONS ---
TRANSLATIONS = {
    "vi": {
        "tab_home": "Trang Chủ",
        "tab_history": "Lịch sử Download", # Renamed
        "tab_settings": "Cài đặt",
        "info_source": " Thông tin nguồn ",
        "lbl_link": "Link Video/Nhạc:",
        "btn_paste": "📋 Dán",
        "chk_auto_paste": "Tự động dán Link",
        "btn_check": "🔍 Kiểm tra",
        "btn_cancel_check": "✖ Hủy lấy tin",
        "lbl_loading": "Đang tải thông tin...",
        "lbl_filename": "Đặt tên file:",
        "lbl_filename_note": "(Để trống = Tên gốc)",
        "lbl_save_at": "Lưu tại:",
        "btn_browse": "...",
        "btn_open": "Mở",
        "grp_cut": " Bộ công cụ Cắt (Cut) ",
        "chk_enable_cut": "Kích hoạt chế độ Cắt",
        "lbl_time_fmt": "(Nhập dạng MM:SS hoặc HH:MM:SS)",
        "lbl_start": "Bắt đầu:",
        "chk_from_start": "Từ đầu",
        "lbl_end": "Kết thúc:",
        "chk_to_end": "Đến hết",
        "grp_opts": " Định dạng & Tùy chọn ",
        "lbl_format_title": "Chọn định dạng:",
        "opt_audio_aac": "Audio AAC (M4A)",
        "opt_audio_mp3": "Audio MP3",
        "opt_video_4k": "Video 4K (2160p)",
        "opt_video_2k": "Video 2K (1440p)",
        "opt_video_1080": "Video Full HD (1080p)",
        "lbl_advanced": "Chức năng nâng cao:",
        "chk_keep_audio": "Giữ file Audio gốc",
        "chk_keep_video": "Giữ file Video gốc",
        "chk_sub": "Tải Phụ đề (Chọn ngôn ngữ...)",
        "chk_sub_count": "Tải Phụ đề (Đã chọn {})",
        "chk_playlist": "Tải toàn bộ Playlist/Album",
        "chk_open_done": "Tự động mở file khi tải xong",
        "lbl_cookies": "Cookies (Dùng khi bị lỗi/chặn):",
        "btn_cookies": "Chọn File .txt",
        "btn_guide": "Hướng dẫn & Cookies",
        "lbl_queue": "Danh sách hàng đợi:",
        "col_title": "Tên Video / File",
        "col_link": "Đường dẫn (Link)",
        "btn_add_queue": "➕ Thêm vào hàng đợi",
        "btn_del_queue": "❌ Xóa dòng chọn",
        "lbl_ready": "Đang chờ lệnh...",
        "lbl_paste_hint": "Hãy dán link (YouTube, FB, Insta, TwitCasting...) vào ô trên...",
        "btn_download": "TẢI VỀ NGAY",
        "btn_cancel": "✖ HỦY BỎ",
        "set_title": "Cài đặt hệ thống",
        "set_lang": "Ngôn ngữ (Language):",
        "set_theme": "Giao diện (Theme):",
        "set_bg": "Hình nền (Background):",
        "btn_img_browse": "Chọn ảnh...",
        "btn_img_clear": "Xóa ảnh",
        "chk_tray": "Ẩn xuống khay hệ thống khi đóng (Minimize to Tray)",
        "btn_update": "⟳ Kiểm tra phiên bản mới",
        "btn_save": "Lưu & Áp dụng",
        "msg_saved": "Đã lưu cài đặt!",
        "err_no_link": "Vui lòng nhập link trước!",
        "err_no_ffmpeg": "Thiếu file ffmpeg.exe",
        "status_playlist": "Phát hiện Playlist!",
        "status_ready": "Đã sẵn sàng tải xuống",
        "status_downloading": "Đang tải xuống...",
        "status_processing": "Đang xử lý (Mux/Convert)...",
        "status_done": "Hoàn tất!",
        "status_cancel": "Đã hủy",
        "opt_audio_lossless": "Audio Lossless (FLAC/WAV)",
        "grp_fmt_setting": " Cấu hình Định dạng (FFmpeg) ",
        "lbl_video_ext": "Container Video mặc định:",
        "lbl_audio_ext": "Định dạng Audio mặc định:",
        "lbl_video_codec": "Ưu tiên Codec Video:",
        "val_codec_auto": "Tự động (Tốt nhất)",
        "val_codec_h264": "H.264 (Tương thích cao)",
        "val_codec_av1": "AV1/VP9 (Nét hơn/Nhẹ hơn)",
        "chk_metadata": "Ghi Metadata (Tên, Artist, Album) vào file",
        "chk_thumbnail": "Embed Thumbnail (Ảnh bìa) vào file",
        # History Tab Updates
        "col_check": "Chọn",
        "col_platform": "Nền tảng",
        "col_size": "Dung lượng",
        "col_date": "Ngày tải",
        "ctx_open_file": "Mở File",
        "ctx_open_folder": "Mở Thư mục chứa",
        "ctx_delete": "Xóa...",
        "msg_del_title": "Xác nhận xóa",
        "msg_del_confirm": "Bạn muốn xóa file này như thế nào?",
        "btn_del_rec": "Chỉ xóa lịch sử",
        "btn_del_both": "Xóa File gốc & Lịch sử",
        "btn_del_cancel": "Hủy",
        "msg_file_missing": "File không còn tồn tại!",
        "lbl_platform_count": "Hỗ trợ {} Nền tảng",
        "btn_sel_all": "Chọn tất cả",
        "btn_del_sel": "Xóa mục đã chọn ({})",
        "lbl_right_click_hint": "💡 Mẹo: Nhấn chuột phải vào file để có thêm tùy chọn",
        "msg_confirm_del_multi": "Bạn có chắc muốn xóa {} mục đã chọn khỏi lịch sử?",
        # Popups
        "pop_success": "Thành công",
        "pop_error": "Lỗi",
        "pop_warning": "Cảnh báo",
        "pop_confirm": "Xác nhận",
        "msg_all_done": "Đã tải xong toàn bộ {} file!",
        "msg_partial_done": "Hoàn tất {}. Lỗi {}.",
        "msg_stop_dl": "Bạn có muốn dừng tải xuống không?",
        "msg_update_avail": "Có phiên bản mới: {}\nH iện tại: {}\n\nBạn có muốn tải về không?",
        "msg_latest": "Bạn đang dùng phiên bản mới nhất ({})",
    },
    "en": {
        "tab_home": "Home",
        "tab_history": "Download History", # Renamed
        "tab_settings": "Settings",
        "info_source": " Source Info ",
        "lbl_link": "Video/Music Link:",
        "btn_paste": "📋 Paste",
        "chk_auto_paste": "Auto Paste Link",
        "btn_check": "🔍 Check",
        "btn_cancel_check": "✖ Cancel",
        "lbl_loading": "Loading info...",
        "lbl_filename": "Filename:",
        "lbl_filename_note": "(Empty = Original Name)",
        "lbl_save_at": "Save to:",
        "btn_browse": "...",
        "btn_open": "Open",
        "grp_cut": " Cut / Trim Tool ",
        "chk_enable_cut": "Enable Cut Mode",
        "lbl_time_fmt": "(Format: MM:SS or HH:MM:SS)",
        "lbl_start": "Start:",
        "chk_from_start": "From Start",
        "lbl_end": "End:",
        "chk_to_end": "To End",
        "grp_opts": " Formats & Options ",
        "lbl_format_title": "Select Format:",
        "opt_audio_aac": "Audio AAC (M4A)",
        "opt_audio_mp3": "Audio MP3",
        "opt_video_4k": "Video 4K (2160p)",
        "opt_video_2k": "Video 2K (1440p)",
        "opt_video_1080": "Video Full HD (1080p)",
        "lbl_advanced": "Advanced Options:",
        "chk_keep_audio": "Keep Original Audio",
        "chk_keep_video": "Keep Original Video",
        "chk_sub": "Download Subtitles (Select Lang...)",
        "chk_sub_count": "Download Subtitles ({} Selected)",
        "chk_playlist": "Download full Playlist/Album",
        "chk_open_done": "Open file when finished",
        "lbl_cookies": "Cookies (For blocked/age-gated):",
        "btn_cookies": "Select .txt File",
        "btn_guide": "Guide & Cookies",
        "lbl_queue": "Download Queue:",
        "col_title": "Video Name / File",
        "col_link": "URL",
        "btn_add_queue": "➕ Add to Queue",
        "btn_del_queue": "❌ Remove Selected",
        "lbl_ready": "Waiting...",
        "lbl_paste_hint": "Paste a link (YouTube, FB, Insta...) above to start...",
        "btn_download": "DOWNLOAD NOW",
        "btn_cancel": "✖ CANCEL",
        "set_title": "System Settings",
        "set_lang": "Language:",
        "set_theme": "Theme:",
        "set_bg": "Background Image:",
        "btn_img_browse": "Browse...",
        "btn_img_clear": "Clear",
        "chk_tray": "Minimize to Tray on Close",
        "btn_update": "⟳ Check for Updates",
        "btn_save": "Save & Apply",
        "msg_saved": "Settings Saved!",
        "err_no_link": "Please enter a link first!",
        "err_no_ffmpeg": "Missing ffmpeg.exe",
        "status_playlist": "Playlist Detected!",
        "status_ready": "Ready to download",
        "status_downloading": "Downloading...",
        "status_processing": "Processing (Mux/Convert)...",
        "status_done": "Finished!",
        "status_cancel": "Cancelled",
        "opt_audio_lossless": "Audio Lossless (FLAC/WAV)",
        "grp_fmt_setting": " Format Configuration (FFmpeg) ",
        "lbl_video_ext": "Default Video Container:",
        "lbl_audio_ext": "Default Audio Format:",
        "lbl_video_codec": "Video Codec Priority:",
        "val_codec_auto": "Auto (Best Quality)",
        "val_codec_h264": "H.264 (High Compatibility)",
        "val_codec_av1": "AV1/VP9 (High Efficiency)",
        "chk_metadata": "Add Metadata (Artist, Title)",
        "chk_thumbnail": "Embed Thumbnail to file",
        # History Tab Updates
        "col_check": "Select",
        "col_platform": "Platform",
        "col_size": "Size",
        "col_date": "Date",
        "ctx_open_file": "Open File",
        "ctx_open_folder": "Open Folder",
        "ctx_delete": "Delete...",
        "msg_del_title": "Confirm Delete",
        "msg_del_confirm": "How do you want to delete this?",
        "btn_del_rec": "History Only",
        "btn_del_both": "File & History",
        "btn_del_cancel": "Cancel",
        "msg_file_missing": "File not found!",
        "lbl_platform_count": "Supports {} Platforms",
        "btn_sel_all": "Select All",
        "btn_del_sel": "Delete Selected ({})",
        "lbl_right_click_hint": "💡 Tip: Right-click on file for more options",
        "msg_confirm_del_multi": "Are you sure you want to delete {} selected items from history?",
        # Popups
        "pop_success": "Success",
        "pop_error": "Error",
        "pop_warning": "Warning",
        "pop_confirm": "Confirm",
        "msg_all_done": "All {} files downloaded!",
        "msg_partial_done": "Finished {}. Failed {}.",
        "msg_stop_dl": "Do you want to stop downloading?",
        "msg_update_avail": "New version available: {}\nCurrent: {}\n\nDownload now?",
        "msg_latest": "You are using the latest version ({})",
    }
}

# --- LAZY IMPORT WRAPPER ---
yt_dlp = None

def lazy_import_ytdlp():
    global yt_dlp
    if yt_dlp is None:
        try:
            import yt_dlp
            import yt_dlp.utils
        except ImportError as e:
            raise ImportError(f"Missing 'yt_dlp'. Run: pip install yt-dlp\nError: {e}")

# --- CLASS SCROLLABLE FRAME ---
class ScrollableFrame(ttk.Frame):
    def __init__(self, container, bg_color, *args, **kwargs):
        super().__init__(container, *args, **kwargs)
        self.canvas = tk.Canvas(self, borderwidth=0, background=bg_color, highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = tk.Frame(self.canvas, background=bg_color)
        
        self.scrollable_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas_window = self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")
        self.canvas.bind('<Configure>', lambda e: self.canvas.itemconfig(self.canvas_window, width=e.width))
        self.canvas.bind('<Enter>', self._bound_to_mousewheel)
        self.canvas.bind('<Leave>', self._unbound_to_mousewheel)
        self.scrollable_frame.bind('<Enter>', self._bound_to_mousewheel)
        self.scrollable_frame.bind('<Leave>', self._unbound_to_mousewheel)

    def _bound_to_mousewheel(self, event):
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)
        self.canvas.bind_all("<Button-4>", self._on_mousewheel)
        self.canvas.bind_all("<Button-5>", self._on_mousewheel)

    def _unbound_to_mousewheel(self, event):
        self.canvas.unbind_all("<MouseWheel>")
        self.canvas.unbind_all("<Button-4>")
        self.canvas.unbind_all("<Button-5>")

    def _on_mousewheel(self, event):
        speed_multiplier = 3 
        if event.num == 4: self.canvas.yview_scroll(-1 * speed_multiplier, "units")
        elif event.num == 5: self.canvas.yview_scroll(1 * speed_multiplier, "units")
        else:
             delta = int(-1*(event.delta/120)) * speed_multiplier
             self.canvas.yview_scroll(delta, "units")

# --- SETTINGS & THEMES ---
THEMES = {
    "Light": {
        "bg": "#f0f2f5", "fg": "#333333", 
        "frame_bg": "#ffffff", "accent": "#1976d2", 
        "success": "#2e7d32", "input_bg": "#ffffff", "input_fg": "#000000",
        "placeholder": "gray"
    },
    "Dark": {
        "bg": "#1e1e1e", "fg": "#e0e0e0",  
        "frame_bg": "#2d2d2d", "accent": "#64b5f6", 
        "success": "#81c784", "input_bg": "#3c3c3c", "input_fg": "#ffffff",
        "placeholder": "#aaaaaa" 
    }
}

class YoutubeDownloaderApp:
    def __init__(self, root):
        self.root = root
        self.root.title(f"{APP_TITLE} - {VERSION}")
        
        app_width = 1000
        app_height = 850
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x_pos = (screen_width - app_width) // 2
        y_pos = (screen_height - app_height) // 2
        self.root.geometry(f"{app_width}x{app_height}+{x_pos}+{y_pos}")
        
        # Setup Config Path
        if os.name == 'nt': 
            app_data = os.getenv('LOCALAPPDATA')
            if not app_data: app_data = os.getenv('APPDATA')
        else: 
            app_data = os.path.expanduser("~/.config")

        self.config_dir = os.path.join(app_data, "Tsufutube")
        if not os.path.exists(self.config_dir):
            try: os.makedirs(self.config_dir)
            except: self.config_dir = os.getcwd() 

        self.settings_file = os.path.join(self.config_dir, "tsufu_settings.json")
        self.history_file = os.path.join(self.config_dir, "tsufu_history.json")
        
        self.load_settings()
        self.load_history()
        
        self.current_theme = THEMES[self.settings["theme"]]
        
        # State Variables
        self.lang = self.settings.get("language", "vi")
        self.last_update_time = 0 
        self.download_queue = []
        self.cookies_path_var = tk.StringVar(value="")
        self.is_cancelled = False
        self.last_clipboard = ""
        self.bg_image_ref = None
        self.thumb_image_ref = None 
        
        self.fetched_title = "" 
        self.is_fetching_info = False
        self.cancel_fetch_event = threading.Event()
        self.available_subtitles = {}
        self.selected_sub_langs = []
        
        # History selection
        self.history_selected_indices = set()
        self.history_tree = None

        self.style = ttk.Style()
        self.style.theme_use('clam')
        self.apply_theme_colors()
        self.ffmpeg_path = self.resource_path("ffmpeg.exe")
        
        # UI Persistence Vars
        self.url_var = tk.StringVar()
        self.name_var = tk.StringVar()
        self.path_var = tk.StringVar(value=os.getcwd())
        self.cut_var = tk.BooleanVar(value=False)
        self.start_chk_var = tk.BooleanVar(value=True)
        self.end_chk_var = tk.BooleanVar(value=True)
        self.type_var = tk.StringVar(value="video_1080")
        self.keep_audio_var = tk.BooleanVar(value=False)
        self.keep_video_var = tk.BooleanVar(value=False)
        self.sub_var = tk.BooleanVar(value=False)
        self.playlist_var = tk.BooleanVar(value=False)
        self.open_finished_var = tk.BooleanVar(value=False)
        
        # Settings Vars
        self.lang_var = tk.StringVar(value=self.lang)
        self.theme_var = tk.StringVar(value=self.settings.get("theme", "Dark"))
        self.tray_var = tk.BooleanVar(value=self.settings.get("minimize_to_tray", False))
        self.bg_path_var = tk.StringVar(value=self.settings.get("bg_image_path", ""))
        self.auto_clear_var = tk.BooleanVar(value=self.settings.get("auto_clear_link", True))
        self.auto_paste_var = tk.BooleanVar(value=self.settings.get("auto_paste", False)) 
        self.show_popup_var = tk.BooleanVar(value=self.settings.get("show_finished_popup", True))
        self.video_ext_var = tk.StringVar(value=self.settings.get("default_video_ext", "mp4"))
        self.audio_ext_var = tk.StringVar(value=self.settings.get("default_audio_ext", "mp3"))
        self.codec_var = tk.StringVar(value=self.settings.get("video_codec_priority", "auto"))
        self.meta_var = tk.BooleanVar(value=self.settings.get("add_metadata", False))
        self.thumb_embed_var = tk.BooleanVar(value=self.settings.get("embed_thumbnail", False))

        # UI Setup
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True)

        self.tab_home = tk.Frame(self.notebook, bg=self.current_theme["bg"])
        self.tab_history = tk.Frame(self.notebook, bg=self.current_theme["bg"])
        self.tab_settings = tk.Frame(self.notebook, bg=self.current_theme["bg"])
        
        self.setup_tabs()
        
        self.update_background_image()
        self.monitor_clipboard()
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        threading.Thread(target=self.check_for_updates, args=(False,), daemon=True).start()

    def T(self, key):
        return TRANSLATIONS.get(self.lang, TRANSLATIONS["en"]).get(key, key)

    def change_language_from_settings(self, event=None):
        self.lang = self.lang_var.get()
        self.setup_tabs()
        self.update_background_image()

    def setup_tabs(self):
        # Clear existing tabs
        for widget in self.tab_home.winfo_children(): widget.destroy()
        # History tab: clear logic slightly different to prevent full redraw loop
        for widget in self.tab_history.winfo_children(): widget.destroy()
        for widget in self.tab_settings.winfo_children(): widget.destroy()
        
        if not self.notebook.tabs():
            self.notebook.add(self.tab_home, text="")
            self.notebook.add(self.tab_history, text="")
            self.notebook.add(self.tab_settings, text="")
        
        self.notebook.tab(0, text=self.T("tab_home"))
        self.notebook.tab(1, text=self.T("tab_history"))
        self.notebook.tab(2, text=self.T("tab_settings"))

        self.setup_home_tab()
        self.init_history_tab() # Use Init instead of Refresh
        self.setup_settings_tab()
        self.toggle_cut_inputs() 

    def load_settings(self):
        default = {
            "language": "vi",
            "theme": "Dark", 
            "minimize_to_tray": False, 
            "bg_image_path": "",
            "auto_clear_link": True,       
            "auto_paste": False,
            "show_finished_popup": True,
            "default_video_ext": "mp4",
            "default_audio_ext": "mp3", 
            "video_codec_priority": "auto",
            "add_metadata": False,    
            "embed_thumbnail": False   
        }
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, "r", encoding="utf-8") as f:
                    self.settings = json.load(f)
                    for k, v in default.items(): self.settings.setdefault(k, v)
            else: self.settings = default
        except: self.settings = default

    def save_settings(self):
        self.settings["language"] = self.lang_var.get()
        self.settings["theme"] = self.theme_var.get()
        self.settings["minimize_to_tray"] = self.tray_var.get()
        self.settings["bg_image_path"] = self.bg_path_var.get()
        self.settings["auto_clear_link"] = self.auto_clear_var.get()
        self.settings["auto_paste"] = self.auto_paste_var.get()
        self.settings["show_finished_popup"] = self.show_popup_var.get()
        self.settings["default_video_ext"] = self.video_ext_var.get()
        self.settings["default_audio_ext"] = self.audio_ext_var.get()
        self.settings["video_codec_priority"] = self.codec_var.get()
        self.settings["add_metadata"] = self.meta_var.get()
        self.settings["embed_thumbnail"] = self.thumb_embed_var.get()
        
        try:
            with open(self.settings_file, "w", encoding="utf-8") as f: json.dump(self.settings, f, ensure_ascii=False, indent=4)
            messagebox.showinfo(self.T("pop_success"), self.T("msg_saved"))
            self.change_language_from_settings()
        except Exception as e: messagebox.showerror(self.T("pop_error"), str(e))

    def load_history(self):
        try:
            if os.path.exists(self.history_file):
                with open(self.history_file, "r", encoding="utf-8") as f:
                    self.history_data = json.load(f)
            else: self.history_data = []
        except: self.history_data = []
        # Inject checked state to memory (False by default)
        for item in self.history_data: item["_checked"] = False

    def save_history(self):
        # Remove temporary state before saving
        data_to_save = []
        for item in self.history_data:
            clean_item = item.copy()
            if "_checked" in clean_item: del clean_item["_checked"]
            data_to_save.append(clean_item)
            
        try:
            with open(self.history_file, "w", encoding="utf-8") as f:
                json.dump(data_to_save, f, ensure_ascii=False, indent=4)
        except: pass

    def add_to_history(self, item):
        item["_checked"] = False
        self.history_data.insert(0, item)
        self.save_history()
        self.refresh_history_view() 

    def apply_theme_colors(self):
        t = self.current_theme
        self.root.configure(bg=t["bg"])
        self.style.configure("TNotebook", background=t["bg"], borderwidth=0)
        self.style.configure("TNotebook.Tab", background=t["frame_bg"], foreground=t["fg"], padding=[15, 5], font=("Segoe UI", 10))
        self.style.map("TNotebook.Tab", background=[("selected", t["accent"])], foreground=[("selected", "white")])
        self.style.configure("Treeview", background=t["input_bg"], foreground=t["input_fg"], fieldbackground=t["input_bg"], font=("Segoe UI", 9))
        self.style.configure("Treeview.Heading", background=t["frame_bg"], foreground=t["fg"], font=("Segoe UI", 9, "bold"))
        self.style.configure("TProgressbar", thickness=20, background=t["success"])

    def resource_path(self, relative_path):
        try: base = sys._MEIPASS
        except: base = os.path.abspath(".")
        return os.path.join(base, relative_path)

    # --- TAB 1: HOME ---
    def setup_home_tab(self):
        t = self.current_theme
        
        self.main_container = ScrollableFrame(self.tab_home, bg_color=t["bg"])
        self.main_container.pack(fill="both", expand=True, padx=0, pady=0)
        self.content_frame = self.main_container.scrollable_frame

        self.bottom_bar = tk.Frame(self.tab_home, bg=t["bg"], bd=1, relief="raised")
        self.bottom_bar.pack(fill="x", side="bottom")

        self.load_branding()
        self.create_widgets()
        self.create_bottom_bar()

    def load_branding(self):
        header_frame = tk.Frame(self.content_frame, bg=self.current_theme["bg"])
        header_frame.pack(pady=(10, 5), fill="x", padx=40)
        
        logo_box = tk.Frame(header_frame, bg=self.current_theme["bg"])
        logo_box.pack(side="left")
        try:
            self.root.iconbitmap(self.resource_path("icon_chuan.ico"))
            self.logo_img = tk.PhotoImage(file=self.resource_path("logo.png")).subsample(3, 3)
            tk.Label(logo_box, image=self.logo_img, bg=self.current_theme["bg"], bd=0).pack()
        except: pass

        center_box = tk.Frame(header_frame, bg=self.current_theme["bg"])
        center_box.pack(side="left", fill="x", expand=True)

        tk.Label(center_box, text=APP_TITLE, font=("Segoe UI", 24, "bold"), 
                 bg=self.current_theme["bg"], fg="#ce2d35").pack(side="top")
        
        tk.Label(center_box, text=APP_SLOGAN, 
                 font=("Segoe UI", 11, "italic"), bg=self.current_theme["bg"], fg="gray").pack(side="top")

        platform_text = self.T("lbl_platform_count").format("1000+")
        tk.Label(center_box, text=platform_text, font=("Segoe UI", 9, "bold"), 
                 bg="#e3f2fd", fg="#1565c0", padx=10, pady=2, relief="solid", bd=1).pack(side="top", pady=5)
        
        link_frame = tk.Frame(header_frame, bg=self.current_theme["bg"])
        link_frame.pack(side="right", pady=2)
        tk.Button(link_frame, text="☕ Donate", command=self.open_donate_link,
                  bg="#FFDD00", fg="black", font=("Segoe UI", 8, "bold"), bd=0, cursor="hand2", padx=10, pady=5).pack(side="top", pady=2, fill="x")
        tk.Button(link_frame, text="⬇ GitHub", command=self.open_update_link,
                  bg="black", fg="white", font=("Segoe UI", 8, "bold"), bd=0, cursor="hand2", padx=10, pady=5).pack(side="top", pady=2, fill="x")

    def create_widgets(self):
        t = self.current_theme
        container_pad = tk.Frame(self.content_frame, bg=t["bg"])
        container_pad.pack(fill="x", padx=40)

        # INPUT FRAME
        input_frame = tk.LabelFrame(container_pad, text=self.T("info_source"), font=("Segoe UI", 10, "bold"), 
                                    bg=t["frame_bg"], fg=t["fg"], padx=10, pady=10, bd=0, highlightthickness=1)
        input_frame.pack(fill="x", pady=5)

        row1 = tk.Frame(input_frame, bg=t["frame_bg"])
        row1.grid(row=0, column=0, columnspan=3, sticky="ew", pady=(0, 5))
        
        tk.Label(row1, text=self.T("lbl_link"), bg=t["frame_bg"], fg=t["fg"], font=("Segoe UI", 10)).pack(side="left")
        tk.Checkbutton(row1, text=self.T("chk_auto_paste"), variable=self.auto_paste_var, 
                       bg=t["frame_bg"], fg=t["accent"], font=("Segoe UI", 8), 
                       selectcolor=t["frame_bg"], activebackground=t["frame_bg"]).pack(side="right")

        link_container = tk.Frame(input_frame, bg=t["frame_bg"])
        link_container.grid(row=1, column=0, columnspan=3, sticky="ew", padx=5, pady=0)
        
        self.url_entry = tk.Entry(link_container, textvariable=self.url_var, font=("Segoe UI", 11), bd=1, relief="solid", bg=t["input_bg"], fg=t["input_fg"], insertbackground=t["fg"])
        self.url_entry.pack(side="left", fill="x", expand=True)
        self.url_entry.bind('<KeyRelease>', self.on_url_change_delayed)
        
        btn_container = tk.Frame(link_container, bg=t["frame_bg"])
        btn_container.pack(side="left", padx=(5, 0))
        
        tk.Button(btn_container, text=self.T("btn_paste"), command=self.paste_link, 
                  bg="#e0e0e0", fg="black", font=("Segoe UI", 9), cursor="hand2", width=6).pack(side="left", padx=1)
        
        self.check_btn = tk.Button(btn_container, text=self.T("btn_check"), command=self.toggle_check_cancel,
                  bg=t["accent"], fg="white", font=("Segoe UI", 9, "bold"), cursor="hand2", width=11)
        self.check_btn.pack(side="left", padx=1)

        # INFO DISPLAY FRAME
        self.info_frame = tk.Frame(input_frame, bg=t["frame_bg"], bd=1, relief="sunken")
        self.info_frame.grid(row=2, column=0, columnspan=3, sticky="ew", padx=5, pady=(10, 10))
        if not self.is_fetching_info and not self.fetched_title:
             self.info_frame.grid_remove() 

        self.thumb_container = tk.Frame(self.info_frame, bg="black", width=160, height=90)
        self.thumb_container.pack_propagate(False) 
        self.thumb_container.pack(side="left", padx=5, pady=5)

        self.thumb_label = tk.Label(self.thumb_container, bg="#333", fg="white", text="...", font=("Segoe UI", 8)) 
        self.thumb_label.pack(fill="both", expand=True)
        if self.thumb_image_ref: self.thumb_label.config(image=self.thumb_image_ref, text="")

        self.title_label = tk.Label(self.info_frame, text=self.fetched_title if self.fetched_title else self.T("lbl_loading"), wraplength=400, justify="left", 
                                    font=("Segoe UI", 10, "bold"), bg=t["frame_bg"], fg=t["fg"])
        self.title_label.pack(side="left", fill="both", expand=True, padx=5)

        tk.Label(input_frame, text=self.T("lbl_filename"), bg=t["frame_bg"], fg=t["fg"], font=("Segoe UI", 10)).grid(row=3, column=0, sticky="w", pady=5)
        self.name_entry = tk.Entry(input_frame, textvariable=self.name_var, font=("Segoe UI", 11), bd=1, relief="solid", bg=t["input_bg"], fg=t["input_fg"], insertbackground=t["fg"])
        self.name_entry.grid(row=3, column=1, columnspan=2, padx=5, pady=5, sticky="ew")
        
        tk.Label(input_frame, text=self.T("lbl_filename_note"), font=("Segoe UI", 9, "italic"), bg=t["frame_bg"], fg=t["placeholder"]).grid(row=4, column=1, sticky="w", padx=5)

        tk.Label(input_frame, text=self.T("lbl_save_at"), bg=t["frame_bg"], fg=t["fg"], font=("Segoe UI", 10)).grid(row=5, column=0, sticky="w", pady=5)
        self.path_entry = tk.Entry(input_frame, textvariable=self.path_var, state='readonly', font=("Segoe UI", 10), bd=1, relief="solid")
        self.path_entry.grid(row=5, column=1, padx=5, pady=5, sticky="ew")
        
        btn_frame = tk.Frame(input_frame, bg=t["frame_bg"])
        btn_frame.grid(row=5, column=2, sticky="e", padx=5)
        tk.Button(btn_frame, text=self.T("btn_browse"), command=self.select_folder, width=4, cursor="hand2").pack(side="left", padx=2)
        tk.Button(btn_frame, text=self.T("btn_open"), command=self.open_save_folder, width=6, bg=t["accent"], fg="white", bd=0, cursor="hand2").pack(side="left", padx=2)
        
        input_frame.columnconfigure(1, weight=1)

        # CUT FRAME
        cut_frame = tk.LabelFrame(container_pad, text=self.T("grp_cut"), font=("Segoe UI", 10, "bold"), 
                                  bg=t["frame_bg"], fg=t["fg"], padx=10, pady=5, bd=0, highlightthickness=1)
        cut_frame.pack(fill="x", pady=5)

        top_cut_row = tk.Frame(cut_frame, bg=t["frame_bg"])
        top_cut_row.pack(fill="x", pady=2)
        
        self.cut_chk = tk.Checkbutton(top_cut_row, text=self.T("chk_enable_cut"), variable=self.cut_var, command=self.toggle_cut_inputs, 
                                  bg=t["frame_bg"], fg=t["accent"], font=("Segoe UI", 9, "bold"), selectcolor=t["frame_bg"], activebackground=t["frame_bg"])
        self.cut_chk.pack(side="left")
        tk.Label(top_cut_row, text=self.T("lbl_time_fmt"), bg=t["frame_bg"], fg=t["placeholder"], font=("Segoe UI", 9)).pack(side="right")

        time_row = tk.Frame(cut_frame, bg=t["frame_bg"])
        time_row.pack(fill="x", pady=5)

        tk.Label(time_row, text=self.T("lbl_start"), bg=t["frame_bg"], fg=t["fg"]).pack(side="left")
        self.start_entry = tk.Entry(time_row, width=10, font=("Segoe UI", 10), justify="center", bd=1, relief="solid")
        self.start_entry.pack(side="left", padx=5)
        self.add_placeholder(self.start_entry, "00:00:00")
        self.start_chk = tk.Checkbutton(time_row, text=self.T("chk_from_start"), variable=self.start_chk_var, command=self.toggle_cut_inputs, bg=t["frame_bg"], fg=t["fg"], selectcolor=t["frame_bg"], activebackground=t["frame_bg"])
        self.start_chk.pack(side="left", padx=5)

        ttk.Separator(time_row, orient="vertical").pack(side="left", fill="y", padx=15)

        tk.Label(time_row, text=self.T("lbl_end"), bg=t["frame_bg"], fg=t["fg"]).pack(side="left")
        self.end_entry = tk.Entry(time_row, width=10, font=("Segoe UI", 10), justify="center", bd=1, relief="solid")
        self.end_entry.pack(side="left", padx=5)
        self.add_placeholder(self.end_entry, "00:00:00")
        self.end_chk = tk.Checkbutton(time_row, text=self.T("chk_to_end"), variable=self.end_chk_var, command=self.toggle_cut_inputs, bg=t["frame_bg"], fg=t["fg"], selectcolor=t["frame_bg"], activebackground=t["frame_bg"])
        self.end_chk.pack(side="left", padx=5)

        # OPTIONS FRAME
        opts_frame = tk.LabelFrame(container_pad, text=self.T("grp_opts"), font=("Segoe UI", 10, "bold"), 
                                    bg=t["frame_bg"], fg=t["fg"], padx=10, pady=5, bd=0, highlightthickness=1)
        opts_frame.pack(fill="x", pady=5)

        main_opts_grid = tk.Frame(opts_frame, bg=t["frame_bg"])
        main_opts_grid.pack(fill="x", pady=5)

        # Left: Format
        fmt_frame = tk.Frame(main_opts_grid, bg=t["frame_bg"])
        fmt_frame.pack(side="left", fill="both", expand=True)
        
        tk.Label(fmt_frame, text=self.T("lbl_format_title"), font=("Segoe UI", 9, "bold", "underline"), bg=t["frame_bg"], fg=t["fg"]).grid(row=0, column=0, sticky="w", columnspan=2, pady=(0,8))
        
        rb_opts = {'bg': t["frame_bg"], 'fg': t["fg"], 'selectcolor': t["frame_bg"], 'activebackground': t["frame_bg"]}
        
        tk.Radiobutton(fmt_frame, text=self.T("opt_audio_aac"), variable=self.type_var, value="audio", **rb_opts).grid(row=1, column=0, sticky="w", pady=2)
        tk.Radiobutton(fmt_frame, text=self.T("opt_audio_mp3"), variable=self.type_var, value="audio_mp3", **rb_opts).grid(row=2, column=0, sticky="w", pady=2)
        tk.Radiobutton(fmt_frame, text=self.T("opt_audio_lossless"), variable=self.type_var, value="audio_lossless", font=("Segoe UI", 9, "italic"), **rb_opts).grid(row=3, column=0, sticky="w", pady=2)
        
        r_4k = tk.Radiobutton(fmt_frame, text=self.T("opt_video_4k"), variable=self.type_var, value="video_4k", font=("Segoe UI", 9, "bold"), **rb_opts)
        r_4k.config(fg="#d32f2f")
        r_4k.grid(row=4, column=0, sticky="w", pady=2)
        
        r_2k = tk.Radiobutton(fmt_frame, text=self.T("opt_video_2k"), variable=self.type_var, value="video_2k", font=("Segoe UI", 9, "bold"), **rb_opts)
        r_2k.config(fg="#c2185b")
        r_2k.grid(row=5, column=0, sticky="w", pady=2)

        r_1080 = tk.Radiobutton(fmt_frame, text=self.T("opt_video_1080"), variable=self.type_var, value="video_1080", font=("Segoe UI", 9, "bold"), **rb_opts)
        r_1080.grid(row=6, column=0, sticky="w", pady=2)

        resolutions = [
            ("Video HD 720p", "video_720"),
            ("Video SD 480p", "video_480"),
            ("Video 360p", "video_360"),
            ("Video 240p", "video_240"),
            ("Video 144p", "video_144")
        ]
        for i, (text, val) in enumerate(resolutions):
            tk.Radiobutton(fmt_frame, text=text, variable=self.type_var, value=val, **rb_opts).grid(row=1+i, column=1, sticky="w", padx=20, pady=2)

        ttk.Separator(main_opts_grid, orient="vertical").pack(side="left", fill="y", padx=20)

        # Right: Options
        sub_frame = tk.Frame(main_opts_grid, bg=t["frame_bg"])
        sub_frame.pack(side="left", fill="both", expand=True)

        tk.Label(sub_frame, text=self.T("lbl_advanced"), font=("Segoe UI", 9, "bold", "underline"), bg=t["frame_bg"], fg=t["success"]).pack(anchor="w", pady=(0,8))
        
        sep_row = tk.Frame(sub_frame, bg=t["frame_bg"])
        sep_row.pack(anchor="w", pady=2)
        tk.Checkbutton(sep_row, text=self.T("chk_keep_audio"), variable=self.keep_audio_var, **rb_opts).pack(side="left")
        tk.Checkbutton(sep_row, text=self.T("chk_keep_video"), variable=self.keep_video_var, **rb_opts).pack(side="left", padx=10)
        
        sub_style = rb_opts.copy()
        sub_style['fg'] = '#e65100'
        sub_txt = self.T("chk_sub")
        if self.selected_sub_langs: sub_txt = self.T("chk_sub_count").format(len(self.selected_sub_langs))
        
        self.sub_chk = tk.Checkbutton(sub_frame, text=sub_txt, variable=self.sub_var, command=self.on_sub_toggled, **sub_style)
        self.sub_chk.pack(anchor="w", pady=2)
        
        self.plist_chk = tk.Checkbutton(sub_frame, text=self.T("chk_playlist"), variable=self.playlist_var, **sub_style)
        self.plist_chk.pack(anchor="w", pady=2)
        
        open_style = rb_opts.copy()
        open_style['fg'] = '#d32f2f'
        tk.Checkbutton(sub_frame, text=self.T("chk_open_done"), variable=self.open_finished_var, **open_style).pack(anchor="w", pady=2)

        # COOKIES
        cookie_frame = tk.Frame(container_pad, bg=t["bg"])
        cookie_frame.pack(fill="x", pady=10)
        
        tk.Label(cookie_frame, text=self.T("lbl_cookies"), bg=t["bg"], fg=t["fg"], font=("Segoe UI", 9, "bold")).pack(side="left")
        self.cookie_btn = tk.Button(cookie_frame, text=self.T("btn_cookies"), command=self.select_cookies, font=("Segoe UI", 8), bg="#e0e0e0", cursor="hand2")
        self.cookie_btn.pack(side="left", padx=5)
        self.cookie_status = tk.Label(cookie_frame, text="(Chưa chọn)" if not self.cookies_path_var.get() else "Đã chọn", 
                                      fg="gray" if not self.cookies_path_var.get() else t["success"], bg=t["bg"], font=("Segoe UI", 8, "italic"))
        self.cookie_status.pack(side="left")
        tk.Button(cookie_frame, text=self.T("btn_guide"), command=self.show_cookies_guide, font=("Segoe UI", 8, "bold"), bg="#fff9c4", fg="black", cursor="hand2").pack(side="right", padx=2)

        # QUEUE
        queue_frame = tk.Frame(container_pad, bg=t["bg"])
        queue_frame.pack(fill="x", pady=(0, 20))
        
        q_head = tk.Frame(queue_frame, bg=t["bg"])
        q_head.pack(fill="x")
        tk.Label(q_head, text=self.T("lbl_queue"), font=("Segoe UI", 9, "bold"), bg=t["bg"], fg=t["accent"]).pack(side="left")
        
        q_btns = tk.Frame(q_head, bg=t["bg"])
        q_btns.pack(side="right")
        tk.Button(q_btns, text=self.T("btn_add_queue"), command=self.add_to_queue, font=("Segoe UI", 8), bg=t["accent"], fg="white", bd=0).pack(side="left", padx=2)
        tk.Button(q_btns, text=self.T("btn_del_queue"), command=self.remove_from_queue, font=("Segoe UI", 8), bg="#d32f2f", fg="white", bd=0).pack(side="left", padx=2)

        self.queue_tree = ttk.Treeview(queue_frame, columns=("title", "link"), show="headings", height=4) 
        self.queue_tree.heading("title", text=self.T("col_title"))
        self.queue_tree.heading("link", text=self.T("col_link"))
        self.queue_tree.column("title", width=400)
        self.queue_tree.column("link", width=300)
        self.queue_tree.pack(fill="x", pady=2)
        
        for task in self.download_queue:
            self.queue_tree.insert("", tk.END, values=(task.get("title", "Unknown"), task["url"]))

    def create_bottom_bar(self):
        t = self.current_theme
        status_frame = tk.Frame(self.bottom_bar, bg=t["bg"])
        status_frame.pack(fill="x", padx=20, pady=(10, 5))

        self.status_label = tk.Label(status_frame, text=self.T("lbl_paste_hint"), font=("Segoe UI", 10, "bold"), bg=t["bg"], fg=t["success"])
        self.status_label.pack(side="top")

        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(status_frame, variable=self.progress_var, maximum=100)
        self.progress_bar.pack(fill="x", pady=(5, 10))

        btn_action_frame = tk.Frame(self.bottom_bar, bg=t["bg"])
        btn_action_frame.pack(pady=(0, 20))

        self.download_btn = tk.Button(btn_action_frame, text=self.T("btn_download"), font=("Segoe UI", 12, "bold"), 
                                      bg=t["accent"], fg="white", height=1, width=25, 
                                      bd=0, cursor="hand2", activebackground="#0d47a1", activeforeground="white",
                                      command=self.start_download_thread)
        self.download_btn.pack(side="left", padx=10)

        self.cancel_btn = tk.Button(btn_action_frame, text=self.T("btn_cancel"), font=("Segoe UI", 11, "bold"),
                                    bg="gray", fg="white", height=1, width=12,
                                    bd=0, cursor="hand2", state="disabled",
                                    command=self.cancel_download)
        self.cancel_btn.pack(side="left", padx=10)

    # --- TAB 2: HISTORY (FIXED RELOAD & BULK ACTION) ---
    def init_history_tab(self):
        """Build the UI once"""
        t = self.current_theme
        
        # Main Container
        frame = tk.Frame(self.tab_history, bg=t["bg"], padx=20, pady=20)
        frame.pack(fill="both", expand=True)

        # Header with Title and Bulk Actions
        header = tk.Frame(frame, bg=t["bg"])
        header.pack(fill="x", pady=(0, 10))
        
        tk.Label(header, text=self.T("tab_history"), font=("Segoe UI", 18, "bold"), bg=t["bg"], fg=t["fg"]).pack(side="left")
        
        # Bulk Action Buttons
        btn_box = tk.Frame(header, bg=t["bg"])
        btn_box.pack(side="right")

        self.lbl_del_sel = tk.Button(btn_box, text=self.T("btn_del_sel").format(0), command=self.delete_selected_history, 
                                    bg="#d32f2f", fg="white", font=("Segoe UI", 9), bd=0, padx=10, state="disabled")
        self.lbl_del_sel.pack(side="right", padx=5)

        tk.Button(btn_box, text=self.T("btn_sel_all"), command=self.history_select_all, 
                  bg=t["accent"], fg="white", font=("Segoe UI", 9), bd=0, padx=10).pack(side="right", padx=5)

        # Treeview
        cols = ("check", "platform", "title", "size", "date")
        self.history_tree = ttk.Treeview(frame, columns=cols, show="headings", selectmode="browse")
        
        self.history_tree.heading("check", text=self.T("col_check"))
        self.history_tree.heading("platform", text=self.T("col_platform"))
        self.history_tree.heading("title", text=self.T("col_title"))
        self.history_tree.heading("size", text=self.T("col_size"))
        self.history_tree.heading("date", text=self.T("col_date"))
        
        self.history_tree.column("check", width=50, anchor="center")
        self.history_tree.column("platform", width=100, anchor="center")
        self.history_tree.column("title", width=400)
        self.history_tree.column("size", width=100, anchor="center")
        self.history_tree.column("date", width=150, anchor="center")

        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=self.history_tree.yview)
        self.history_tree.configure(yscrollcommand=scrollbar.set)
        
        self.history_tree.pack(side="top", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y", in_=self.history_tree)
        
        # Bottom Hint
        tk.Label(frame, text=self.T("lbl_right_click_hint"), font=("Segoe UI", 9, "italic"), bg=t["bg"], fg="gray").pack(side="bottom", anchor="w", pady=5)

        # Bindings
        self.history_tree.bind("<Button-1>", self.on_history_click)
        self.history_tree.bind("<Button-3>", self.on_history_right_click)

        # Context Menu
        self.history_menu = tk.Menu(self.root, tearoff=0)
        self.history_menu.add_command(label=self.T("ctx_open_file"), command=self.history_open_file)
        self.history_menu.add_command(label=self.T("ctx_open_folder"), command=self.history_open_folder)
        self.history_menu.add_separator()
        self.history_menu.add_command(label=self.T("ctx_delete"), command=self.history_delete_dialog)

        # Initial Load
        self.refresh_history_view()

    def refresh_history_view(self):
        """Updates data only, does not rebuild UI"""
        if not self.history_tree: return
        
        # Clear existing items
        self.history_tree.delete(*self.history_tree.get_children())
        
        # Re-populate
        for idx, item in enumerate(self.history_data):
            check_mark = "☑" if item.get("_checked", False) else "☐"
            self.history_tree.insert("", tk.END, iid=idx, values=(
                check_mark,
                item.get("platform", "Unknown"),
                item.get("title", "Unknown"),
                item.get("size", "0 MB"),
                item.get("date", "")
            ))
        self.update_bulk_btn_state()

    def on_history_click(self, event):
        region = self.history_tree.identify("region", event.x, event.y)
        if region == "heading": return

        item_id = self.history_tree.identify_row(event.y)
        col = self.history_tree.identify_column(event.x)
        
        if item_id and col == "#1": # Column 'check'
            idx = int(item_id)
            if idx < len(self.history_data):
                self.history_data[idx]["_checked"] = not self.history_data[idx]["_checked"]
                
                # Update visual only for this row
                current_vals = self.history_tree.item(item_id, "values")
                new_mark = "☑" if self.history_data[idx]["_checked"] else "☐"
                self.history_tree.item(item_id, values=(new_mark, *current_vals[1:]))
                
                self.update_bulk_btn_state()
            return "break" # Prevent default selection on checkbox click

    def history_select_all(self):
        all_checked = all(item.get("_checked", False) for item in self.history_data)
        target_state = not all_checked
        
        for item in self.history_data: item["_checked"] = target_state
        self.refresh_history_view()

    def update_bulk_btn_state(self):
        count = sum(1 for item in self.history_data if item.get("_checked", False))
        if count > 0:
            self.lbl_del_sel.config(text=self.T("btn_del_sel").format(count), state="normal", bg="#d32f2f")
        else:
            self.lbl_del_sel.config(text=self.T("btn_del_sel").format(0), state="disabled", bg="gray")

    def delete_selected_history(self):
        to_delete_indices = [i for i, x in enumerate(self.history_data) if x.get("_checked")]
        if not to_delete_indices: return

        if messagebox.askyesno(self.T("msg_del_title"), self.T("msg_confirm_del_multi").format(len(to_delete_indices))):
             # Delete from bottom up to avoid index shifting issues
             for i in sorted(to_delete_indices, reverse=True):
                 self.history_data.pop(i)
             self.save_history()
             self.refresh_history_view()

    def on_history_right_click(self, event):
        item = self.history_tree.identify_row(event.y)
        if item:
            self.history_tree.selection_set(item)
            self.history_menu.post(event.x_root, event.y_root)

    def get_selected_history(self):
        sel = self.history_tree.selection()
        if not sel: return None
        idx = int(sel[0]) # iid is index
        return idx, self.history_data[idx]

    def history_open_file(self):
        res = self.get_selected_history()
        if res:
            path = res[1].get("path")
            if path and os.path.exists(path): os.startfile(path)
            else: messagebox.showerror(self.T("pop_error"), self.T("msg_file_missing"))

    def history_open_folder(self):
        res = self.get_selected_history()
        if res:
            path = res[1].get("path")
            folder = os.path.dirname(path)
            if folder and os.path.exists(folder): os.startfile(folder)

    def history_delete_dialog(self):
        res = self.get_selected_history()
        if not res: return
        idx, item = res
        
        dialog = tk.Toplevel(self.root)
        dialog.title(self.T("msg_del_title"))
        dialog.geometry("400x180")
        
        tk.Label(dialog, text=self.T("msg_del_confirm"), font=("Segoe UI", 10), pady=15).pack()
        
        btn_frame = tk.Frame(dialog)
        btn_frame.pack(pady=10)

        def del_record():
            self.history_data.pop(idx)
            self.save_history()
            self.refresh_history_view()
            dialog.destroy()

        def del_both():
            path = item.get("path")
            if path and os.path.exists(path):
                try: os.remove(path)
                except: pass
            del_record()

        tk.Button(btn_frame, text=self.T("btn_del_rec"), command=del_record, bg="#2196F3", fg="white", padx=10).pack(side="left", padx=5)
        tk.Button(btn_frame, text=self.T("btn_del_both"), command=del_both, bg="#d32f2f", fg="white", padx=10).pack(side="left", padx=5)
        tk.Button(btn_frame, text=self.T("btn_del_cancel"), command=dialog.destroy, padx=10).pack(side="left", padx=5)


    # --- TAB 3: SETTINGS ---
    def setup_settings_tab(self):
        t = self.current_theme
        frame = tk.Frame(self.tab_settings, bg=t["bg"], padx=40, pady=20)
        frame.pack(fill="both", expand=True)
        
        tk.Label(frame, text=self.T("set_title"), font=("Segoe UI", 18, "bold"), bg=t["bg"], fg=t["fg"]).pack(anchor="w", pady=(0, 15))

        # UI Group
        group_ui = tk.LabelFrame(frame, text=" Giao diện & Hệ thống ", font=("Segoe UI", 10, "bold"), bg=t["bg"], fg=t["accent"], bd=1, relief="solid")
        group_ui.pack(fill="x", pady=(0, 10), ipadx=10, ipady=5)

        row_1 = tk.Frame(group_ui, bg=t["bg"])
        row_1.pack(fill="x", pady=2)
        
        tk.Label(row_1, text=self.T("set_lang"), bg=t["bg"], fg=t["fg"]).pack(side="left")
        ttk.Combobox(row_1, textvariable=self.lang_var, values=["vi", "en"], state="readonly", width=5).pack(side="left", padx=(5, 15))

        tk.Label(row_1, text=self.T("set_theme"), bg=t["bg"], fg=t["fg"]).pack(side="left")
        ttk.Combobox(row_1, textvariable=self.theme_var, values=["Light", "Dark"], state="readonly", width=10).pack(side="left", padx=10)
        
        row_bg = tk.Frame(group_ui, bg=t["bg"])
        row_bg.pack(fill="x", pady=5)
        tk.Label(row_bg, text=self.T("set_bg"), bg=t["bg"], fg=t["fg"]).pack(side="left")
        tk.Entry(row_bg, textvariable=self.bg_path_var, width=25, bg=t["input_bg"], fg=t["input_fg"]).pack(side="left", padx=5)
        tk.Button(row_bg, text="...", command=self.browse_bg, width=3).pack(side="left", padx=2)
        tk.Button(row_bg, text="X", command=self.clear_bg, width=3).pack(side="left", padx=2)

        chk_opts = {'bg': t["bg"], 'fg': t["fg"], 'selectcolor': t["bg"], 'activebackground': t["bg"], 'font': ("Segoe UI", 9)}
        row_2 = tk.Frame(group_ui, bg=t["bg"])
        row_2.pack(fill="x", pady=2)
        tk.Checkbutton(row_2, text=self.T("chk_tray"), variable=self.tray_var, **chk_opts).pack(side="left")
        tk.Checkbutton(row_2, text="Auto clear Link", variable=self.auto_clear_var, **chk_opts).pack(side="left", padx=15)
        tk.Checkbutton(row_2, text="Popup Done", variable=self.show_popup_var, **chk_opts).pack(side="left", padx=15)

        # Format Group
        group_fmt = tk.LabelFrame(frame, text=self.T("grp_fmt_setting"), font=("Segoe UI", 10, "bold"), bg=t["bg"], fg="#e65100", bd=1, relief="solid")
        group_fmt.pack(fill="x", pady=(0, 15), ipadx=10, ipady=5)
        
        fmt_row = tk.Frame(group_fmt, bg=t["bg"])
        fmt_row.pack(fill="x", pady=5)
        
        tk.Label(fmt_row, text=self.T("lbl_video_ext"), bg=t["bg"], fg=t["fg"], font=("Segoe UI", 9, "bold")).grid(row=0, column=0, sticky="w", padx=5)
        vid_cbo = ttk.Combobox(fmt_row, textvariable=self.video_ext_var, values=["mp4", "mkv", "webm", "avi", "mov"], state="readonly", width=8)
        vid_cbo.grid(row=0, column=1, sticky="w", padx=5)
        
        tk.Label(fmt_row, text=self.T("lbl_audio_ext"), bg=t["bg"], fg=t["fg"], font=("Segoe UI", 9, "bold")).grid(row=0, column=2, sticky="w", padx=(20, 5))
        aud_cbo = ttk.Combobox(fmt_row, textvariable=self.audio_ext_var, values=["mp3", "m4a", "flac", "wav", "ogg", "opus"], state="readonly", width=8)
        aud_cbo.grid(row=0, column=3, sticky="w", padx=5)

        codec_row = tk.Frame(group_fmt, bg=t["bg"])
        codec_row.pack(fill="x", pady=5)
        tk.Label(codec_row, text=self.T("lbl_video_codec"), bg=t["bg"], fg=t["fg"], font=("Segoe UI", 9, "bold")).pack(side="left", padx=5)
        
        codecs = {
            self.T("val_codec_auto"): "auto",
            self.T("val_codec_h264"): "h264",
            self.T("val_codec_av1"): "av1"
        }
        codec_values = list(codecs.keys())
        
        def get_codec_display(val):
            for k, v in codecs.items(): 
                if v == val: return k
            return list(codecs.keys())[0]

        self.codec_display_var = tk.StringVar(value=get_codec_display(self.codec_var.get()))
        
        def on_codec_change(event):
            self.codec_var.set(codecs[self.codec_display_var.get()])

        c_cbo = ttk.Combobox(codec_row, textvariable=self.codec_display_var, values=codec_values, state="readonly", width=25)
        c_cbo.pack(side="left", padx=5)
        c_cbo.bind("<<ComboboxSelected>>", on_codec_change)

        meta_row = tk.Frame(group_fmt, bg=t["bg"])
        meta_row.pack(fill="x", pady=5)
        tk.Checkbutton(meta_row, text=self.T("chk_metadata"), variable=self.meta_var, **chk_opts).pack(side="left", padx=5)
        tk.Checkbutton(meta_row, text=self.T("chk_thumbnail"), variable=self.thumb_embed_var, **chk_opts).pack(side="left", padx=20)

        # Action Buttons
        btn_row = tk.Frame(frame, bg=t["bg"])
        btn_row.pack(fill="x", pady=20)
        tk.Button(btn_row, text=self.T("btn_update"), command=lambda: self.check_for_updates(manual_check=True), 
                  bg="#2196F3", fg="white", font=("Segoe UI", 10), bd=0, padx=15, pady=8).pack(side="left")
        tk.Button(btn_row, text=self.T("btn_save"), command=self.save_settings, 
                  bg=t["accent"], fg="white", font=("Segoe UI", 10, "bold"), bd=0, padx=20, pady=8).pack(side="right")

    # --- LOGIC & HELPERS ---
    def check_for_updates(self, manual_check=False):
        try:
            req = urllib.request.Request(REPO_API_URL, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=5) as response:
                data = json.loads(response.read().decode())
                latest_version = data.get("tag_name", "")
                release_url = data.get("html_url", "")
                
                assets = data.get("assets", [])
                download_url = release_url
                for asset in assets:
                    if asset["name"].endswith(".exe") or asset["name"].endswith(".zip"):
                        download_url = asset["browser_download_url"]
                        break
                
                if latest_version and latest_version != VERSION:
                    msg = self.T("msg_update_avail").format(latest_version, VERSION)
                    if messagebox.askyesno("Update", msg):
                        webbrowser.open(download_url)
                else:
                    if manual_check:
                        messagebox.showinfo("Update", self.T("msg_latest").format(VERSION))
        except Exception as e:
            if manual_check: messagebox.showerror(self.T("pop_error"), f"Update check failed.\n{e}")

    def show_cookies_guide(self):
        guide_win = tk.Toplevel(self.root)
        guide_win.title("Hướng dẫn & Cookies")
        guide_win.geometry("700x700")
        scroll = ttk.Scrollbar(guide_win)
        scroll.pack(side="right", fill="y")
        txt = tk.Text(guide_win, font=("Segoe UI", 10), padx=15, pady=15, wrap="word", yscrollcommand=scroll.set)
        txt.pack(fill="both", expand=True)
        scroll.config(command=txt.yview)

        txt.tag_config("title", font=("Segoe UI", 14, "bold"), foreground="#d32f2f", spacing1=10, spacing3=10)
        txt.tag_config("header", font=("Segoe UI", 11, "bold"), foreground="#1976d2", spacing1=5)
        txt.tag_config("important", font=("Segoe UI", 10, "bold"), foreground="#e65100")
        txt.tag_config("normal", font=("Segoe UI", 10))

        txt.insert(tk.END, "HƯỚNG DẪN SỬ DỤNG / USER GUIDE\n", "title")
        
        txt.insert(tk.END, "1. FACEBOOK / INSTAGRAM / THREADS:\n", "header")
        txt.insert(tk.END, "- Các nền tảng này thường rất gắt gao.\n- Nếu tải lỗi, hãy thử dùng Cookies.\n- Đối với Facebook/Insta, nếu video riêng tư, ", "normal")
        txt.insert(tk.END, "BẮT BUỘC phải nạp Cookies.\n\n", "important")

        txt.insert(tk.END, "2. TWITCASTING / BILIBILI:\n", "header")
        txt.insert(tk.END, "- TwitCasting thường chỉ có 1 file gốc. \n- Nếu chọn độ phân giải thấp (360p) mà không có, App sẽ ", "normal")
        txt.insert(tk.END, "TỰ ĐỘNG tải bản tốt nhất (Best).\n\n", "important")

        txt.insert(tk.END, "3. CÁCH LẤY COOKIES (QUAN TRỌNG):\n", "header")
        txt.insert(tk.END, "B1: Cài tiện ích 'Get cookies.txt LOCALLY' trên trình duyệt Chrome/Edge.\n", "normal")
        txt.insert(tk.END, "B2: Vào trang (YouTube, Facebook...), đăng nhập tài khoản.\n", "normal")
        txt.insert(tk.END, "B3: Mở tiện ích -> Nhấn 'Export' để tải file .txt về máy.\n", "normal")
        txt.insert(tk.END, "B4: Tại App này, bấm nút 'Chọn File .txt' và chọn file vừa tải.\n\n", "normal")
        
        txt.insert(tk.END, "4. ĐỊNH DẠNG & CHẤT LƯỢNG:\n", "header")
        txt.insert(tk.END, "- Video: Hỗ trợ 4K, 2K, 1080p.\n- Audio: Tự động convert sang MP3 hoặc giữ nguyên M4A.", "normal")

        txt.config(state="disabled")

    def open_donate_link(self): webbrowser.open("https://tsufu.gitbook.io/donate/") 
    def open_update_link(self): webbrowser.open("https://github.com/tsufuwu/tsufutube_downloader")
    
    def select_folder(self):
        f = filedialog.askdirectory()
        if f: self.path_var.set(f)
    def open_save_folder(self):
        path = self.path_var.get()
        if os.path.exists(path): os.startfile(path)
    def select_cookies(self):
        f = filedialog.askopenfilename(filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")])
        if f:
            self.cookies_path_var.set(f)
            self.cookie_status.config(text="Đã chọn", fg=self.current_theme["success"])
            self.cookie_btn.config(bg="#c8e6c9")
        else:
            self.cookies_path_var.set("")
            self.cookie_status.config(text="(Chưa chọn)", fg="gray")
            self.cookie_btn.config(bg="#e0e0e0")
    
    def toggle_cut_inputs(self):
        s = 'normal' if self.cut_var.get() else 'disabled'
        self.start_chk.config(state=s)
        self.end_chk.config(state=s)
        entry_bg = self.current_theme["input_bg"] if self.cut_var.get() else "#f0f0f0"
        
        if not self.cut_var.get():
            self.start_entry.config(state='disabled', bg="#f0f0f0")
            self.end_entry.config(state='disabled', bg="#f0f0f0")
        else:
            self.start_entry.config(state='disabled' if self.start_chk_var.get() else 'normal', bg=entry_bg)
            self.end_entry.config(state='disabled' if self.end_chk_var.get() else 'normal', bg=entry_bg)

    def add_placeholder(self, entry, text):
        entry.insert(0, text)
        entry.config(fg=self.current_theme["placeholder"])
        def on_focus_in(event):
            if entry.get() == text:
                entry.delete(0, tk.END)
                entry.config(fg=self.current_theme["input_fg"])
        def on_focus_out(event):
            if not entry.get():
                entry.insert(0, text)
                entry.config(fg=self.current_theme["placeholder"])
        entry.bind("<FocusIn>", on_focus_in)
        entry.bind("<FocusOut>", on_focus_out)
    
    def paste_link(self):
        try:
            clipboard_text = self.root.clipboard_get()
            self.url_var.set(clipboard_text)
            self.start_check_link_info(clipboard_text) 
        except: pass 

    def monitor_clipboard(self):
        try:
            current_clipboard = self.root.clipboard_get()
            if current_clipboard != self.last_clipboard:
                if re.match(r'^(https?://)[^\s/$.?#].[^\s]*$', current_clipboard.strip()):
                    current_entry = self.url_var.get().strip()
                    if self.auto_paste_var.get() and current_entry != current_clipboard:
                        self.url_var.set(current_clipboard)
                        self.start_check_link_info(current_clipboard)
                
                self.last_clipboard = current_clipboard 
        except: pass
        
        current_url = self.url_var.get()
        is_downloading = self.download_btn.cget("state") == "disabled"
        if current_url:
            current_status = self.status_label.cget("text")
            if "Playlist" not in current_status and not is_downloading and not self.is_fetching_info:
                 self.status_label.config(text=self.T("status_ready"), fg=self.current_theme["accent"])
        else:
            if not is_downloading:
                self.status_label.config(text=self.T("lbl_paste_hint"), fg=self.current_theme["success"])
        
        self.root.after(1000, self.monitor_clipboard)

    def on_url_change_delayed(self, event):
        if hasattr(self, '_after_id'): self.root.after_cancel(self._after_id)
        self._after_id = self.root.after(800, lambda: self.start_check_link_info(self.url_var.get()))

    def browse_bg(self):
        f = filedialog.askopenfilename(filetypes=[("Images", "*.png;*.jpg;*.jpeg;*.gif")])
        if f: self.bg_path_var.set(f)
    def clear_bg(self): self.bg_path_var.set("")
    
    def update_background_image(self):
        path = self.settings.get("bg_image_path")
        if path and os.path.exists(path):
            try:
                img = tk.PhotoImage(file=path) 
                self.bg_image_ref = img 
                self.main_container.canvas.create_image(0, 0, image=img, anchor="nw")
            except: pass

    def on_close(self):
        if self.settings["minimize_to_tray"]:
            try:
                self.root.withdraw()
                import pystray
                from PIL import Image
                def after_click(icon, query):
                    if str(query) == "Open":
                        icon.stop()
                        self.root.after(0, self.root.deiconify)
                    elif str(query) == "Exit":
                        icon.stop()
                        self.root.destroy()
                image = Image.open(self.resource_path("icon_chuan.ico"))
                icon = pystray.Icon("Tsufutube", image, "Tsufutube Downloader", menu=pystray.Menu(
                    pystray.MenuItem("Open", after_click),
                    pystray.MenuItem("Exit", after_click)
                ))
                icon.run()
            except ImportError:
                self.root.iconify() 
        else:
            self.root.destroy()

    # --- INFO CHECKER ---
    def toggle_check_cancel(self):
        if self.is_fetching_info:
            self.cancel_fetch_event.set() 
            self.check_btn.config(text="...", state="disabled")
        else:
            self.start_check_link_info(self.url_var.get())

    def start_check_link_info(self, url):
        url = url.strip()
        if not url: return
        
        if self.is_fetching_info:
            self.cancel_fetch_event.set()
            self.root.after(200, lambda: self.start_check_link_info(url))
            return

        self.is_fetching_info = True
        self.fetched_title = "" 
        self.cancel_fetch_event.clear()
        
        self.check_btn.config(text=self.T("btn_cancel_check"), state="normal", bg="#d32f2f")
        self.info_frame.grid() 
        self.title_label.config(text=self.T("lbl_loading"), fg=self.current_theme["fg"])
        if self.thumb_image_ref:
            self.thumb_label.config(image="", text="...", bg="#333", width=1, height=1)
        else:
            self.thumb_label.config(text="Loading...", bg="gray")
        
        self.available_subtitles = {}
        self.selected_sub_langs = []
        self.sub_chk.config(text=self.T("chk_sub"))
        
        self.fetching_info_thread = threading.Thread(target=self.run_fetch_info, args=(url,), daemon=True)
        self.fetching_info_thread.start()

    def run_fetch_info(self, url):
        try:
            lazy_import_ytdlp() 
            
            ydl_opts = {
                'quiet': True, 'skip_download': True, 'noplaylist': True, 'ignoreerrors': True,
                'socket_timeout': 10,
                'http_headers': {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'Referer': 'https://www.google.com/',
                }
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                if self.cancel_fetch_event.is_set(): raise Exception("Cancelled")
                info = ydl.extract_info(url, download=False)
                if self.cancel_fetch_event.is_set(): raise Exception("Cancelled")

                if 'entries' in info: info = info['entries'][0]

                title = info.get('title', 'Unknown Title')
                self.fetched_title = title 
                
                uploader = info.get('uploader', 'Unknown')
                duration = info.get('duration_string', '??:??')
                thumbnail_url = info.get('thumbnail', None)
                
                if 'entries' in info or 'playlist' in url or 'list=' in url:
                    self.root.after(0, lambda: self.plist_chk.config(state='normal'))
                    self.root.after(0, lambda: self.status_label.config(text=self.T("status_playlist"), fg="#e65100"))
                else:
                    self.root.after(0, lambda: self.playlist_var.set(False))
                    self.root.after(0, lambda: self.plist_chk.config(state='disabled'))

                self.available_subtitles = {}
                if 'subtitles' in info: self.available_subtitles.update(info['subtitles'])
                if 'automatic_captions' in info: 
                    for code, val in info['automatic_captions'].items():
                        if code not in self.available_subtitles:
                            self.available_subtitles[code] = val

                display_text = f"{title}\nChan: {uploader} | Time: {duration}"
                self.root.after(0, lambda: self.title_label.config(text=display_text))

                if thumbnail_url:
                    try:
                        if self.cancel_fetch_event.is_set(): raise Exception("Cancelled")
                        req = urllib.request.Request(thumbnail_url, headers={'User-Agent': 'Mozilla/5.0'})
                        with urllib.request.urlopen(req, timeout=10) as u:
                            raw_data = u.read()
                        self.root.after(0, lambda: self.update_thumbnail_ui(raw_data))
                    except:
                         self.root.after(0, lambda: self.thumb_label.config(text="Err Thumb"))
                else:
                    self.root.after(0, lambda: self.thumb_label.config(text="No Thumb"))

        except Exception as e:
            msg = str(e)
            if msg == "Cancelled":
                self.root.after(0, lambda: self.title_label.config(text=self.T("status_cancel")))
            else:
                self.root.after(0, lambda: self.title_label.config(text=f"Error: {msg[:30]}...", fg="red"))
        finally:
            self.is_fetching_info = False
            self.root.after(0, lambda: self.check_btn.config(state="normal", text=self.T("btn_check"), bg=self.current_theme["accent"]))
            
            if self.sub_var.get() and self.available_subtitles:
                 self.root.after(0, self.show_subtitle_selector)

    def update_thumbnail_ui(self, raw_data):
        if HAS_PIL:
            try:
                image = Image.open(BytesIO(raw_data))
                image = image.resize((160, 90), Image.Resampling.LANCZOS)
                photo = ImageTk.PhotoImage(image)
                self.thumb_image_ref = photo 
                self.thumb_label.config(image=photo, text="", width=160, height=90)
            except: pass
        else:
            self.thumb_label.config(text="No PIL", bg="#555", fg="white")

    # --- SUBTITLES ---
    def on_sub_toggled(self):
        if not self.sub_var.get(): 
            self.sub_chk.config(text=self.T("chk_sub"))
            return

        if not self.available_subtitles:
            url = self.url_var.get()
            if url: 
                self.start_check_link_info(url)
                messagebox.showinfo(self.T("pop_success"), self.T("lbl_loading"))
            else:
                messagebox.showwarning(self.T("pop_warning"), self.T("err_no_link"))
                self.sub_var.set(False)
        else:
            self.show_subtitle_selector()

    def show_subtitle_selector(self):
        if not self.available_subtitles:
            messagebox.showinfo("Info", "No subtitles found.")
            self.sub_var.set(False)
            return

        top = tk.Toplevel(self.root)
        top.title("Subtitles")
        top.geometry("400x500")
        
        tk.Label(top, text="Select languages:", font=("Segoe UI", 10, "bold"), pady=10).pack()

        frame_container = ttk.Frame(top)
        frame_container.pack(fill="both", expand=True, padx=10, pady=5)
        
        canvas = tk.Canvas(frame_container)
        scrollbar = ttk.Scrollbar(frame_container, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas)

        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        self.sub_check_vars = {}
        priority = ['vi', 'en', 'ja', 'ko', 'zh']
        sorted_keys = sorted(self.available_subtitles.keys(), key=lambda x: (x not in priority, x))

        for lang_code in sorted_keys:
            subs = self.available_subtitles[lang_code]
            lang_name = subs[0].get('name', lang_code) if subs else lang_code
            display_str = f"[{lang_code}] {lang_name}"
            var = tk.BooleanVar(value=(lang_code in self.selected_sub_langs))
            self.sub_check_vars[lang_code] = var
            tk.Checkbutton(scrollable_frame, text=display_str, variable=var, anchor="w").pack(fill="x", padx=5)

        def confirm_selection():
            self.selected_sub_langs = [code for code, var in self.sub_check_vars.items() if var.get()]
            count = len(self.selected_sub_langs)
            if count > 0:
                self.sub_chk.config(text=self.T("chk_sub_count").format(count))
            else:
                self.sub_var.set(False)
                self.sub_chk.config(text=self.T("chk_sub"))
            top.destroy()

        tk.Button(top, text="OK", command=confirm_selection, bg=self.current_theme["accent"], fg="white").pack(pady=10)


    # --- DOWNLOAD CORE ---
    def add_to_queue(self):
        url = self.url_var.get().strip()
        if not url: return
        
        display_title = self.fetched_title if self.fetched_title else "Checking info..."
        
        self.download_queue.append({
            "url": url, 
            "title": display_title,
            "is_plist": self.playlist_var.get(), 
            "name": self.name_var.get().strip(),
            "subs": list(self.selected_sub_langs)
        })
        self.queue_tree.insert("", tk.END, values=(display_title, url))
        
        if self.auto_clear_var.get():
            self.url_var.set("")
            self.fetched_title = "" 
            if self.thumb_image_ref:
                self.thumb_label.config(image="", text="...", bg="#333", width=1, height=1) 
                self.thumb_image_ref = None
            self.info_frame.grid_remove() 
            
        self.name_var.set("")
        self.status_label.config(text="Added to queue!", fg=self.current_theme["accent"])

    def remove_from_queue(self):
        selected = self.queue_tree.selection()
        for item in selected:
            idx = self.queue_tree.index(item)
            self.download_queue.pop(idx)
            self.queue_tree.delete(item)

    def cancel_download(self):
        if messagebox.askyesno(self.T("pop_confirm"), self.T("msg_stop_dl")):
            self.is_cancelled = True
            self.status_label.config(text=self.T("status_cancel"), fg="red")
            self.cancel_btn.config(state="disabled")

    def start_download_thread(self):
        self.is_cancelled = False
        self.download_btn.config(state="disabled", text="STARTING...", bg="#7f8c8d") 
        self.cancel_btn.config(state="normal", bg="#d32f2f")
        threading.Thread(target=self.run_download_queue, daemon=True).start()

    def run_download_queue(self):
        try: 
            lazy_import_ytdlp()
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror(self.T("pop_error"), str(e)))
            self.root.after(0, lambda: self.reset_ui())
            return

        tasks = list(self.download_queue) if self.download_queue else [{
            "url": self.url_var.get().strip(), 
            "is_plist": self.playlist_var.get(), 
            "name": self.name_var.get().strip(),
            "subs": list(self.selected_sub_langs)
        }]
        
        if not tasks[0]["url"]:
            self.root.after(0, lambda: self.reset_ui())
            return

        success_count = 0
        fail_count = 0
        failed_links = []
        
        self.root.after(0, lambda: self.download_btn.config(text=self.T("status_downloading")))

        for task in tasks:
            if self.is_cancelled: break
            is_success, msg = self.run_single_download(task)
            if self.is_cancelled: break
            if is_success: success_count += 1
            else:
                fail_count += 1
                failed_links.append(f"{task['url']} -> {msg}")
            
            if self.download_queue:
                self.download_queue.pop(0)
                self.root.after(0, lambda: self.queue_tree.delete(self.queue_tree.get_children()[0]))
        
        self.root.after(0, lambda: self.reset_ui())
        if self.is_cancelled:
            self.root.after(0, lambda: self.status_label.config(text=self.T("status_cancel"), fg="red"))
            self.root.after(0, lambda: self.progress_var.set(0))
        elif fail_count == 0:
            if self.show_popup_var.get():
                self.root.after(0, lambda: messagebox.showinfo(self.T("pop_success"), self.T("msg_all_done").format(success_count)))
            
            self.root.after(0, lambda: self.status_label.config(text=self.T("status_done"), fg=self.current_theme["success"]))
        else:
             err_details = "\n".join(failed_links)
             msg_txt = self.T("msg_partial_done").format(success_count, fail_count)
             self.root.after(0, lambda: messagebox.showwarning(self.T("pop_warning"), f"{msg_txt}\n{err_details}"))

    def run_single_download(self, task):
        url = task["url"]
        is_playlist = task["is_plist"]
        custom_name = task["name"]
        selected_subs = task.get("subs", [])

        if not os.path.exists(self.ffmpeg_path): return False, self.T("err_no_ffmpeg")

        save_path = self.path_var.get()
        dtype = self.type_var.get()
        is_cutting = self.cut_var.get()
        cookies = self.cookies_path_var.get()
        
        pref_vid_ext = self.settings.get("default_video_ext", "mp4")
        pref_aud_ext = self.settings.get("default_audio_ext", "mp3")
        pref_codec = self.settings.get("video_codec_priority", "auto")
        do_meta = self.settings.get("add_metadata", False)
        do_embed_thumb = self.settings.get("embed_thumbnail", False)

        final_tmpl = custom_name if custom_name else '%(title)s'
        if is_cutting: final_tmpl += " (Cut)"
        if is_playlist and custom_name: final_tmpl += " - %(playlist_index)s"
        
        ydl_opts = {
            'outtmpl': os.path.join(save_path, f'{final_tmpl}.%(ext)s'),
            'progress_hooks': [self.progress_hook],
            'postprocessor_hooks': [self.post_processor_hook], 
            'noplaylist': not is_playlist,
            'force_overwrites': True, 
            'ignoreerrors': True if is_playlist else False,
            'socket_timeout': 30,
            'ffmpeg_location': self.ffmpeg_path,
            'writethumbnail': do_embed_thumb,
            'addmetadata': do_meta,
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Referer': 'https://www.google.com/',
            }
        }
        
        if cookies and os.path.exists(cookies): ydl_opts['cookiefile'] = cookies

        if is_cutting:
            start = 0 if self.start_chk_var.get() else self.time_to_seconds(self.start_entry.get())
            end = float('inf') if self.end_chk_var.get() else self.time_to_seconds(self.end_entry.get())
            ydl_opts['download_ranges'] = yt_dlp.utils.download_range_func(None, [(start, end)])
            ydl_opts['force_keyframes_at_cuts'] = True 

        # AUDIO
        if "audio" in dtype:
            target_ext = "m4a" 
            quality = "192"
            
            if dtype == "audio_mp3": target_ext = "mp3"
            elif dtype == "audio_lossless": 
                if pref_aud_ext in ["flac", "wav", "aiff"]: target_ext = pref_aud_ext
                else: target_ext = "flac" 
                quality = "0" 

            ydl_opts['format'] = 'bestaudio/best'
            pp = [{'key': 'FFmpegExtractAudio', 'preferredcodec': target_ext}]
            
            if target_ext in ['mp3', 'm4a', 'ogg', 'opus']:
                pp[0]['preferredquality'] = quality
                
            if do_embed_thumb: pp.append({'key': 'EmbedThumbnail'})
            if do_meta: pp.append({'key': 'FFmpegMetadata'})
            
            ydl_opts['postprocessors'] = pp

        # VIDEO
        else:
            if self.sub_var.get():
                ydl_opts.update({'writesubtitles': True, 'writeautomaticsub': True})
                if selected_subs: ydl_opts['subtitleslangs'] = selected_subs
                else: ydl_opts['subtitleslangs'] = ['all']
                if pref_vid_ext in ["mkv", "mp4"]: ydl_opts['embedsub'] = True

            if self.keep_audio_var.get() or self.keep_video_var.get(): 
                ydl_opts['keepvideo'] = True
            
            pp_vid = []
            if do_embed_thumb and pref_vid_ext in ['mp4', 'mkv']: 
                pp_vid.append({'key': 'EmbedThumbnail'})
            
            if do_meta: pp_vid.append({'key': 'FFmpegMetadata'})
            if pp_vid: ydl_opts['postprocessors'] = pp_vid

            limit = 1080 
            if dtype == "video_4k": limit = 2160
            elif dtype == "video_2k": limit = 1440
            elif dtype == "video_720": limit = 720
            elif dtype == "video_480": limit = 480
            elif dtype == "video_360": limit = 360
            elif dtype == "video_240": limit = 240
            elif dtype == "video_144": limit = 144

            codec_filter = ""
            if pref_codec == "h264": codec_filter = "[vcodec^=avc1]"
            elif pref_codec == "av1": codec_filter = "[vcodec!=avc1]" 
            
            audio_pref = "bestaudio"
            if pref_vid_ext == "mp4": audio_pref = "bestaudio[ext=m4a]"

            fmt_str = f'bestvideo[height<={limit}]{codec_filter}+{audio_pref}/bestvideo[height<={limit}]+bestaudio/best[height<={limit}]'
            
            ydl_opts['format'] = fmt_str
            ydl_opts['merge_output_format'] = pref_vid_ext

        # EXECUTE
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                self._run_dl(ydl, url, save_path)
                return True, "Success"

        except Exception as e:
            if self.is_cancelled: return False, "Cancelled"
            err_str = str(e)
            
            print(f"Initial download failed: {err_str}. Retrying with BEST...")
            try:
                ydl_opts['format'] = 'best' 
                if "facebook.com" in url or "instagram.com" in url or "threads.net" in url:
                     ydl_opts['format'] = 'bestvideo+bestaudio/best'

                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    self._run_dl(ydl, url, save_path)
                return True, "Success (Fallback)"
            except Exception as e2:
                if "ffmpeg" in str(e2).lower(): return False, "FFmpeg error."
                elif "Sign in" in str(e2): return False, "Blocked (Needs Cookies)."
                return False, f"Err: {str(e2)[:50]}..."

    def _run_dl(self, ydl, url, save_path):
        info = ydl.extract_info(url, download=True)
        
        final_path = None
        if 'requested_downloads' in info:
            final_path = info['requested_downloads'][0].get('filepath')
        
        if not final_path:
            final_path = ydl.prepare_filename(info)
            base, ext = os.path.splitext(final_path)
            if not os.path.exists(final_path):
                for e in ['.mp4', '.mkv', '.webm', '.mp3', '.m4a']:
                    if os.path.exists(base + e):
                        final_path = base + e
                        break

        if final_path and os.path.exists(final_path):
            file_size_mb = os.path.getsize(final_path) / (1024 * 1024)
            platform_name = info.get('extractor_key', 'Web').replace('Tab', '')
            
            history_item = {
                "platform": platform_name,
                "title": info.get('title', os.path.basename(final_path)),
                "path": final_path,
                "size": f"{file_size_mb:.1f} MB",
                "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "_checked": False 
            }
            self.root.after(0, lambda: self.add_to_history(history_item))

            if self.open_finished_var.get() and not self.is_cancelled:
                try: os.startfile(final_path)
                except: pass

    def reset_ui(self):
        self.download_btn.config(state="normal", text=self.T("btn_download"), bg=self.current_theme["accent"])
        self.cancel_btn.config(state="disabled", bg="gray")

    def time_to_seconds(self, t):
        try:
            p = list(map(int, t.split(':')))
            if len(p)==3: return p[0]*3600+p[1]*60+p[2]
            if len(p)==2: return p[0]*60+p[1]
            return p[0]
        except: return 0

    def progress_hook(self, d):
        if self.is_cancelled: raise yt_dlp.utils.DownloadError("Cancelled")
        if d['status'] == 'downloading':
            current_time = time.time()
            if current_time - self.last_update_time < 0.1: return
            self.last_update_time = current_time
            total = d.get('total_bytes') or d.get('total_bytes_estimate')
            down = d.get('downloaded_bytes', 0)
            if total:
                per = (down/total)*100
                eta = d.get('eta', '?')
                msg = f"{per:.1f}% | ETA: {eta}s"
                self.root.after(0, lambda: self.progress_var.set(per))
                self.root.after(0, lambda: self.status_label.config(text=msg, fg=self.current_theme["accent"]))
        elif d['status'] == 'finished':
            self.root.after(0, lambda: self.progress_var.set(100))
    
    def post_processor_hook(self, d):
        if self.is_cancelled: raise yt_dlp.utils.DownloadError("Cancelled")
        if d['status'] == 'started':
            self.root.after(0, lambda: self.status_label.config(text=self.T("status_processing"), fg="#e65100"))

if __name__ == "__main__":
    try: ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("tsufu.tsufutube.downloader")
    except: pass

    root = tk.Tk()
    root.withdraw()
    try: root.tk.call("tk", "scaling", 1.25)
    except: pass
    
    try:
        icon = tk.PhotoImage(file="icon_chuan.png")
        root.iconphoto(True, icon)
    except: pass

    app = YoutubeDownloaderApp(root)
    root.deiconify()
    root.mainloop()