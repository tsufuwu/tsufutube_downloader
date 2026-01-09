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
from io import BytesIO 

# Thử import PIL
HAS_PIL = False
try:
    from PIL import Image, ImageTk
    HAS_PIL = True
except ImportError:
    pass

# --- CONFIG & CONSTANTS ---
APP_TITLE = "Tsufutube Downloader Pro" 
VERSION = "v3.3.2" # Đã cập nhật phiên bản fix lỗi
REPO_API_URL = "https://api.github.com/repos/tsufuwu/tsufutube_downloader/releases/latest"

# --- TỪ ĐIỂN NGÔN NGỮ (LANGUAGE DICTIONARY) ---
TRANSLATIONS = {
    "vi": {
        "tab_home": "Trang Chủ",
        "tab_settings": "Cài đặt",
        "info_source": " Thông tin nguồn ",
        "lbl_link": "Link Video/Nhạc:",
        "btn_paste": "📋 Dán",
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
        "lbl_paste_hint": "Hãy dán link vào ô trên để bắt đầu...",
        "btn_download": "TẢI VỀ NGAY",
        "btn_cancel": "✖ HỦY BỎ",
        "set_title": "Cài đặt hệ thống",
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
    },
    "en": {
        "tab_home": "Home",
        "tab_settings": "Settings",
        "info_source": " Source Info ",
        "lbl_link": "Video/Music Link:",
        "btn_paste": "📋 Paste",
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
        "lbl_paste_hint": "Paste a link above to start...",
        "btn_download": "DOWNLOAD NOW",
        "btn_cancel": "✖ CANCEL",
        "set_title": "System Settings",
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

# --- CLASS TOOLTIP ---
class CreateToolTip(object):
    def __init__(self, widget, text='widget info'):
        self.waittime = 500     
        self.wraplength = 400
        self.widget = widget
        self.text = text
        self.widget.bind("<Enter>", self.enter)
        self.widget.bind("<Leave>", self.leave)
        self.widget.bind("<ButtonPress>", self.leave)
        self.id = None
        self.tw = None

    def enter(self, event=None):
        self.schedule()
    def leave(self, event=None):
        self.unschedule()
        self.hidetip()
    def schedule(self):
        self.unschedule()
        self.id = self.widget.after(self.waittime, self.showtip)
    def unschedule(self):
        id = self.id
        self.id = None
        if id: self.widget.after_cancel(id)
    def showtip(self, event=None):
        x = y = 0
        x, y, cx, cy = self.widget.bbox("insert")
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 20
        self.tw = tk.Toplevel(self.widget)
        self.tw.wm_overrideredirect(True)
        self.tw.wm_geometry("+%d+%d" % (x, y))
        label = tk.Label(self.tw, text=self.text, justify='left',
                       background="#ffffe0", relief='solid', borderwidth=1,
                       wraplength = self.wraplength, font=("Segoe UI", 9))
        label.pack(ipadx=5, ipady=3)
    def hidetip(self):
        tw = self.tw
        self.tw= None
        if tw: tw.destroy()

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
        app_height = 820
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
        self.load_settings()
        self.current_theme = THEMES[self.settings["theme"]]
        
        # State Variables
        self.lang = "vi" # Mặc định Tiếng Việt
        self.last_update_time = 0 
        self.download_queue = []
        self.cookies_path_var = tk.StringVar(value="")
        self.is_cancelled = False
        self.last_clipboard = ""
        self.bg_image_ref = None
        self.thumb_image_ref = None 
        
        # Biến lưu trữ thông tin tạm
        self.fetched_title = "" 
        self.is_fetching_info = False
        self.cancel_fetch_event = threading.Event()
        self.available_subtitles = {}
        self.selected_sub_langs = []

        self.style = ttk.Style()
        self.style.theme_use('clam')
        self.apply_theme_colors()
        self.ffmpeg_path = self.resource_path("ffmpeg.exe")
        
        # Variables for UI persistence
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
        
        # --- CÁC BIẾN CÀI ĐẶT (QUAN TRỌNG) ---
        # Sử dụng .get() để tránh KeyError nếu file cũ thiếu key
        self.theme_var = tk.StringVar(value=self.settings.get("theme", "Dark"))
        self.tray_var = tk.BooleanVar(value=self.settings.get("minimize_to_tray", False))
        self.bg_path_var = tk.StringVar(value=self.settings.get("bg_image_path", ""))
        self.auto_clear_var = tk.BooleanVar(value=self.settings.get("auto_clear_link", True))
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
        self.tab_settings = tk.Frame(self.notebook, bg=self.current_theme["bg"])
        
        self.setup_tabs()
        
        self.update_background_image()
        self.monitor_clipboard()
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        threading.Thread(target=self.check_for_updates, args=(False,), daemon=True).start()

    def T(self, key):
        """Helper để lấy text theo ngôn ngữ hiện tại"""
        return TRANSLATIONS.get(self.lang, TRANSLATIONS["en"]).get(key, key)

    def toggle_language(self):
        self.lang = "en" if self.lang == "vi" else "vi"
        # Re-render UI
        self.setup_tabs()
        self.update_background_image() # Re-draw BG
        # Update title text if fetching
        if self.is_fetching_info:
            self.title_label.config(text=self.T("lbl_loading"))

    def setup_tabs(self):
        # Clear old tabs
        for widget in self.tab_home.winfo_children(): widget.destroy()
        for widget in self.tab_settings.winfo_children(): widget.destroy()
        
        # Add tabs back
        if not self.notebook.tabs():
            self.notebook.add(self.tab_home, text="")
            self.notebook.add(self.tab_settings, text="")
        
        self.notebook.tab(0, text=self.T("tab_home"))
        self.notebook.tab(1, text=self.T("tab_settings"))

        self.setup_home_tab()
        self.setup_settings_tab()
        self.toggle_cut_inputs() # Reset state

    def load_settings(self):
        # [CẬP NHẬT] Mặc định mới theo yêu cầu: Dark mode, tắt metadata/thumb, audio mp3
        default = {
            "theme": "Dark", 
            "minimize_to_tray": False, 
            "bg_image_path": "",
            "auto_clear_link": True,       
            "show_finished_popup": True,
            "default_video_ext": "mp4",
            "default_audio_ext": "mp3", 
            "video_codec_priority": "auto",
            "add_metadata": False,     # Mặc định tắt để tránh lỗi FFmpeg
            "embed_thumbnail": False   # Mặc định tắt để tránh lỗi FFmpeg
        }
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, "r", encoding="utf-8") as f:
                    self.settings = json.load(f)
                    for k, v in default.items(): self.settings.setdefault(k, v)
            else: self.settings = default
        except: self.settings = default

    def save_settings(self):
        self.settings["theme"] = self.theme_var.get()
        self.settings["minimize_to_tray"] = self.tray_var.get()
        self.settings["bg_image_path"] = self.bg_path_var.get()
        self.settings["auto_clear_link"] = self.auto_clear_var.get()
        self.settings["show_finished_popup"] = self.show_popup_var.get()
        # --- LƯU CẤU HÌNH MỚI ---
        self.settings["default_video_ext"] = self.video_ext_var.get()
        self.settings["default_audio_ext"] = self.audio_ext_var.get()
        self.settings["video_codec_priority"] = self.codec_var.get()
        self.settings["add_metadata"] = self.meta_var.get()
        self.settings["embed_thumbnail"] = self.thumb_embed_var.get()
        
        try:
            with open(self.settings_file, "w", encoding="utf-8") as f: json.dump(self.settings, f, ensure_ascii=False, indent=4)
            messagebox.showinfo("Thông báo", self.T("msg_saved"))
        except Exception as e: messagebox.showerror("Lỗi", str(e))

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
        header_frame.pack(pady=(5, 0), fill="x")
        
        # Nút chuyển ngôn ngữ to hơn
        lang_btn = tk.Button(header_frame, text="LANGUAGE: VI / EN", command=self.toggle_language,
                             bg=self.current_theme["frame_bg"], fg=self.current_theme["accent"],
                             font=("Segoe UI", 9, "bold"), bd=1, relief="solid", cursor="hand2", width=18)
        lang_btn.place(relx=0.95, rely=0.05, anchor="ne")

        center_box = tk.Frame(header_frame, bg=self.current_theme["bg"])
        center_box.pack(anchor="center")

        try:
            self.root.iconbitmap(self.resource_path("icon_chuan.ico"))
            self.logo_img = tk.PhotoImage(file=self.resource_path("logo.png")).subsample(3, 3)
            tk.Label(center_box, image=self.logo_img, bg=self.current_theme["bg"], bd=0).pack(side="top", pady=0)
        except: pass

        tk.Label(center_box, text=APP_TITLE, font=("Segoe UI", 22, "bold"), 
                 bg=self.current_theme["bg"], fg="#ce2d35").pack(side="top")
        
        tk.Label(center_box, text="Dev By Tsufu/ Lê Trần Trung Phú", 
                 font=("Segoe UI", 10, "italic"), bg=self.current_theme["bg"], fg="gray").pack(side="top", pady=(0, 5))

        link_frame = tk.Frame(center_box, bg=self.current_theme["bg"])
        link_frame.pack(side="top", pady=2)
        tk.Button(link_frame, text="☕ Donate", command=self.open_donate_link,
                  bg="#FFDD00", fg="black", font=("Segoe UI", 8, "bold"), bd=0, cursor="hand2", padx=10, pady=2).pack(side="left", padx=5)
        tk.Button(link_frame, text="⬇ GitHub Repo", command=self.open_update_link,
                  bg="black", fg="white", font=("Segoe UI", 8, "bold"), bd=0, cursor="hand2", padx=10, pady=2).pack(side="left", padx=5)

    def create_widgets(self):
        t = self.current_theme
        container_pad = tk.Frame(self.content_frame, bg=t["bg"])
        container_pad.pack(fill="x", padx=40)

        # KHUNG 1: NHẬP THÔNG TIN
        input_frame = tk.LabelFrame(container_pad, text=self.T("info_source"), font=("Segoe UI", 10, "bold"), 
                                    bg=t["frame_bg"], fg=t["fg"], padx=10, pady=10, bd=0, highlightthickness=1)
        input_frame.pack(fill="x", pady=5)

        tk.Label(input_frame, text=self.T("lbl_link"), bg=t["frame_bg"], fg=t["fg"], font=("Segoe UI", 10)).grid(row=0, column=0, sticky="w", pady=5)
        
        link_container = tk.Frame(input_frame, bg=t["frame_bg"])
        link_container.grid(row=0, column=1, columnspan=2, sticky="ew", padx=5, pady=5)
        
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
        self.info_frame.grid(row=1, column=0, columnspan=3, sticky="ew", padx=5, pady=(0, 10))
        if not self.is_fetching_info and not self.fetched_title:
             self.info_frame.grid_remove() 

        # --- FIX LAYOUT THUMBNAIL ---
        self.thumb_container = tk.Frame(self.info_frame, bg="black", width=160, height=90)
        self.thumb_container.pack_propagate(False) # Khóa kích thước container
        self.thumb_container.pack(side="left", padx=5, pady=5)

        self.thumb_label = tk.Label(self.thumb_container, bg="#333", fg="white", text="...", font=("Segoe UI", 8)) 
        self.thumb_label.pack(fill="both", expand=True)
        if self.thumb_image_ref: self.thumb_label.config(image=self.thumb_image_ref, text="")

        self.title_label = tk.Label(self.info_frame, text=self.fetched_title if self.fetched_title else self.T("lbl_loading"), wraplength=400, justify="left", 
                                    font=("Segoe UI", 10, "bold"), bg=t["frame_bg"], fg=t["fg"])
        self.title_label.pack(side="left", fill="both", expand=True, padx=5)

        tk.Label(input_frame, text=self.T("lbl_filename"), bg=t["frame_bg"], fg=t["fg"], font=("Segoe UI", 10)).grid(row=2, column=0, sticky="w", pady=5)
        self.name_entry = tk.Entry(input_frame, textvariable=self.name_var, font=("Segoe UI", 11), bd=1, relief="solid", bg=t["input_bg"], fg=t["input_fg"], insertbackground=t["fg"])
        self.name_entry.grid(row=2, column=1, columnspan=2, padx=5, pady=5, sticky="ew")
        
        tk.Label(input_frame, text=self.T("lbl_filename_note"), font=("Segoe UI", 9, "italic"), bg=t["frame_bg"], fg=t["placeholder"]).grid(row=3, column=1, sticky="w", padx=5)

        tk.Label(input_frame, text=self.T("lbl_save_at"), bg=t["frame_bg"], fg=t["fg"], font=("Segoe UI", 10)).grid(row=4, column=0, sticky="w", pady=5)
        self.path_entry = tk.Entry(input_frame, textvariable=self.path_var, state='readonly', font=("Segoe UI", 10), bd=1, relief="solid")
        self.path_entry.grid(row=4, column=1, padx=5, pady=5, sticky="ew")
        
        btn_frame = tk.Frame(input_frame, bg=t["frame_bg"])
        btn_frame.grid(row=4, column=2, sticky="e", padx=5)
        tk.Button(btn_frame, text=self.T("btn_browse"), command=self.select_folder, width=4, cursor="hand2").pack(side="left", padx=2)
        tk.Button(btn_frame, text=self.T("btn_open"), command=self.open_save_folder, width=6, bg=t["accent"], fg="white", bd=0, cursor="hand2").pack(side="left", padx=2)
        
        input_frame.columnconfigure(1, weight=1)

        # KHUNG 2: CẮT VIDEO
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

        # KHUNG 3: CẤU HÌNH & ĐỊNH DẠNG
        opts_frame = tk.LabelFrame(container_pad, text=self.T("grp_opts"), font=("Segoe UI", 10, "bold"), 
                                    bg=t["frame_bg"], fg=t["fg"], padx=10, pady=5, bd=0, highlightthickness=1)
        opts_frame.pack(fill="x", pady=5)

        main_opts_grid = tk.Frame(opts_frame, bg=t["frame_bg"])
        main_opts_grid.pack(fill="x", pady=5)

        # Cột trái: Định dạng
        fmt_frame = tk.Frame(main_opts_grid, bg=t["frame_bg"])
        fmt_frame.pack(side="left", fill="both", expand=True)
        
        tk.Label(fmt_frame, text=self.T("lbl_format_title"), font=("Segoe UI", 9, "bold", "underline"), bg=t["frame_bg"], fg=t["fg"]).grid(row=0, column=0, sticky="w", columnspan=2, pady=(0,8))
        
        rb_opts = {'bg': t["frame_bg"], 'fg': t["fg"], 'selectcolor': t["frame_bg"], 'activebackground': t["frame_bg"]}
        # Audio Section
        tk.Radiobutton(fmt_frame, text=self.T("opt_audio_aac"), variable=self.type_var, value="audio", **rb_opts).grid(row=1, column=0, sticky="w", pady=2)
        tk.Radiobutton(fmt_frame, text=self.T("opt_audio_mp3"), variable=self.type_var, value="audio_mp3", **rb_opts).grid(row=2, column=0, sticky="w", pady=2)
        # Lossless
        tk.Radiobutton(fmt_frame, text=self.T("opt_audio_lossless"), variable=self.type_var, value="audio_lossless", font=("Segoe UI", 9, "italic"), **rb_opts).grid(row=3, column=0, sticky="w", pady=2)
        
        # Video High Res (Tách 2K và 4K)
        r_4k = tk.Radiobutton(fmt_frame, text=self.T("opt_video_4k"), variable=self.type_var, value="video_4k", font=("Segoe UI", 9, "bold"), **rb_opts)
        r_4k.config(fg="#d32f2f")
        r_4k.grid(row=4, column=0, sticky="w", pady=2)
        
        r_2k = tk.Radiobutton(fmt_frame, text=self.T("opt_video_2k"), variable=self.type_var, value="video_2k", font=("Segoe UI", 9, "bold"), **rb_opts)
        r_2k.config(fg="#c2185b")
        r_2k.grid(row=5, column=0, sticky="w", pady=2)

        # Video Standard
        r_1080 = tk.Radiobutton(fmt_frame, text=self.T("opt_video_1080"), variable=self.type_var, value="video_1080", font=("Segoe UI", 9, "bold"), **rb_opts)
        r_1080.grid(row=6, column=0, sticky="w", pady=2)

        resolutions = [
            ("Video HD 720p", "video_720"),
            ("Video SD 480p", "video_480"),
            ("Video 360p", "video_360"),
            ("Video 240p", "video_240"), # Thêm lại
            ("Video 144p", "video_144")  # Thêm lại
        ]
        for i, (text, val) in enumerate(resolutions):
            tk.Radiobutton(fmt_frame, text=text, variable=self.type_var, value=val, **rb_opts).grid(row=1+i, column=1, sticky="w", padx=20, pady=2)

        ttk.Separator(main_opts_grid, orient="vertical").pack(side="left", fill="y", padx=20)

        # Cột phải: Chức năng khác
        sub_frame = tk.Frame(main_opts_grid, bg=t["frame_bg"])
        sub_frame.pack(side="left", fill="both", expand=True)

        tk.Label(sub_frame, text=self.T("lbl_advanced"), font=("Segoe UI", 9, "bold", "underline"), bg=t["frame_bg"], fg=t["success"]).pack(anchor="w", pady=(0,8))
        
        # Tách video/audio
        sep_row = tk.Frame(sub_frame, bg=t["frame_bg"])
        sep_row.pack(anchor="w", pady=2)
        tk.Checkbutton(sep_row, text=self.T("chk_keep_audio"), variable=self.keep_audio_var, **rb_opts).pack(side="left")
        tk.Checkbutton(sep_row, text=self.T("chk_keep_video"), variable=self.keep_video_var, **rb_opts).pack(side="left", padx=10)
        
        # Subtitles
        sub_style = rb_opts.copy()
        sub_style['fg'] = '#e65100'
        # Update text if langs selected
        sub_txt = self.T("chk_sub")
        if self.selected_sub_langs: sub_txt = self.T("chk_sub_count").format(len(self.selected_sub_langs))
        
        self.sub_chk = tk.Checkbutton(sub_frame, text=sub_txt, variable=self.sub_var, command=self.on_sub_toggled, **sub_style)
        self.sub_chk.pack(anchor="w", pady=2)
        
        # Playlist
        self.plist_chk = tk.Checkbutton(sub_frame, text=self.T("chk_playlist"), variable=self.playlist_var, **sub_style)
        self.plist_chk.pack(anchor="w", pady=2)
        
        # Auto open
        open_style = rb_opts.copy()
        open_style['fg'] = '#d32f2f'
        tk.Checkbutton(sub_frame, text=self.T("chk_open_done"), variable=self.open_finished_var, **open_style).pack(anchor="w", pady=2)

        # Cookies
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

        # Treeview
        self.queue_tree = ttk.Treeview(queue_frame, columns=("title", "link"), show="headings", height=4) 
        self.queue_tree.heading("title", text=self.T("col_title"))
        self.queue_tree.heading("link", text=self.T("col_link"))
        self.queue_tree.column("title", width=400)
        self.queue_tree.column("link", width=300)
        self.queue_tree.pack(fill="x", pady=2)
        
        # Restore queue view
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

    # --- TAB 2: SETTINGS UI ---
    def setup_settings_tab(self):
        t = self.current_theme
        frame = tk.Frame(self.tab_settings, bg=t["bg"], padx=40, pady=20)
        frame.pack(fill="both", expand=True)
        
        tk.Label(frame, text=self.T("set_title"), font=("Segoe UI", 18, "bold"), bg=t["bg"], fg=t["fg"]).pack(anchor="w", pady=(0, 15))

        # --- GROUP 1: GIAO DIỆN & HỆ THỐNG ---
        group_ui = tk.LabelFrame(frame, text=" Giao diện & Hệ thống ", font=("Segoe UI", 10, "bold"), bg=t["bg"], fg=t["accent"], bd=1, relief="solid")
        group_ui.pack(fill="x", pady=(0, 10), ipadx=10, ipady=5)

        # Theme & Background
        row_1 = tk.Frame(group_ui, bg=t["bg"])
        row_1.pack(fill="x", pady=2)
        tk.Label(row_1, text=self.T("set_theme"), bg=t["bg"], fg=t["fg"]).pack(side="left")
        ttk.Combobox(row_1, textvariable=self.theme_var, values=["Light", "Dark"], state="readonly", width=10).pack(side="left", padx=10)
        
        tk.Label(row_1, text=self.T("set_bg"), bg=t["bg"], fg=t["fg"]).pack(side="left", padx=(20,5))
        tk.Entry(row_1, textvariable=self.bg_path_var, width=20, bg=t["input_bg"], fg=t["input_fg"]).pack(side="left")
        tk.Button(row_1, text="...", command=self.browse_bg, width=3).pack(side="left", padx=2)
        tk.Button(row_1, text="X", command=self.clear_bg, width=3).pack(side="left", padx=2)

        # Checkboxes System
        chk_opts = {'bg': t["bg"], 'fg': t["fg"], 'selectcolor': t["bg"], 'activebackground': t["bg"], 'font': ("Segoe UI", 9)}
        row_2 = tk.Frame(group_ui, bg=t["bg"])
        row_2.pack(fill="x", pady=2)
        tk.Checkbutton(row_2, text=self.T("chk_tray"), variable=self.tray_var, **chk_opts).pack(side="left")
        tk.Checkbutton(row_2, text="Auto clear Link", variable=self.auto_clear_var, **chk_opts).pack(side="left", padx=15)
        tk.Checkbutton(row_2, text="Popup Done", variable=self.show_popup_var, **chk_opts).pack(side="left", padx=15)

        # --- GROUP 2: CẤU HÌNH FFMPEG (MỚI) ---
        group_fmt = tk.LabelFrame(frame, text=self.T("grp_fmt_setting"), font=("Segoe UI", 10, "bold"), bg=t["bg"], fg="#e65100", bd=1, relief="solid")
        group_fmt.pack(fill="x", pady=(0, 15), ipadx=10, ipady=5)
        
        # Row 1: Container
        fmt_row = tk.Frame(group_fmt, bg=t["bg"])
        fmt_row.pack(fill="x", pady=5)
        
        # Video Container
        tk.Label(fmt_row, text=self.T("lbl_video_ext"), bg=t["bg"], fg=t["fg"], font=("Segoe UI", 9, "bold")).grid(row=0, column=0, sticky="w", padx=5)
        vid_cbo = ttk.Combobox(fmt_row, textvariable=self.video_ext_var, values=["mp4", "mkv", "webm", "avi", "mov"], state="readonly", width=8)
        vid_cbo.grid(row=0, column=1, sticky="w", padx=5)
        
        # Audio Format
        tk.Label(fmt_row, text=self.T("lbl_audio_ext"), bg=t["bg"], fg=t["fg"], font=("Segoe UI", 9, "bold")).grid(row=0, column=2, sticky="w", padx=(20, 5))
        aud_cbo = ttk.Combobox(fmt_row, textvariable=self.audio_ext_var, values=["mp3", "m4a", "flac", "wav", "ogg", "opus"], state="readonly", width=8)
        aud_cbo.grid(row=0, column=3, sticky="w", padx=5)

        # Row 2: Codec Priority
        codec_row = tk.Frame(group_fmt, bg=t["bg"])
        codec_row.pack(fill="x", pady=5)
        tk.Label(codec_row, text=self.T("lbl_video_codec"), bg=t["bg"], fg=t["fg"], font=("Segoe UI", 9, "bold")).pack(side="left", padx=5)
        
        codecs = {
            self.T("val_codec_auto"): "auto",
            self.T("val_codec_h264"): "h264",
            self.T("val_codec_av1"): "av1"
        }
        # Đảo ngược dict để lấy values cho combobox
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

        # Row 3: Metadata & Thumbnail
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
                
                if latest_version and latest_version != VERSION:
                    msg = f"New version available: {latest_version}\nCurrent: {VERSION}\n\nDownload now?"
                    if messagebox.askyesno("Update", msg):
                        webbrowser.open(release_url)
                else:
                    if manual_check:
                        messagebox.showinfo("Update", f"You are using the latest version ({VERSION}).")
        except Exception as e:
            if manual_check: messagebox.showerror("Error", f"Update check failed.\n{e}")

    def show_cookies_guide(self):
        guide_win = tk.Toplevel(self.root)
        guide_win.title("Hướng dẫn & Cookies")
        guide_win.geometry("680x700")
        scroll = ttk.Scrollbar(guide_win)
        scroll.pack(side="right", fill="y")
        txt = tk.Text(guide_win, font=("Segoe UI", 10), padx=15, pady=15, wrap="word", yscrollcommand=scroll.set)
        txt.pack(fill="both", expand=True)
        scroll.config(command=txt.yview)

        # [CẬP NHẬT] Hướng dẫn chi tiết hơn
        guide_content = """
        ==================================================
        HƯỚNG DẪN SỬ DỤNG (VIETNAMESE)
        ==================================================
        1. TỰ ĐỘNG LẤY TIN: 
           - Bạn chỉ cần dán Link (YouTube, SoundCloud...) vào ô Link.
           - App sẽ tự động tải tên bài hát và ảnh bìa.

        2. ĐỊNH DẠNG & CHẤT LƯỢNG:
           - Video: Hỗ trợ tách biệt 4K, 2K, 1080p và các mức thấp hơn (480p/360p).
           - Audio AAC: Tải file nhạc nhẹ (m4a) chuẩn gốc của YouTube.
           - Audio MP3: Tải và tự động chuyển đổi sang MP3.
           - Audio Lossless: Tải file chất lượng cao nhất và chuyển sang FLAC/WAV (Cần chỉnh trong Cài đặt).

        3. CÀI ĐẶT NÂNG CAO (TAB CÀI ĐẶT):
           - Bạn có thể chỉnh đuôi video mặc định (MP4 hoặc MKV).
           - Ưu tiên Codec: H.264 (Dễ xem trên Tivi cũ) hoặc AV1 (Nét hơn trên máy tính).
           - Tắt/Bật Metadata và Thumbnail (Mặc định đã tắt để tránh lỗi).

        4. XỬ LÝ LỖI "SIGN IN" / BỊ CHẶN:
           Nếu tải bị lỗi "Sign in to confirm you're not a bot":
           B1: Cài tiện ích "Get cookies.txt LOCALLY" trên trình duyệt Chrome/Edge.
           B2: Vào trang chủ YouTube, đăng nhập tài khoản của bạn.
           B3: Mở tiện ích -> Nhấn "Export" để tải file .txt về máy.
           B4: Tại App này, bấm nút "Chọn File .txt" và chọn file vừa tải.
        
        ==================================================
        USER GUIDE (ENGLISH)
        ==================================================
        1. AUTO INFO FETCHING:
           - Just paste the link. The app automatically fetches the title & thumbnail.

        2. FORMATS:
           - Video: Separate options for 4K, 2K, 1080p, and low-res (480p/360p).
           - Audio AAC: Original compressed audio (m4a).
           - Audio MP3: Auto-converted to MP3.
           - Audio Lossless: Best quality converted to FLAC/WAV (Configurable in Settings).

        3. ADVANCED SETTINGS:
           - Default Video Container: MP4 or MKV.
           - Codec Priority: H.264 (Compatibility) or AV1 (Efficiency).
           - Metadata/Thumbnail: Disabled by default to prevent FFmpeg errors.

        4. HOW TO FIX "SIGN IN" / BLOCKED ERRORS:
           Step 1: Install "Get cookies.txt LOCALLY" extension on your browser.
           Step 2: Go to YouTube and log in.
           Step 3: Open extension -> Click "Export" to save the .txt file.
           Step 4: In this App, click "Select .txt File" and load it.
        """
        txt.insert(tk.END, guide_content)
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
                    if not current_entry or current_entry == self.last_clipboard:
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
        self.fetched_title = "" # Reset title
        self.cancel_fetch_event.clear()
        
        self.check_btn.config(text=self.T("btn_cancel_check"), state="normal", bg="#d32f2f")
        self.info_frame.grid() 
        self.title_label.config(text=self.T("lbl_loading"), fg=self.current_theme["fg"])
        # RESET THUMB UI
        if self.thumb_image_ref:
            self.thumb_label.config(image="", text="Loading...", bg="gray")
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
                'socket_timeout': 10 
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                if self.cancel_fetch_event.is_set(): raise Exception("Cancelled")
                info = ydl.extract_info(url, download=False)
                if self.cancel_fetch_event.is_set(): raise Exception("Cancelled")

                if 'entries' in info: info = info['entries'][0]

                title = info.get('title', 'Unknown Title')
                self.fetched_title = title # Store for queue
                
                uploader = info.get('uploader', 'Unknown')
                duration = info.get('duration_string', '??:??')
                thumbnail_url = info.get('thumbnail', None)
                
                if 'entries' in info or 'playlist' in url or 'list=' in url:
                    self.root.after(0, lambda: self.plist_chk.config(state='normal'))
                    self.root.after(0, lambda: self.status_label.config(text=self.T("status_playlist"), fg="#e65100"))
                else:
                    self.root.after(0, lambda: self.playlist_var.set(False))
                    self.root.after(0, lambda: self.plist_chk.config(state='disabled'))

                # Subtitles
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

    # --- SUBTITLE SELECTOR ---
    def on_sub_toggled(self):
        if not self.sub_var.get(): 
            self.sub_chk.config(text=self.T("chk_sub"))
            return

        if not self.available_subtitles:
            url = self.url_var.get()
            if url: 
                self.start_check_link_info(url)
                messagebox.showinfo("Info", self.T("lbl_loading"))
            else:
                messagebox.showwarning("Warning", self.T("err_no_link"))
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
        
        # Lấy tên hiển thị: Nếu đã load xong thì dùng fetched_title, không thì dùng "Đang chờ..."
        display_title = self.fetched_title if self.fetched_title else "Checking info..."
        
        self.download_queue.append({
            "url": url, 
            "title": display_title,
            "is_plist": self.playlist_var.get(), 
            "name": self.name_var.get().strip(),
            "subs": list(self.selected_sub_langs)
        })
        self.queue_tree.insert("", tk.END, values=(display_title, url))
        
        # LOGIC TỰ ĐỘNG XÓA LINK
        if self.auto_clear_var.get():
            self.url_var.set("")
            self.fetched_title = "" 
            # Reset UI thumbnail về trạng thái chờ
            if self.thumb_image_ref:
                self.thumb_label.config(image="", text="...", bg="#333", width=1, height=1) 
                self.thumb_image_ref = None
            self.info_frame.grid_remove() # Ẩn khung info đi cho gọn
            
        self.name_var.set("")
        self.status_label.config(text="Added to queue!", fg=self.current_theme["accent"])

    def remove_from_queue(self):
        selected = self.queue_tree.selection()
        for item in selected:
            idx = self.queue_tree.index(item)
            self.download_queue.pop(idx)
            self.queue_tree.delete(item)

    def cancel_download(self):
        if messagebox.askyesno("Confirm", "Stop downloading?"):
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
            self.root.after(0, lambda: messagebox.showerror("Err", str(e)))
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
                self.root.after(0, lambda: messagebox.showinfo("Success", f"All {success_count} files downloaded!"))
            
            self.root.after(0, lambda: self.status_label.config(text=self.T("status_done"), fg=self.current_theme["success"]))
        else:
             err_details = "\n".join(failed_links)
             self.root.after(0, lambda: messagebox.showwarning("Partial Success", f"Done {success_count}, Fail {fail_count}.\n{err_details}"))

    def run_single_download(self, task):
        # 1. Lấy thông tin cơ bản từ task
        url = task["url"]
        is_playlist = task["is_plist"]
        custom_name = task["name"]
        selected_subs = task.get("subs", [])

        # 2. Kiểm tra FFmpeg
        if not os.path.exists(self.ffmpeg_path): return False, self.T("err_no_ffmpeg")

        # 3. Lấy các biến từ giao diện
        save_path = self.path_var.get()
        dtype = self.type_var.get()
        is_cutting = self.cut_var.get()
        cookies = self.cookies_path_var.get()
        
        # --- LOAD SETTINGS TỪ FILE CẤU HÌNH ---
        pref_vid_ext = self.settings.get("default_video_ext", "mp4")
        pref_aud_ext = self.settings.get("default_audio_ext", "mp3")
        pref_codec = self.settings.get("video_codec_priority", "auto")
        do_meta = self.settings.get("add_metadata", False)     # [QUAN TRỌNG] Mặc định False để tránh lỗi
        do_embed_thumb = self.settings.get("embed_thumbnail", False) # [QUAN TRỌNG] Mặc định False để tránh lỗi

        # 4. Xử lý tên file (Template)
        final_tmpl = custom_name if custom_name else '%(title)s'
        if is_cutting: final_tmpl += " (Cut)"
        if is_playlist and custom_name: final_tmpl += " - %(playlist_index)s"
        
        # 5. Cấu hình cơ bản cho yt-dlp
        ydl_opts = {
            'outtmpl': os.path.join(save_path, f'{final_tmpl}.%(ext)s'),
            'progress_hooks': [self.progress_hook],
            'postprocessor_hooks': [self.post_processor_hook], 
            'noplaylist': not is_playlist,
            'force_overwrites': True, 
            'ignoreerrors': True if is_playlist else False,
            'socket_timeout': 30,
            'ffmpeg_location': self.ffmpeg_path,
            'writethumbnail': do_embed_thumb, # Tự động tải thumbnail nếu bật
            'addmetadata': do_meta,           # Tự động ghi metadata nếu bật
        }
        
        if cookies and os.path.exists(cookies): ydl_opts['cookiefile'] = cookies

        # --- XỬ LÝ CẮT VIDEO ---
        if is_cutting:
            start = 0 if self.start_chk_var.get() else self.time_to_seconds(self.start_entry.get())
            end = float('inf') if self.end_chk_var.get() else self.time_to_seconds(self.end_entry.get())
            ydl_opts['download_ranges'] = yt_dlp.utils.download_range_func(None, [(start, end)])
            ydl_opts['force_keyframes_at_cuts'] = True 

        # --- LOGIC XỬ LÝ ĐỊNH DẠNG ---
        
        # A. XỬ LÝ AUDIO
        if "audio" in dtype:
            target_ext = "m4a" # Mặc định
            quality = "192"
            
            if dtype == "audio_mp3": 
                target_ext = "mp3"
            elif dtype == "audio_lossless": 
                # Logic cho Lossless: Dùng định dạng từ cài đặt (FLAC/WAV...)
                if pref_aud_ext in ["flac", "wav", "aiff"]: target_ext = pref_aud_ext
                else: target_ext = "flac" # Fallback về FLAC nếu setting đang để mp3
                quality = "0" # 0 là chất lượng tốt nhất cho VBR/Lossless
            else: # dtype == "audio" (AAC gốc)
                target_ext = "m4a"

            # Setup postprocessors chuyển đổi âm thanh
            ydl_opts['format'] = 'bestaudio/best'
            pp = [{'key': 'FFmpegExtractAudio', 'preferredcodec': target_ext}]
            
            # Chỉ set quality cho các định dạng nén
            if target_ext in ['mp3', 'm4a', 'ogg', 'opus']:
                pp[0]['preferredquality'] = quality
                
            if do_embed_thumb: pp.append({'key': 'EmbedThumbnail'})
            if do_meta: pp.append({'key': 'FFmpegMetadata'})
            
            ydl_opts['postprocessors'] = pp

        # B. XỬ LÝ VIDEO
        else:
            # Xử lý Subtitles
            if self.sub_var.get():
                ydl_opts.update({'writesubtitles': True, 'writeautomaticsub': True})
                if selected_subs: ydl_opts['subtitleslangs'] = selected_subs
                else: ydl_opts['subtitleslangs'] = ['all']
                
                # MKV và MP4 hỗ trợ nhúng sub (Embed)
                if pref_vid_ext in ["mkv", "mp4"]: ydl_opts['embedsub'] = True

            if self.keep_audio_var.get() or self.keep_video_var.get(): ydl_opts['keepvideo'] = True
            
            # Postprocessors cho Video (Embed Thumb / Meta)
            pp_vid = []
            if do_embed_thumb and pref_vid_ext in ['mp4', 'mkv']: pp_vid.append({'key': 'EmbedThumbnail'})
            if do_meta: pp_vid.append({'key': 'FFmpegMetadata'})
            if pp_vid: ydl_opts['postprocessors'] = pp_vid

            # Logic giới hạn độ phân giải (Limit Height)
            limit = 2160
            if dtype == "video_4k": limit = 2160
            elif dtype == "video_2k": limit = 1440
            elif dtype == "video_1080": limit = 1080
            elif dtype == "video_720": limit = 720
            elif dtype == "video_480": limit = 480
            elif dtype == "video_360": limit = 360
            elif dtype == "video_240": limit = 240
            elif dtype == "video_144": limit = 144

            # Logic Codec (H264 vs AV1/VP9)
            codec_filter = ""
            if pref_codec == "h264": codec_filter = "[vcodec^=avc1]"
            elif pref_codec == "av1": codec_filter = "[vcodec!=avc1]" 
            
            # Chuỗi Format Selector của yt-dlp
            fmt_str = f'bestvideo[height<={limit}]{codec_filter}+bestaudio/bestvideo[height<={limit}]+bestaudio/best[height<={limit}]'
            
            ydl_opts['format'] = fmt_str
            ydl_opts['merge_output_format'] = pref_vid_ext

        # 6. Thực hiện tải xuống
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                if not info: return False, "No Info"
                
                # Logic mở file sau khi tải
                if self.open_finished_var.get() and not self.is_cancelled:
                    # Mở thư mục chứa file
                    if os.path.exists(save_path):
                        os.startfile(save_path)

                return True, "Success"

        except Exception as e:
            if self.is_cancelled: return False, "Cancelled"
            err_str = str(e)
            
            # [FIX LỖI] Nếu file đã tải xong mà lỗi ở bước Post-Processing (Embed/Metadata)
            # thì vẫn coi là thành công để tránh báo lỗi giả.
            # Tuy nhiên, do chúng ta đã tắt Metadata/Thumb ở mặc định nên lỗi này sẽ ít gặp hơn.
            
            if "Requested format is not available" in err_str: return False, "Format/Res not found."
            elif "ffmpeg" in err_str.lower(): return False, "FFmpeg error."
            elif "Sign in" in err_str: return False, "Blocked (Needs Cookies)."
            else: return False, f"Err: {err_str[:50]}..."

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