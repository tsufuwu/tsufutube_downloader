import customtkinter as ctk
import tkinter as tk
import sys
from tkinter import ttk, messagebox, filedialog, simpledialog
import threading
import queue
import os
import json
import shutil
import re
import subprocess
from io import BytesIO
import webbrowser
from ui.widget import Tooltip  # Keeping Tooltip, removing others
from core import DownloaderEngine
from fetcher import get_fetcher
from data import THEMES, TIPS_CONTENT
from constant import APP_TITLE, APP_SLOGAN, REPO_API_URL, VERSION, APP_VERSION
from utils import resource_path, time_to_seconds, set_autostart_registry
from config import ConfigManager
from time_spinbox import TimeSpinbox
from updater import UpdateChecker, check_update_async

# Lazy Import Wrapper for Tray
HAS_PYSTRAY = False

# Initialize CustomTkinter
# ctk.set_appearance_mode("Dark") # Removed global override
ctk.set_default_color_theme("blue")

class YoutubeDownloaderApp(ctk.CTk):
    def __init__(self, root=None, start_silently=False):
        # NOTE: 'root' arg is kept for compatibility with existing launcher but ignored for CTk inheritance
        super().__init__()
        
        print("DEBUG: Initializing App (CustomTkinter Mode)...")
        self.title(f"{APP_TITLE} - {VERSION}")
        
        icon_path = resource_path(os.path.join("assets", "icon.ico"))
        if os.path.exists(icon_path):
            try:
                self.iconbitmap(icon_path)
            except:
                try: self.wm_iconbitmap(icon_path)
                except Exception as e: print(f"Warning: Could not set icon: {e}")
        else:
            print(f"Warning: Icon not found at {icon_path}")
            
        
        if start_silently:
            self.withdraw()
        
        # --- 1. MANAGER INIT ---
        self.config_mgr = ConfigManager()
        
        # Thread Safe Queue
        self.msg_queue = queue.Queue()
        self.after(100, self.process_msg_queue)
        
        default_settings = {
            "language": "en", "theme": "Dark", "minimize_to_tray": True, 
            "auto_clear_link": True, "auto_paste": True,
            "show_finished_popup": True, "default_video_ext": "mp4",
            "default_audio_ext": "mp3", "video_codec_priority": "h264",
            "add_metadata": False, "embed_thumbnail": False,
            "run_on_startup": True,
            "enable_sponsorblock": False,
            "split_chapters": False,
            "use_archive": False,
            "geo_bypass_country": "None",
            "proxy_url": "",
            "config_path": self.config_mgr.config_dir,
        }
        
        # Load settings & history
        self.settings = self.config_mgr.load_settings(default_settings)
        
        # Apply Theme Immediate
        saved_theme = self.settings.get("theme", "Dark")
        ctk.set_appearance_mode(saved_theme)
        
        self.chapter_var = tk.BooleanVar(value=self.settings.get("split_chapters", False))
        self.archive_var = tk.BooleanVar(value=self.settings.get("use_archive", True))
        self.meta_var = tk.BooleanVar(value=self.settings.get("add_metadata", False))
        
        # --- SPONSORBLOCK VARS ---
        sb_default = self.settings.get("enable_sponsorblock", False)
        self.sb_sponsor_var = tk.BooleanVar(value=self.settings.get("sb_sponsor", sb_default))
        self.sb_intro_var = tk.BooleanVar(value=self.settings.get("sb_intro", sb_default))
        self.sb_outro_var = tk.BooleanVar(value=self.settings.get("sb_outro", False))
        self.sb_selfpromo_var = tk.BooleanVar(value=self.settings.get("sb_selfpromo", False))
        self.sb_interaction_var = tk.BooleanVar(value=self.settings.get("sb_interaction", False))
        self.sb_music_off_var = tk.BooleanVar(value=self.settings.get("sb_music_offtopic", False))
        self.sb_preview_var = tk.BooleanVar(value=self.settings.get("sb_preview", False))
        self.geo_var = tk.StringVar(value=self.settings.get("geo_bypass_country", "None"))
        self.proxy_var = tk.StringVar(value=self.settings.get("proxy_url", ""))
        self.history_data = self.config_mgr.load_history()
        
        # Note: First-run language selection is now handled in main entry point (before splash)
            
        # Initialize Engine
        # [FFMPEG HYBRID CHECKS]
        # Priority 1: "Portable" folder (root/ffmpeg/)
        # This allows user to drop a portable ffmpeg folder next to the exe
        root_dir = os.path.dirname(os.path.abspath(sys.executable))
        
        # Determine executable name based on OS
        ffmpeg_exe = "ffmpeg.exe" if os.name == 'nt' else "ffmpeg"
        
        portable_ffmpeg = os.path.join(root_dir, "ffmpeg", ffmpeg_exe)
        
        # Priority 2: Bundled (PyInstaller _internal)
        bundled_ffmpeg = resource_path(os.path.join("ffmpeg", ffmpeg_exe))
        
        ffmpeg_final_path = ffmpeg_exe # Default fallback
        
        if os.path.exists(portable_ffmpeg):
            ffmpeg_final_path = portable_ffmpeg
            print(f"Info: Using PORTABLE FFmpeg at {portable_ffmpeg}")
        elif os.path.exists(bundled_ffmpeg):
            ffmpeg_final_path = bundled_ffmpeg
            print(f"Info: Using BUNDLED FFmpeg at {bundled_ffmpeg}")
        else:
            # Priority 3: System PATH
            system_ffmpeg = shutil.which("ffmpeg")
            if system_ffmpeg:
                ffmpeg_final_path = system_ffmpeg
                print(f"Info: Using SYSTEM FFmpeg at {system_ffmpeg}")
            else:
                print("Warning: FFmpeg not found!")

        self.engine = DownloaderEngine(ffmpeg_final_path)
        
        # [OPTIMIZED] Initialize FastFetcher for video info
        self.fetcher = get_fetcher()
        
        # --- 2. WINDOW CONFIG ---
        # --- 2. WINDOW CONFIG ---
        # Fallback to Safe Fixed Size since dynamic calculation is unreliable on this specific setup
        app_width = 750
        app_height = 780 # Increased by 20% from 650
        
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        
        # Simple center calculation (Horizontal only)
        x_pos = (screen_width - app_width) // 2
        
        # Position at top (User requested to avoid taskbar at bottom)
        y_pos = 50
        
        self.geometry(f"{app_width}x{app_height}+{x_pos}+{y_pos}")
        self.minsize(700, 600)

        self.current_theme = THEMES.get(self.settings["theme"], THEMES["Dark"])
        
        # --- 3. UI VARIABLES ---
        self.lang = self.settings.get("language", "vi")
        
        # [OPTIMIZED] Load Translation JSON
        try:
            locale_path = resource_path(os.path.join("assets", "locales", f"{self.lang}.json"))
            with open(locale_path, "r", encoding="utf-8") as f:
                self.translations = json.load(f)
        except Exception as e:
            print(f"Error loading locale {self.lang}: {e}")
            self.translations = {}
        self.download_queue = []
        self.cookies_path_var = tk.StringVar(value=self.settings.get("cookie_file", ""))
        self.is_cancelled = False
        self.last_clipboard = ""
        self.thumb_image_ref = None 
        
        # Fetching state
        self.fetched_title = "" 
        self.is_fetching_info = False
        self.cancel_fetch_event = threading.Event()
        self.fetch_req_id = 0 
        self.available_subtitles = {}
        self.selected_sub_langs = []
        self.selected_sub_format = "vtt"
        self.history_tree = None

        # Lazy Loading Flags
        self.is_history_loaded = False
        self.is_settings_loaded = False
        self.is_tools_loaded = False 
        
        # UI Persistence Vars
        self.url_var = tk.StringVar()
        self.name_var = tk.StringVar()
        self.path_var = tk.StringVar(value=self.settings.get("save_path", os.getcwd()))
        self.cut_var = tk.BooleanVar(value=False)
        self.start_chk_var = tk.BooleanVar(value=True)
        self.end_chk_var = tk.BooleanVar(value=True)
        self.type_var = tk.StringVar(value="video_1080")
        self.keep_audio_var = tk.BooleanVar(value=False)
        self.keep_video_var = tk.BooleanVar(value=False)
        self.sub_var = tk.BooleanVar(value=False)
        self.playlist_var = tk.BooleanVar(value=False)
        self.open_finished_var = tk.BooleanVar(value=False)
        
        # Cut Mode Var (Home Tab)
        self.cut_mode_var = tk.StringVar(value="fast") # fast / acc
        
        self.type_var.trace_add("write", self.on_type_changed)
        
        # Tool Tab Vars
        self.tool_input_var = tk.StringVar()
        self.tool_extra_var = tk.StringVar()
        self.tool_action_var = tk.StringVar(value="remux")
        self.tool_param_var = tk.StringVar(value="90")
        self.tool_out_path_var = tk.StringVar()
        
        # Tool Cut Mode Var
        self.tool_cut_mode_var = tk.StringVar(value="fast")
        self.tool_start_chk_var = tk.BooleanVar(value=True)
        self.tool_end_chk_var = tk.BooleanVar(value=True)
        
        # Settings Vars
        self.lang_var = tk.StringVar(value=self.lang)
        self.theme_var = tk.StringVar(value=self.settings.get("theme", "Dark"))
        self.tray_var = tk.BooleanVar(value=self.settings.get("minimize_to_tray", False))
        self.startup_var = tk.BooleanVar(value=self.settings.get("run_on_startup", True))
        self.auto_clear_var = tk.BooleanVar(value=self.settings.get("auto_clear_link", True))
        self.auto_paste_var = tk.BooleanVar(value=self.settings.get("auto_paste", True)) 
        self.show_popup_var = tk.BooleanVar(value=self.settings.get("show_finished_popup", True))
        self.video_ext_var = tk.StringVar(value=self.settings.get("default_video_ext", "mp4"))
        self.audio_ext_var = tk.StringVar(value=self.settings.get("default_audio_ext", "mp3"))
        self.browser_var = tk.StringVar(value=self.settings.get("browser_source", "none"))
        
        self.codec_var = tk.StringVar(value=self.settings.get("video_codec_priority", "auto"))
        self.codec_display_var = tk.StringVar(value="Auto") # Init later
        self.thumb_embed_var = tk.BooleanVar(value=self.settings.get("embed_thumbnail", False))
        self.auto_update_var = tk.BooleanVar(value=self.settings.get("auto_check_update", True))

        # --- 4. DRAW UI ---
        self.setup_tabs()
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        self.bind("<Map>", self.on_window_map)
        
        # Background Startup Tasks
        self.after(2000, self._run_background_startup_tasks)
        
        # [TRAY] Start Tray Icon if enabled (Persistent)
        if self.settings.get("minimize_to_tray", False):
            threading.Thread(target=self._run_tray_icon, daemon=True).start()

    # --- UTILS ---
    def T(self, key):
        return self.translations.get(key, f"[{key}]")

    def process_msg_queue(self):
        """Process messages from background threads (thread-safe UI updates)"""
        try:
            while not self.msg_queue.empty():
                item = self.msg_queue.get_nowait()
                
                # Case 1: Callable task (e.g. from queue_update)
                if callable(item):
                    try:
                        item()
                    except Exception as e:
                        print(f"Queue Task Error: {e}")
                    continue

                # Case 2: Tuple Message (e.g. ("tray_open", None))
                if isinstance(item, (tuple, list)) and len(item) >= 1:
                    msg_type = item[0]
                    # data = item[1] if len(item) > 1 else None
                    
                    if msg_type == "tray_open":
                        self.deiconify()
                        self.lift()
                        self.focus_force()
                    elif msg_type == "tray_exit":
                        self.quit()
                    # Add more message types as needed
                    
        except Exception as e:
            # print(f"Queue processing error: {e}")
            pass
        finally:
            # Re-schedule this check
            self.after(100, self.process_msg_queue)

    def style_treeview(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview", 
                        background="#2b2b2b", 
                        foreground="white", 
                        fieldbackground="#2b2b2b", 
                        borderwidth=0,
                        font=("Segoe UI", 10))
        style.map("Treeview", background=[('selected', '#1f538d')])
        style.configure("Treeview.Heading", 
                        background="#333333", 
                        foreground="white", 
                        relief="flat",
                        font=("Segoe UI", 10, "bold"))
        style.map("Treeview.Heading", background=[('active', '#404040')])
        
        # Force row colors
        style.configure("Treeview", 
                        background="#2b2b2b",
                        foreground="white", 
                        fieldbackground="#2b2b2b")
        style.map("Treeview", 
                  background=[('selected', '#1f538d')],
                  foreground=[('selected', 'white')])
        
        # Tag for missing files (gray, strike-through)
        if hasattr(self, 'history_tree') and self.history_tree:
            self.history_tree.tag_configure('missing', foreground='#666666', font=("Segoe UI", 10, "overstrike"))

    # --- LABELS & PANELS ---
    def setup_tabs(self):
        self.tab_view = ctk.CTkTabview(self)
        self.tab_view.pack(fill="both", expand=True, padx=20, pady=20)
        
        self.tab_view.add(self.T("tab_home"))
        self.tab_view.add(self.T("tab_history"))
        self.tab_view.add(self.T("tab_tools"))
        self.tab_view.add(self.T("tab_settings"))
        
        # Store tab names for reference if needed, but we mostly use indices or command
        self.tab_names = {
            0: self.T("tab_home"),
            1: self.T("tab_history"),
            2: self.T("tab_tools"),
            3: self.T("tab_settings")
        }
        
        self.tab_view.configure(command=self.on_tab_changed)
        
        self.setup_home_tab()
        self.setup_tools_tab()  # Load Tools tab immediately instead of lazy loading

    def on_tab_changed(self):
        selected = self.tab_view.get()
        
        if selected == self.T("tab_history") and not self.is_history_loaded:
            self.init_history_tab()
            self.is_history_loaded = True
        elif selected == self.T("tab_settings") and not self.is_settings_loaded:
            self.setup_settings_tab()
            self.is_settings_loaded = True

    # ==========================
    # TAB 1: HOME
    # ==========================
    def setup_home_tab(self):
        tab = self.tab_view.tab(self.T("tab_home"))
        
        # Branding
        self.header_frame = ctk.CTkFrame(tab, fg_color="transparent")
        self.header_frame.pack(fill="x", pady=10)
        self.after(100, self._lazy_load_branding)

        # Scrollable Main Area
        self.main_scroll = ctk.CTkScrollableFrame(tab, fg_color="transparent")
        self.main_scroll.pack(fill="both", expand=True)

        self.create_widgets(self.main_scroll)
        self.create_bottom_bar(tab)
        self.toggle_cut_inputs()
        self.monitor_clipboard()

    def _lazy_load_branding(self):
        # Clear existing
        for widget in self.header_frame.winfo_children(): widget.destroy()
        
        # Left Logo
        try:
            from PIL import Image
            logo_path = resource_path(os.path.join("assets", "logo.png"))
            if os.path.exists(logo_path):
                img = ctk.CTkImage(light_image=Image.open(logo_path), dark_image=Image.open(logo_path), size=(80, 80))
                ctk.CTkLabel(self.header_frame, image=img, text="").pack(side="left", padx=15)
        except Exception: pass
        
        # Center Title with Donate/GitHub below
        title_box = ctk.CTkFrame(self.header_frame, fg_color="transparent")
        title_box.pack(side="left", fill="x", expand=True)
        ctk.CTkLabel(title_box, text=APP_TITLE, font=("Segoe UI", 32, "bold"), text_color="#ce2d35").pack()
        ctk.CTkLabel(title_box, text=APP_SLOGAN, font=("Segoe UI", 12, "italic"), text_color="gray").pack()
        
        # Donate, GitHub, Bug Report buttons in a row below slogan
        social_row = ctk.CTkFrame(title_box, fg_color="transparent")
        social_row.pack(pady=(5, 0))
        ctk.CTkButton(social_row, text="☕ Donate", command=self.open_donate_link, height=25, fg_color="#FFDD00", text_color="black", hover_color="#FFEA00", width=70).pack(side="left", padx=2)
        ctk.CTkButton(social_row, text="⬇ GitHub", command=self.open_update_link, height=25, fg_color="black", hover_color="#333", width=70).pack(side="left", padx=2)
        ctk.CTkButton(social_row, text="🐛 Bug", command=self.show_bug_report, height=25, fg_color="#E53935", hover_color="#C62828", width=60).pack(side="left", padx=2)
        
        # Right Links: HDSD, Update, Refresh
        link_box = ctk.CTkFrame(self.header_frame, fg_color="transparent")
        link_box.pack(side="right")
        
        ctk.CTkButton(link_box, text=self.T("btn_guide"), command=self.show_user_guide, height=25, fg_color="#FF5722", hover_color="#E64A19", width=80).pack(pady=2)
        ctk.CTkButton(link_box, text=self.T("btn_check_update"), command=lambda: self.check_for_updates(manual=True), height=25, fg_color="#4CAF50", hover_color="#388E3C", width=80).pack(pady=2)
        ctk.CTkButton(link_box, text="🔄 Refresh", command=lambda: self.restart_app(save_first=True), height=25, fg_color="#009688", hover_color="#00796B", width=80).pack(pady=2)

    def create_widgets(self, parent):
        # --- INPUT CARD ---
        input_card = ctk.CTkFrame(parent)
        input_card.pack(fill="x", pady=10, padx=10)
        
        # Header Row
        row1 = ctk.CTkFrame(input_card, fg_color="transparent")
        row1.pack(fill="x", pady=(10, 5), padx=10)
        ctk.CTkLabel(row1, text=self.T("lbl_link"), font=("Segoe UI", 13, "bold")).pack(side="left")

        
        # Link Entry Row
        row_link = ctk.CTkFrame(input_card, fg_color="transparent")
        row_link.pack(fill="x", pady=5, padx=10)
        
        self.url_entry = ctk.CTkEntry(row_link, textvariable=self.url_var, placeholder_text="Paste YouTube/Facebook/Tiktok link here...", height=40)
        self.url_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.url_entry.bind('<KeyRelease>', self.on_url_change_delayed)
        
        ctk.CTkButton(row_link, text=self.T("btn_paste"), command=self.paste_link, width=60, height=40, fg_color="#424242", hover_color="#616161").pack(side="left", padx=2)
        self.check_btn = ctk.CTkButton(row_link, text=self.T("btn_check"), command=self.toggle_check_cancel, width=70, height=40)
        self.check_btn.pack(side="left", padx=2)
        
        # Cookie Status & Auto-paste Row
        opt_row = ctk.CTkFrame(input_card, fg_color="transparent")
        opt_row.pack(fill="x", padx=10, pady=(5, 0))
        
        # Cookie indicator (left)
        self.cookie_indicator = ctk.CTkFrame(opt_row, fg_color="transparent")
        self.cookie_indicator.pack(side="left")
        self.cookie_status_label = ctk.CTkLabel(self.cookie_indicator, text="🍪 Cookies: None", 
                                                font=("Segoe UI", 10), text_color="gray")
        self.cookie_status_label.pack(side="left")
        ctk.CTkButton(self.cookie_indicator, text="⚙", width=20, height=20, 
                     command=self.jump_to_cookie_settings, fg_color="transparent", 
                     hover_color="#424242").pack(side="left", padx=2)
        
        # Auto-paste checkbox (right)
        ctk.CTkCheckBox(opt_row, text=self.T("chk_auto_paste"), variable=self.auto_paste_var).pack(side="right")
        
        # Update cookie indicator
        self.update_cookie_indicator()
        
        # Info Area (Lazy load)
        self.info_frame = ctk.CTkFrame(input_card, fg_color="transparent")
        # Keep hidden initially
        
        # Thumb & Title
        self.thumb_container = ctk.CTkFrame(self.info_frame, width=160, height=90, fg_color="black")
        self.thumb_container.pack_propagate(False)
        self.thumb_container.pack(side="left")
        self.thumb_label = tk.Label(self.thumb_container, text="...", fg="gray", bg="black")
        self.thumb_label.pack(fill="both", expand=True)
        
        self.title_label = ctk.CTkLabel(self.info_frame, text=self.T("lbl_loading"), font=("Segoe UI", 12, "bold"), wraplength=450, justify="left")
        self.title_label.pack(side="left", padx=10, fill="x", expand=True)

        # Meta Grid (Filename & Path)
        meta_grid = ctk.CTkFrame(input_card, fg_color="transparent")
        meta_grid.pack(fill="x", pady=10, padx=10)
        
        ctk.CTkLabel(meta_grid, text=self.T("lbl_filename"), text_color="gray", font=("Segoe UI", 10, "bold")).grid(row=0, column=0, sticky="w")
        ctk.CTkEntry(meta_grid, textvariable=self.name_var).grid(row=1, column=0, sticky="ew", padx=(0, 10))
        
        ctk.CTkLabel(meta_grid, text=self.T("lbl_save_at"), text_color="gray", font=("Segoe UI", 10, "bold")).grid(row=0, column=1, sticky="w")
        
        path_box = ctk.CTkFrame(meta_grid, fg_color="transparent")
        path_box.grid(row=1, column=1, sticky="ew")
        ctk.CTkEntry(path_box, textvariable=self.path_var, state="readonly").pack(side="left", fill="x", expand=True)
        ctk.CTkButton(path_box, text="📂", width=30, command=self.select_folder, fg_color="#424242").pack(side="left", padx=2)
        ctk.CTkButton(path_box, text="↗", width=30, command=self.open_save_folder, fg_color="#424242").pack(side="left", padx=2)
        
        meta_grid.columnconfigure(0, weight=6)
        meta_grid.columnconfigure(1, weight=4)

        # --- CUT OPTION ---
        self.cut_card = ctk.CTkFrame(parent)
        self.cut_card.pack(fill="x", pady=10, padx=10)
        
        head_cut = ctk.CTkFrame(self.cut_card, fg_color="transparent")
        head_cut.pack(fill="x", padx=10, pady=5)
        self.cut_chk = ctk.CTkCheckBox(head_cut, text=self.T("grp_cut"), variable=self.cut_var, command=self.on_main_cut_toggle, font=("Segoe UI", 12, "bold"))
        self.cut_chk.pack(side="left")
        # Right side info stack
        right_frame = ctk.CTkFrame(head_cut, fg_color="transparent")
        right_frame.pack(side="right")

        ctk.CTkLabel(right_frame, text=self.T("lbl_time_fmt"), text_color="gray", font=("Segoe UI", 10, "italic")).pack(anchor="e")
        
        # [NEW] Cut Mode Checkboxes (as Radio)
        mode_frame = ctk.CTkFrame(right_frame, fg_color="transparent")
        mode_frame.pack(anchor="e")
        
        self.chk_cfast = ctk.CTkCheckBox(mode_frame, text=self.T("chk_fast_cut"), variable=self.cut_mode_var, onvalue="fast", offvalue="acc", 
                                        command=lambda: self.cut_mode_var.set("fast"), font=("Segoe UI", 10))
        self.chk_cfast.pack(side="left", padx=5)
        Tooltip(self.chk_cfast, self.T("tip_fast_cut"))
        
        self.chk_cacc = ctk.CTkCheckBox(mode_frame, text=self.T("chk_adv_cut"), variable=self.cut_mode_var, onvalue="acc", offvalue="fast",
                                       command=lambda: self.cut_mode_var.set("acc"), font=("Segoe UI", 10))
        self.chk_cacc.pack(side="left", padx=5)
        Tooltip(self.chk_cacc, self.T("tip_adv_cut"))
        
        # Ensure correct initial state (visual only, since they share var with on/off values, explicit set helps)
        # But wait, CTkCheckBox with variable sharing: if var="fast", cfast matches onvalue="fast" -> Checked.
        # cacc matches offvalue="fast" -> Unchecked? No, offvalue is what it SETS when unchecked.
        # To make them act like radio buttons:
        # Checkbox 1: variable=var, onvalue="fast", offvalue="acc" (if unchecked -> acc)
        # Checkbox 2: variable=var, onvalue="acc", offvalue="fast" (if unchecked -> fast)
        # Perfect.
        
        time_row = ctk.CTkFrame(self.cut_card, fg_color="transparent")
        time_row.pack(fill="x", padx=10, pady=(0, 10))
        
        # Start Time
        b1 = ctk.CTkFrame(time_row, fg_color="transparent")
        b1.pack(side="left")
        ctk.CTkLabel(b1, text=self.T("lbl_start").upper(), font=("Segoe UI", 10, "bold"), text_color="gray").pack(anchor="w")
        
        # [MOD] New TimeSpinbox
        self.start_entry = TimeSpinbox(b1)
        self.start_entry.pack(pady=2)
        
        self.start_chk = ctk.CTkCheckBox(b1, text=self.T("chk_from_start"), variable=self.start_chk_var, command=self.toggle_cut_inputs, font=("Segoe UI", 10))
        self.start_chk.pack(anchor="w")
        # self.add_placeholder(self.start_entry, "hh:mm:ss") # No longer needed
        
        ctk.CTkLabel(time_row, text="➜", font=("Segoe UI", 16)).pack(side="left", padx=20)
        
        # End Time
        b2 = ctk.CTkFrame(time_row, fg_color="transparent")
        b2.pack(side="left")
        ctk.CTkLabel(b2, text=self.T("lbl_end").upper(), font=("Segoe UI", 10, "bold"), text_color="gray").pack(anchor="w")
        
        # [MOD] New TimeSpinbox
        self.end_entry = TimeSpinbox(b2)
        self.end_entry.pack(pady=2)
        
        self.end_chk = ctk.CTkCheckBox(b2, text=self.T("chk_to_end"), variable=self.end_chk_var, command=self.toggle_cut_inputs, font=("Segoe UI", 10))
        self.end_chk.pack(anchor="w")
        # self.add_placeholder(self.end_entry, "hh:mm:ss") # No longer needed

        # --- FORMAT OPTIONS ---
        self.opts_card = ctk.CTkFrame(parent)
        self.opts_card.pack(fill="x", pady=10, padx=10)
        
        ctk.CTkLabel(self.opts_card, text=self.T("grp_opts"), font=("Segoe UI", 13, "bold")).pack(anchor="w", padx=10, pady=(10, 5))
        
        limit_grid = ctk.CTkFrame(self.opts_card, fg_color="transparent")
        limit_grid.pack(fill="x", padx=10, pady=(0, 10))
        
        # Three Columns Layout
        col_audio = ctk.CTkFrame(limit_grid, fg_color="transparent")
        col_audio.pack(side="left", anchor="n", fill="x", expand=True) # Fill width

        col_video = ctk.CTkFrame(limit_grid, fg_color="transparent")
        col_video.pack(side="left", anchor="n", fill="x", expand=True, padx=20) # Fill width

        col_adv = ctk.CTkFrame(limit_grid, fg_color="transparent")
        col_adv.pack(side="left", anchor="n", fill="x", expand=True) # Fill width
        
        # Col 1: Audio
        ctk.CTkLabel(col_audio, text=self.T("lbl_format_title").upper(), text_color="gray", font=("Segoe UI", 10, "bold")).pack(anchor="w")
        ctk.CTkRadioButton(col_audio, text=self.T("opt_audio_opus"), variable=self.type_var, value="audio_opus").pack(anchor="w", pady=2)
        ctk.CTkRadioButton(col_audio, text=self.T("opt_audio_aac"), variable=self.type_var, value="audio_m4a").pack(anchor="w", pady=2)
        ctk.CTkRadioButton(col_audio, text=self.T("opt_audio_mp3"), variable=self.type_var, value="audio_mp3").pack(anchor="w", pady=2)
        ctk.CTkRadioButton(col_audio, text=self.T("opt_audio_lossless"), variable=self.type_var, value="audio_lossless").pack(anchor="w", pady=2)
        
        # Col 2: Video
        ctk.CTkLabel(col_video, text=self.T("lbl_video_label"), text_color="gray", font=("Segoe UI", 10, "bold")).pack(anchor="w")
        ctk.CTkRadioButton(col_video, text=self.T("opt_video_4k"), variable=self.type_var, value="video_4k", text_color="#d32f2f").pack(anchor="w", pady=2)
        ctk.CTkRadioButton(col_video, text=self.T("opt_video_2k"), variable=self.type_var, value="video_2k", text_color="#c2185b").pack(anchor="w", pady=2)
        ctk.CTkRadioButton(col_video, text=self.T("opt_video_1080"), variable=self.type_var, value="video_1080").pack(anchor="w", pady=2)
        ctk.CTkRadioButton(col_video, text=self.T("lbl_video_720"), variable=self.type_var, value="video_720").pack(anchor="w", pady=2)
        ctk.CTkRadioButton(col_video, text=self.T("lbl_video_480"), variable=self.type_var, value="video_480").pack(anchor="w", pady=2)
        ctk.CTkRadioButton(col_video, text=self.T("lbl_video_360"), variable=self.type_var, value="video_360").pack(anchor="w", pady=2)
        ctk.CTkRadioButton(col_video, text=self.T("lbl_video_240"), variable=self.type_var, value="video_240").pack(anchor="w", pady=2)
        ctk.CTkRadioButton(col_video, text=self.T("lbl_video_144"), variable=self.type_var, value="video_144").pack(anchor="w", pady=2)

        # Col 3: Advanced
        ctk.CTkLabel(col_adv, text=self.T("lbl_advanced").upper(), text_color="gray", font=("Segoe UI", 10, "bold")).pack(anchor="w")
        ctk.CTkCheckBox(col_adv, text=self.T("chk_keep_audio"), variable=self.keep_audio_var).pack(anchor="w", pady=2)
        ctk.CTkCheckBox(col_adv, text=self.T("chk_keep_video"), variable=self.keep_video_var).pack(anchor="w", pady=2)
        
        self.sub_chk = ctk.CTkCheckBox(col_adv, text=self.T("chk_sub"), variable=self.sub_var, command=self.on_sub_toggled)
        self.sub_chk.pack(anchor="w", pady=2)
        
        # Only Subtitles option
        ctk.CTkRadioButton(col_adv, text="📝 " + self.T("opt_sub_only"), variable=self.type_var, value="sub_only", 
                          command=self.on_sub_only_click, text_color="#4CAF50").pack(anchor="w", pady=2)
        
        self.plist_chk = ctk.CTkCheckBox(col_adv, text=self.T("chk_playlist"), variable=self.playlist_var)
        self.plist_chk.pack(anchor="w", pady=2)
        
        ctk.CTkCheckBox(col_adv, text=self.T("chk_open_done"), variable=self.open_finished_var).pack(anchor="w", pady=2)
        
        ctk.CTkButton(col_adv, text=self.T("btn_adv_settings"), command=self.open_advanced_settings_dialog, height=24, fg_color="#455A64").pack(anchor="w", pady=10)

        # --- COOKIES & QUEUE ---
        misc_card = ctk.CTkFrame(parent, fg_color="transparent")
        misc_card.pack(fill="x", pady=10, padx=10)
        
        c_row = ctk.CTkFrame(misc_card, fg_color="transparent")
        c_row.pack(fill="x")
        ctk.CTkLabel(c_row, text=self.T("lbl_cookies"), font=("Segoe UI", 12, "bold")).pack(side="left")
        self.cookie_status = ctk.CTkLabel(c_row, text="(None)", text_color="gray", font=("Segoe UI", 10, "italic"))
        self.cookie_btn = ctk.CTkButton(c_row, text=self.T("btn_cookies"), command=self.select_cookies, width=80, height=25, fg_color="transparent", border_width=1)
        self.cookie_btn.pack(side="left", padx=10)
        self.cookie_status.pack(side="left")
        
        # Queue
        q_row = ctk.CTkFrame(misc_card, fg_color="transparent")
        q_row.pack(fill="x", pady=(10, 5))
        ctk.CTkLabel(q_row, text=self.T("lbl_queue"), font=("Segoe UI", 12, "bold")).pack(side="left")
        ctk.CTkButton(q_row, text=self.T("btn_add_queue"), command=self.add_to_queue, width=80, height=25).pack(side="right")
        ctk.CTkButton(q_row, text=self.T("btn_del_queue"), command=self.remove_from_queue, width=80, height=25, fg_color="#d32f2f", hover_color="#b71c1c").pack(side="right", padx=5)
        
        # Treeview (Native TTK inside CTk Frame)
        tree_frame = ctk.CTkFrame(misc_card)
        tree_frame.pack(fill="x")
        self.style_treeview()
        self.queue_tree = ttk.Treeview(tree_frame, columns=("title", "link"), show="headings", height=4)
        self.queue_tree.heading("title", text=self.T("col_title"))
        self.queue_tree.heading("link", text=self.T("col_link"))
        self.queue_tree.column("title", width=400)
        self.queue_tree.column("link", width=300)
        self.queue_tree.pack(fill="both", expand=True, padx=2, pady=2)
        
        for task in self.download_queue:
            self.queue_tree.insert("", tk.END, values=(task.get("title", 'Unknown'), task['url']))

    def create_bottom_bar(self, parent):
        bar = ctk.CTkFrame(parent, fg_color="transparent")
        bar.pack(fill="x", side="bottom", padx=20, pady=10)
        
        self.playlist_notif_label = ctk.CTkLabel(bar, text="", text_color="#e65100", font=("Segoe UI", 11, "bold"))
        self.playlist_notif_label.pack(anchor="w")
        
        self.status_label = ctk.CTkLabel(bar, text=self.T("lbl_paste_hint"), text_color="green")
        self.status_label.pack(anchor="w")
        
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ctk.CTkProgressBar(bar, variable=self.progress_var)
        self.progress_bar.set(0)
        self.progress_bar.pack(fill="x", pady=5)
        
        btn_zone = ctk.CTkFrame(bar, fg_color="transparent")
        btn_zone.pack(fill="x", pady=5)
        
        self.download_btn = ctk.CTkButton(btn_zone, text=self.T("btn_download"), command=self.start_download_thread, height=50, font=("Segoe UI", 14, "bold"), corner_radius=25)
        self.download_btn.pack(side="right", fill="x", expand=True, padx=(10,0))
        
        self.cancel_btn = ctk.CTkButton(btn_zone, text=self.T("btn_cancel"), command=self.cancel_download, height=50, width=100, fg_color="#ef5350", hover_color="#e53935", state="disabled")
        self.cancel_btn.pack(side="right")

    # ==========================
    # TAB 2: HISTORY
    # ==========================
    # ==========================
    # TAB 3: TOOLS
    # ==========================
    def setup_tools_tab(self):
        tab = self.tab_view.tab(self.T("tab_tools"))
        for w in tab.winfo_children(): w.destroy()
        
        scroll = ctk.CTkScrollableFrame(tab, fg_color="transparent")
        scroll.pack(fill="both", expand=True)
        
        ctk.CTkLabel(scroll, text=self.T("tool_title"), font=("Segoe UI", 20, "bold")).pack(anchor="w", pady=10)
        
        # Input
        card_in = ctk.CTkFrame(scroll)
        card_in.pack(fill="x", pady=5)
        ctk.CTkLabel(card_in, text=self.T("tool_lbl_input"), text_color="gray", font=("Segoe UI", 12, "bold")).pack(anchor="w", padx=10, pady=(5,0))
        row_in = ctk.CTkFrame(card_in, fg_color="transparent")
        row_in.pack(fill="x", padx=10, pady=5)
        ctk.CTkEntry(row_in, textvariable=self.tool_input_var).pack(side="left", fill="x", expand=True)
        ctk.CTkButton(row_in, text="...", command=lambda: self.tool_browse_file(self.tool_input_var), width=40).pack(side="left", padx=5)

        # Output
        card_out = ctk.CTkFrame(scroll)
        card_out.pack(fill="x", pady=5)
        ctk.CTkLabel(card_out, text=self.T("tool_lbl_output"), text_color="gray", font=("Segoe UI", 12, "bold")).pack(anchor="w", padx=10, pady=(5,0))
        row_out = ctk.CTkFrame(card_out, fg_color="transparent")
        row_out.pack(fill="x", padx=10, pady=5)
        ctk.CTkEntry(row_out, textvariable=self.tool_out_path_var, state="readonly").pack(side="left", fill="x", expand=True)
        ctk.CTkButton(row_out, text="📂", command=self.tool_browse_out_folder, width=40).pack(side="left", padx=5)

        # Actions
        card_act = ctk.CTkFrame(scroll)
        card_act.pack(fill="x", pady=10)
        ctk.CTkLabel(card_act, text=self.T("tool_lbl_act"), text_color="gray", font=("Segoe UI", 12, "bold")).pack(anchor="w", padx=10, pady=(5,0))
        
        acts_grid = ctk.CTkFrame(card_act, fg_color="transparent")
        acts_grid.pack(fill="x", padx=10, pady=10)
        
        acts = [
            ("remux", self.T("act_remux")), ("fix_rot", self.T("act_fix_rot")),
            ("norm_au", self.T("act_norm_au")), ("compress", self.T("act_compress")),
            ("extract_au", self.T("act_extract_au")), ("to_gif", self.T("act_to_gif")),   
            ("mute", self.T("act_mute")), ("fast_cut", "✂ " + self.T("act_fast_cut")), # Used "Fast Cut" key but label is "Cut Video" (modified in json?) or I'll assume I update logic
            ("soft_sub", self.T("act_soft_sub")), ("hard_sub", self.T("act_hard_sub")),
            ("cover", self.T("act_cover")), ("conv_sub", self.T("act_conv_sub"))
        ]
        
        for i, (val, txt) in enumerate(acts):
            ctk.CTkRadioButton(acts_grid, text=txt, variable=self.tool_action_var, value=val, command=self.tool_update_ui).grid(row=i//2, column=i%2, sticky="w", padx=10, pady=5)
        
        # Add GIF to Video option
        ctk.CTkRadioButton(acts_grid, text=self.T("act_gif_to_video"), variable=self.tool_action_var, value="gif_to_video", command=self.tool_update_ui).grid(row=6, column=0, sticky="w", padx=10, pady=5)

        # Extra Options
        self.pnl_extra = ctk.CTkFrame(scroll)
        self.pnl_extra.pack(fill="x", pady=5)
        
        # [NEW] Tool Cut Mode Checkboxes
        self.pnl_tool_cut = ctk.CTkFrame(self.pnl_extra, fg_color="transparent")
        self.pnl_tool_cut.pack(fill="x", padx=10, pady=2)
        
        ctk.CTkLabel(self.pnl_tool_cut, text="Mode:", text_color="gray", font=("Segoe UI", 12, "bold")).pack(side="left", padx=(0,10))
        self.t_cfast = ctk.CTkCheckBox(self.pnl_tool_cut, text=self.T("chk_fast_cut"), variable=self.tool_cut_mode_var, onvalue="fast", offvalue="acc",
                                      command=lambda: self.tool_cut_mode_var.set("fast"))
        self.t_cfast.pack(side="left", padx=5)
        Tooltip(self.t_cfast, self.T("tip_fast_cut"))
        
        self.t_cacc = ctk.CTkCheckBox(self.pnl_tool_cut, text=self.T("chk_adv_cut"), variable=self.tool_cut_mode_var, onvalue="acc", offvalue="fast",
                                     command=lambda: self.tool_cut_mode_var.set("acc"))
        self.t_cacc.pack(side="left", padx=5)
        self.t_cacc.pack(side="left", padx=5)
        Tooltip(self.t_cacc, self.T("tip_adv_cut"))
        
        # [NEW] Tool Time Inputs (Hidden by default)
        self.pnl_tool_time = ctk.CTkFrame(scroll, fg_color="transparent")
        self.pnl_tool_time.pack(fill="x", padx=10, pady=5)
        self.pnl_tool_time.pack_forget() # Hide initially
        
        # Time Row (Start -> End)
        t_row = ctk.CTkFrame(self.pnl_tool_time, fg_color="transparent")
        t_row.pack(fill="x")
        
        # Start
        b1 = ctk.CTkFrame(t_row, fg_color="transparent")
        b1.pack(side="left", expand=True)
        ctk.CTkLabel(b1, text=self.T("lbl_start").upper(), font=("Segoe UI", 10, "bold"), text_color="gray").pack(anchor="w")
        self.tool_start_entry = TimeSpinbox(b1)
        self.tool_start_entry.pack(pady=2)
        self.tool_start_chk = ctk.CTkCheckBox(b1, text=self.T("chk_from_start"), variable=self.tool_start_chk_var, 
                                             command=self.tool_toggle_cut_inputs, font=("Segoe UI", 10))
        self.tool_start_chk.pack(anchor="w")
        
        ctk.CTkLabel(t_row, text="➜", font=("Segoe UI", 16)).pack(side="left", padx=10)
        
        # End
        b2 = ctk.CTkFrame(t_row, fg_color="transparent")
        b2.pack(side="left", expand=True)
        ctk.CTkLabel(b2, text=self.T("lbl_end").upper(), font=("Segoe UI", 10, "bold"), text_color="gray").pack(anchor="w")
        self.tool_end_entry = TimeSpinbox(b2)
        self.tool_end_entry.pack(pady=2)
        self.tool_end_chk = ctk.CTkCheckBox(b2, text=self.T("chk_to_end"), variable=self.tool_end_chk_var, 
                                           command=self.tool_toggle_cut_inputs, font=("Segoe UI", 10))
        self.tool_end_chk.pack(anchor="w")
        
        self.lbl_extra = ctk.CTkLabel(self.pnl_extra, text=self.T("tool_lbl_extra"), text_color="gray")
        self.lbl_extra.pack(anchor="w", padx=10)
        
        # Row for extra entry with browse button
        self.extra_row = ctk.CTkFrame(self.pnl_extra, fg_color="transparent")
        self.extra_row.pack(fill="x", padx=10, pady=5)
        self.ent_extra = ctk.CTkEntry(self.extra_row, textvariable=self.tool_extra_var)
        self.ent_extra.pack(side="left", fill="x", expand=True)
        self.btn_extra_browse = ctk.CTkButton(self.extra_row, text="📂", command=self.tool_browse_extra_file, width=40)
        self.btn_extra_browse.pack(side="left", padx=5)
        
        self.cbo_rot = ctk.CTkComboBox(self.pnl_extra, variable=self.tool_param_var, values=[])
        self.cbo_rot.pack(padx=10, pady=5, anchor="w")

        # Run Btn
        self.btn_tool_run = ctk.CTkButton(scroll, text=self.T("tool_btn_run"), command=self.start_tool_thread, height=50, font=("Segoe UI", 14, "bold"))
        self.btn_tool_run.pack(fill="x", pady=20)
        
        self.tool_progress_var = tk.DoubleVar()
        self.tool_pb = ctk.CTkProgressBar(scroll, variable=self.tool_progress_var)
        self.tool_pb.pack(fill="x", pady=5)
        self.lbl_tool_status = ctk.CTkLabel(scroll, text=self.T("tool_status_ready"))
        self.lbl_tool_status.pack()
        
        self.tool_update_ui()

    # ==========================
    # TAB 4: SETTINGS
    # ==========================
    def setup_settings_tab(self):
        tab = self.tab_view.tab(self.T("tab_settings"))
        for w in tab.winfo_children(): w.destroy()
        
        # Main Scroll Wrapper
        scroll = ctk.CTkScrollableFrame(tab, fg_color="transparent")
        scroll.pack(fill="both", expand=True)

        ctk.CTkLabel(scroll, text=self.T("set_title"), font=("Segoe UI", 24, "bold")).pack(anchor="w", pady=(10, 20))
        
        # --- GROUP 1: NETWORK & CONNECTION ---
        grp_net = ctk.CTkFrame(scroll)
        grp_net.pack(fill="x", pady=10, padx=5)
        
        ctk.CTkLabel(grp_net, text=self.T("grp_net_title"), 
                     font=("Segoe UI", 13, "bold"), text_color="#2196F3").pack(anchor="w", padx=15, pady=(10, 5))
        
        # Proxy
        r_proxy = ctk.CTkFrame(grp_net, fg_color="transparent")
        r_proxy.pack(fill="x", padx=10, pady=5)
        ctk.CTkLabel(r_proxy, text=self.T("lbl_proxy")).pack(side="left", padx=(5, 10))
        ctk.CTkEntry(r_proxy, textvariable=self.proxy_var, placeholder_text="http://user:pass@1.2.3.4:8080").pack(side="left", fill="x", expand=True)
        
        # Geo + Browser
        r_geo = ctk.CTkFrame(grp_net, fg_color="transparent")
        r_geo.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(r_geo, text=self.T("lbl_geo")).pack(side="left", padx=(5, 10))
        ctk.CTkComboBox(r_geo, variable=self.geo_var, values=["None", "VN", "US", "JP", "KR", "CN", "GB"], width=80).pack(side="left")
        
        ctk.CTkLabel(r_geo, text=self.T("lbl_browser_cookie")).pack(side="left", padx=(20, 10))
        # Capitalize Browser Value for Display
        browsers = ["None", "Chrome", "Edge", "Firefox", "Opera", "Brave"]
        self.browser_display_var = tk.StringVar(value=self.browser_var.get().capitalize())
        ctk.CTkComboBox(r_geo, variable=self.browser_display_var, values=browsers, 
                       command=self.on_browser_change, width=100).pack(side="left")

        # --- GROUP 2: FORMAT CONFIG ---
        grp_fmt = ctk.CTkFrame(scroll)
        grp_fmt.pack(fill="x", pady=10, padx=5)
        
        ctk.CTkLabel(grp_fmt, text=self.T("grp_fmt_setting"), font=("Segoe UI", 13, "bold"), text_color="#FF9800").pack(anchor="w", padx=15, pady=(10, 5))
        
        # Exts
        r_ext = ctk.CTkFrame(grp_fmt, fg_color="transparent")
        r_ext.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(r_ext, text=self.T("lbl_video_ext")).pack(side="left", padx=(5, 10))
        # Capitalize Video Ext
        self.video_ext_display_var = tk.StringVar(value=self.video_ext_var.get().upper())
        ctk.CTkComboBox(r_ext, variable=self.video_ext_display_var, values=["MP4", "MKV", "WEBM", "AVI"], width=80).pack(side="left")
        
        ctk.CTkLabel(r_ext, text=self.T("lbl_audio_ext")).pack(side="left", padx=(20, 10))
        # Capitalize Audio Ext
        self.audio_ext_display_var = tk.StringVar(value=self.audio_ext_var.get().upper())
        ctk.CTkComboBox(r_ext, variable=self.audio_ext_display_var, values=["MP3", "M4A", "FLAC", "WAV", "OPUS"], width=80).pack(side="left")
        
        # Codec & Thumb
        r_codec = ctk.CTkFrame(grp_fmt, fg_color="transparent")
        r_codec.pack(fill="x", padx=10, pady=5)
        
        # Sync Display Var
        cv = self.codec_var.get()
        if cv == "h264": self.codec_display_var.set(self.T("val_codec_h264"))
        elif cv == "av1": self.codec_display_var.set(self.T("val_codec_av1"))
        else: self.codec_display_var.set(self.T("val_codec_auto"))
        
        ctk.CTkLabel(r_codec, text=self.T("lbl_video_codec")).pack(side="left", padx=(5, 10))
        ctk.CTkComboBox(r_codec, variable=self.codec_display_var, values=[self.T("val_codec_auto"), self.T("val_codec_h264"), self.T("val_codec_av1")], 
                        command=self.on_codec_change, width=150).pack(side="left")
                        
        ctk.CTkCheckBox(r_codec, text=self.T("chk_thumbnail"), variable=self.thumb_embed_var).pack(side="left", padx=(20, 0))

        # [NEW] Cut Tool Settings
        grp_cut = ctk.CTkFrame(scroll)
        grp_cut.pack(fill="x", pady=10, padx=5)
        
        ctk.CTkLabel(grp_cut, text=self.T("lbl_cut_settings"), font=("Segoe UI", 13, "bold"), text_color="#E91E63").pack(anchor="w", padx=15, pady=(10, 5))
        
        self.cut_method_var = tk.StringVar(value=self.settings.get("cut_method", "download_then_cut"))
        
        # Option 1: Direct
        r_c1 = ctk.CTkFrame(grp_cut, fg_color="transparent")
        r_c1.pack(fill="x", padx=10, pady=2)
        ctk.CTkRadioButton(r_c1, text=self.T("opt_cut_direct"), variable=self.cut_method_var, value="direct_cut").pack(side="left", padx=10)
        ctk.CTkLabel(r_c1, text=self.T("desc_cut_direct"), font=("Segoe UI", 10), text_color="gray").pack(side="left", padx=10)
        
        # Option 2: Download then Cut
        r_c2 = ctk.CTkFrame(grp_cut, fg_color="transparent")
        r_c2.pack(fill="x", padx=10, pady=2)
        ctk.CTkRadioButton(r_c2, text=self.T("opt_cut_download"), variable=self.cut_method_var, value="download_then_cut").pack(side="left", padx=10)
        ctk.CTkLabel(r_c2, text=self.T("desc_cut_download"), font=("Segoe UI", 10), text_color="gray").pack(side="left", padx=10)

        # --- GROUP 3: SYSTEM ---
        grp_sys = ctk.CTkFrame(scroll)
        grp_sys.pack(fill="x", pady=10, padx=5)
        
        ctk.CTkLabel(grp_sys, text=self.T("grp_sys_title"), font=("Segoe UI", 13, "bold"), text_color="#4CAF50").pack(anchor="w", padx=15, pady=(10, 5))
        
        # Lang & Theme
        r_main = ctk.CTkFrame(grp_sys, fg_color="transparent")
        r_main.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(r_main, text=self.T("set_lang")).pack(side="left", padx=(5, 10))
        
        # Language Mapping
        self.LANG_MAP = {
            "Vietnamese": "vi", "English": "en", "Chinese (Simplified)": "zh", 
            "Spanish": "es", "Russian": "ru", "Japanese": "ja", 
            "Korean": "ko", "French": "fr", "Portuguese": "pt", "German": "de"
        }
        self.LANG_MAP_REV = {v: k for k, v in self.LANG_MAP.items()}
        
        current_lang_code = self.lang_var.get()
        display_lang = self.LANG_MAP_REV.get(current_lang_code, "English")
        self.lang_display_var = tk.StringVar(value=display_lang)
        
        ctk.CTkComboBox(r_main, variable=self.lang_display_var, values=list(self.LANG_MAP.keys()), 
                        command=self.on_lang_change_ui, width=150).pack(side="left")
        
        ctk.CTkLabel(r_main, text=self.T("set_theme")).pack(side="left", padx=(20, 10))
        theme_cbo = ctk.CTkComboBox(r_main, values=[self.T("val_theme_light"), self.T("val_theme_dark")], 
                                    command=self.on_theme_change_ui, width=100)
        theme_cbo.pack(side="left")
        # Set Initial Display Value
        curr_theme = self.theme_var.get()
        if curr_theme == "Light": theme_cbo.set(self.T("val_theme_light"))
        else: theme_cbo.set(self.T("val_theme_dark"))
        
        # Toggles
        r_tog = ctk.CTkFrame(grp_sys, fg_color="transparent")
        r_tog.pack(fill="x", padx=20, pady=5)
        
        ctk.CTkCheckBox(r_tog, text=self.T("adv_metadata"), variable=self.meta_var).pack(anchor="w", pady=2)
        ctk.CTkCheckBox(r_tog, text=self.T("chk_tray"), variable=self.tray_var).pack(anchor="w", pady=2)
        ctk.CTkCheckBox(r_tog, text=self.T("chk_startup"), variable=self.startup_var).pack(anchor="w", pady=2)
        ctk.CTkCheckBox(r_tog, text=self.T("chk_auto_update"), variable=self.auto_update_var).pack(anchor="w", pady=2)
        
        # --- ACTION BAR ---
        act_bar = ctk.CTkFrame(scroll, fg_color="transparent")
        act_bar.pack(fill="x", pady=20)
        
        ctk.CTkButton(act_bar, text=self.T("btn_guide"), command=self.show_user_guide, fg_color="#E65100", hover_color="#EF6C00").pack(side="left", padx=5)
        ctk.CTkButton(act_bar, text=self.T("btn_save"), command=self.save_settings, fg_color="#2E7D32", hover_color="#388E3C", width=150).pack(side="right", padx=5)

    def on_codec_change(self, value):
        # Map Display -> Internal
        if value == self.T("val_codec_h264"): self.codec_var.set("h264")
        elif value == self.T("val_codec_av1"): self.codec_var.set("av1")
        else: self.codec_var.set("auto")
    
    def on_browser_change(self, value):
        """Update browser variable and cookie indicator when user changes browser"""
        self.browser_var.set(value.lower())
        # Update indicator on Home tab
        self.update_cookie_indicator()

    # --- POPUPS & LOGIC SHIMS ---
    
    def show_user_guide(self):
        top = ctk.CTkToplevel(self)
        top.title(self.T("guide_title"))
        top.geometry("900x700")
        
        # Make modal/topmost (User requested "in front")
        top.attributes('-topmost', True)
        
        # Center window
        top.update_idletasks()
        try:
            x = self.winfo_x() + (self.winfo_width() // 2) - (900 // 2)
            y = self.winfo_y() + (self.winfo_height() // 2) - (700 // 2)
            top.geometry(f"+{x}+{y}")
        except: pass
        
        # Header
        ctk.CTkLabel(top, text="📖 " + self.T("guide_title"), font=("Segoe UI", 24, "bold")).pack(pady=10)
        
        # TabView
        tabview = ctk.CTkTabview(top)
        tabview.pack(pady=10, padx=10, fill="both", expand=True)
        
        # Common text settings
        txt_font = ("Consolas", 14) # Increased font size
        
        # Tab 1: Manual
        tab1 = tabview.add(self.T("guide_title"))
        text1 = ctk.CTkTextbox(tab1, font=txt_font, wrap="word")
        text1.pack(fill="both", expand=True, padx=5, pady=5)
        text1.insert("1.0", self.T("guide_content"))
        text1.configure(state="disabled")
        
        # Tab 2: Features
        tab2 = tabview.add(self.T("tab_features"))
        text2 = ctk.CTkTextbox(tab2, font=txt_font, wrap="word") 
        text2.pack(fill="both", expand=True, padx=5, pady=5)
        text2.insert("1.0", self.T("guide_features_content"))
        text2.configure(state="disabled")
        
        # Tab 3: FAQ
        tab3 = tabview.add(self.T("tab_faq"))
        text3 = ctk.CTkTextbox(tab3, font=txt_font, wrap="word")
        text3.pack(fill="both", expand=True, padx=5, pady=5)
        text3.insert("1.0", self.T("guide_faq_content"))
        text3.configure(state="disabled")

        # Tab 4: Tips (Mẹo) - [NEW]
        tab4 = tabview.add(self.T("tab_tips") if self.T("tab_tips") != "[tab_tips]" else "Tips")
        text4 = ctk.CTkTextbox(tab4, font=txt_font, wrap="word")
        text4.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Load from data.py based on language, fallback to English
        tips_content = TIPS_CONTENT.get(self.lang, TIPS_CONTENT.get("en", "Tips content not found."))
        
        text4.insert("1.0", tips_content)
        text4.configure(state="disabled")
        
        # Close button
        ctk.CTkButton(top, text=self.T("btn_close"), command=top.destroy, 
                     fg_color="#607D8B", hover_color="#546E7A", width=150).pack(pady=10)
        
    def open_advanced_settings_dialog(self):
        # Migrating the advanced settings dialog to CTk Toplevel would be ideal, 
        # but for now we can wrap it or just use a new CTkToplevel
        top = ctk.CTkToplevel(self)
        top.title(self.T("title_adv_settings"))
        top.geometry("500x600")
        
        scroll = ctk.CTkScrollableFrame(top)
        scroll.pack(fill="both", expand=True)

        ctk.CTkLabel(scroll, text=self.T("title_adv_settings"), font=("Segoe UI", 16, "bold")).pack(pady=10)
        ctk.CTkCheckBox(scroll, text=self.T("adv_split_chapter"), variable=self.chapter_var).pack(anchor="w", padx=20, pady=5)
        ctk.CTkCheckBox(scroll, text=self.T("adv_archive"), variable=self.archive_var).pack(anchor="w", padx=20, pady=5)
        ctk.CTkCheckBox(scroll, text=self.T("adv_metadata"), variable=self.meta_var).pack(anchor="w", padx=20, pady=5)
        
        # SponsorBlock
        sb_frame = ctk.CTkFrame(scroll)
        sb_frame.pack(fill="x", padx=10, pady=10)
        ctk.CTkLabel(sb_frame, text=self.T("grp_sb_opts"), font=("Segoe UI", 12, "bold")).pack(anchor="w", padx=10, pady=5)
        
        sb_items = [
            (self.sb_sponsor_var, "sb_sponsor"),
            (self.sb_intro_var, "sb_intro"),
            (self.sb_outro_var, "sb_outro"),
            (self.sb_selfpromo_var, "sb_selfpromo"),
            (self.sb_interaction_var, "sb_interaction"),
            (self.sb_music_off_var, "sb_music_offtopic"),
            (self.sb_preview_var, "sb_preview"),
        ]
        for var, key in sb_items:
            ctk.CTkCheckBox(sb_frame, text=self.T(key), variable=var).pack(anchor="w", padx=20, pady=2)

        ctk.CTkButton(top, text=self.T("btn_close"), command=lambda: [self.save_settings(), top.destroy()]).pack(fill="x", padx=20, pady=20)

    # --- REQUIRED METHODS FROM ORIGINAL LOGIC (ADAPTED) ---
    def _run_background_startup_tasks(self):
        threading.Thread(target=self.safe_check_updates, daemon=True).start()
        if self.settings.get("run_on_on_startup", True):
            threading.Thread(target=set_autostart_registry, args=(True,), daemon=True).start()

    def _extract_url(self, text):
        """Smartly extract the first valid URL from text"""
        if not text: return ""
        # Regex for http/https URLs
        match = re.search(r'(https?://[^\s]+)', text)
        if match:
            return match.group(1)
        return text.strip()

    def paste_link(self):
        try:
            txt = self.clipboard_get()
            clean_url = self._extract_url(txt)
            self.url_var.set(clean_url)
            self.start_check_link_info(clean_url)
        except: pass

    # ==========================
    # INFO FETCH SYSTEM (REWRITTEN)
    # ==========================
    
    def toggle_check_cancel(self):
        """Toggle between Check and Cancel button"""
        if self.is_fetching_info:
            self._cancel_fetch()
        else:
            raw_url = self.url_var.get()
            clean_url = self._extract_url(raw_url)
            if clean_url != raw_url:
                self.url_var.set(clean_url)
            
            if clean_url:
                self._start_fetch(clean_url)
    
    def _cancel_fetch(self):
        """Cancel current fetch and reset UI"""
        self.cancel_fetch_event.set()
        self.is_fetching_info = False
        self.check_btn.configure(text=self.T("btn_check"), state="normal", fg_color=["#3B8ED0", "#1F6AA5"])
        self.info_frame.pack_forget()
        self.title_label.configure(text="")
        # Clear image reference first to avoid "image doesn't exist" error
        self.thumb_image_ref = None
        try:
            self.thumb_label.configure(text="", image=None)
        except:
            pass  # Ignore if image was garbage collected
    
    def _start_fetch(self, url):
        """Start fetching info for URL"""
        # Cancel any previous fetch
        self.cancel_fetch_event.set()
        self.cancel_fetch_event = threading.Event()  # Create new event
        
        self.is_fetching_info = True
        self.fetched_title = ""
        
        # Update UI to loading state
        self.check_btn.configure(text=self.T("btn_cancel_check"), state="normal", fg_color="#d32f2f")
        self.info_frame.pack(fill="x", pady=(10, 0))
        self.title_label.configure(text=self.T("lbl_loading"), text_color=self.current_theme.get("text", "white"))
        # [FIX] Clear thumbnail properly
        self.thumb_image_ref = None
        try:
            self.thumb_label.configure(image=None, text="⏳")
        except:
            pass
        
        # Start fetch in background
        cancel_event = self.cancel_fetch_event  # Capture reference
        threading.Thread(target=self._do_fetch, args=(url, cancel_event), daemon=True).start()
    
    def _do_fetch(self, url, cancel_event):
        """Background thread: fetch video info"""
        def safe_after(callback):
            """Safe wrapper for self.after() that handles main loop not running."""
            try:
                self.after(0, callback)
            except RuntimeError:
                # Main loop not running (app shutting down or not started)
                pass
        
        try:
            # Check if cancelled
            if cancel_event.is_set():
                return
            
            # Fetch info using FastFetcher (tiered strategy)
            info, error = self.fetcher.fetch(url)
            
            if error:
                 print(f"Fetch Error (Tier {info.get('_fetcher_tier', '?') if info else '?'}): {error}")
                 if not cancel_event.is_set():
                     safe_after(lambda: self._on_fetch_error(f"Lỗi: {error[:60]}"))
                 return
            
            # Check cancelled again
            if cancel_event.is_set():
                return
            
            if not info:
                safe_after(lambda: self._on_fetch_error("Không lấy được thông tin"))
                return
            
            # Handle playlist (get first item)
            is_playlist = False
            if 'entries' in info and info['entries']:
                info = info['entries'][0]
                is_playlist = True
            elif 'playlist' in url or 'list=' in url:
                is_playlist = True
            
            # Extract info
            title = info.get('title', 'Unknown')
            uploader = info.get('uploader', 'Unknown')
            duration = info.get('duration_string', '??:??')
            thumbnail_url = info.get('thumbnail')
            
            self.fetched_title = title
            self.fetched_duration = info.get('duration', 0)
            
            # Extract subtitles
            self.official_subs = info.get('subtitles', {}) or {}
            self.auto_subs = info.get('automatic_captions', {}) or {}
            self.available_subtitles = {**self.official_subs, **self.auto_subs}
            
            # Update UI (check cancelled)
            if cancel_event.is_set():
                return
            
            display_text = f"{title}\nChannel: {uploader} | Duration: {duration}"
            safe_after(lambda: self._on_fetch_success(display_text, thumbnail_url, is_playlist, cancel_event))
            
        except Exception as e:
            if not cancel_event.is_set():
                safe_after(lambda: self._on_fetch_error(str(e)[:50]))
    
    def _on_fetch_success(self, display_text, thumbnail_url, is_playlist, cancel_event):
        """UI update after successful fetch"""
        if cancel_event.is_set():
            return
        
        self.is_fetching_info = False
        self.check_btn.configure(text=self.T("btn_check"), state="normal", fg_color=["#3B8ED0", "#1F6AA5"])
        self.title_label.configure(text=display_text)
        
        # Playlist notification
        if is_playlist:
            self.plist_chk.configure(state='normal')
            self.playlist_notif_label.configure(text=self.T("msg_playlist_detect"))
        else:
            self.playlist_var.set(False)
            self.plist_chk.configure(state='disabled')
            self.playlist_notif_label.configure(text="")
        
        # Load thumbnail in background
        # [FIX] Clear existing image reference first to prevent "pyimage doesn't exist" error
        self.thumb_image_ref = None
        try:
            self.thumb_label.configure(text="⏳", image=None)
        except:
            pass
        
        if thumbnail_url and not cancel_event.is_set():
            threading.Thread(target=self._load_thumbnail, args=(thumbnail_url, cancel_event), daemon=True).start()
        else:
            try:
                self.thumb_label.configure(text="No thumbnail", image=None)
            except:
                pass
        
        # Show subtitle selector if needed
        if self.type_var.get() == "sub_only" and self.available_subtitles:
            self.show_subtitle_selector()
        elif self.sub_var.get() and self.available_subtitles:
            self.show_subtitle_selector()
    
    def _on_fetch_error(self, error_msg):
        """UI update after fetch error"""
        self.is_fetching_info = False
        self.check_btn.configure(text=self.T("btn_check"), state="normal", fg_color=["#3B8ED0", "#1F6AA5"])
        self.title_label.configure(text=f"Error: {error_msg}", text_color="red")
        self.thumb_label.configure(text="❌", image=None)
    
    def _load_thumbnail(self, url, cancel_event):
        """Load thumbnail image in background"""
        try:
            if cancel_event.is_set():
                return
            import urllib.request
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=5) as response:
                data = response.read()
            if not cancel_event.is_set():
                self.after(0, lambda: self._update_thumbnail(data))
        except Exception as e:
            print(f"Thumbnail load error: {e}")
            if not cancel_event.is_set():
                try:
                    self.after(0, lambda: self._safe_set_thumb_error())
                except:
                    pass
    
    def _safe_set_thumb_error(self):
        """Safely set thumbnail error state with proper exception handling."""
        try:
            self.thumb_image_ref = None
            self.thumb_label.configure(text="Err", image=None)
        except Exception:
            pass
    
    def _update_thumbnail(self, raw_data):
        """Update thumbnail image on UI"""
        try:
            from PIL import Image, ImageTk
            from io import BytesIO
            
            img = Image.open(BytesIO(raw_data))
            
            # Manually resize since we are replacing CTkImage (which did this auto)
            # Use high-quality resampling
            # We explicitly bind to 'self' (the main window) to avoid "pyimage doesn't exist" errors
            # caused by the destroyed first-run dialog root.
            target_w, target_h = 160, 90
            img = img.resize((target_w, target_h), Image.Resampling.LANCZOS)
            
            photo_img = ImageTk.PhotoImage(img, master=self)
            
            self.thumb_image_ref = photo_img
            self.thumb_label.configure(image=photo_img, text="")
            
        except Exception as e:
            print(f"Thumbnail update error: {e}")
            try:
                self.thumb_image_ref = None
                self.thumb_label.configure(text="No PIL", image=None)
            except: pass
    
    # Compatibility shim - keep old function name working
    def start_check_link_info(self, url):
        """Compatibility wrapper for _start_fetch"""
        url = url.strip()
        if url:
             self._start_fetch(url)
    
    # ==========================
    # CUT/TRIM CONTROLS
    # ==========================
    def on_main_cut_toggle(self):
        # [LOGIC] When Cut is enabled, AUTO UNCHECK Start/End so user can edit time immediately
        if self.cut_var.get():
            self.start_chk_var.set(False)
            self.end_chk_var.set(False)
        else:
            # Optional: Reset to checked when disabled? Or keep last state?
            # User wants "uncheck when enabled", doesn't specify reverse.
            pass
            
        self.toggle_cut_inputs()

        # [UI] Update Download Button Text Immediately
        if self.cut_var.get():
             self.download_btn.configure(text=self.T("btn_start_cut"))
        else:
             self.download_btn.configure(text=self.T("btn_download"))

    def toggle_cut_inputs(self):
        state = "normal" if self.cut_var.get() else "disabled"
        self.start_chk.configure(state=state)
        self.end_chk.configure(state=state)
        
        # Update TimeSpinbox states
        start_state = state if self.cut_var.get() and not self.start_chk_var.get() else "disabled"
        self.start_entry.configure(state=start_state)
        
        end_state = state if self.cut_var.get() and not self.end_chk_var.get() else "disabled"
        self.end_entry.configure(state=end_state)
    
    def monitor_clipboard(self):
        """Monitor clipboard for auto-paste"""
        try:
            curr = self.clipboard_get()
            if curr != self.last_clipboard and self.auto_paste_var.get():
                clean_curr = self._extract_url(curr)
                # Only paste if regex actually found a URL
                if clean_curr and clean_curr != curr.strip(): 
                     self.url_var.set(clean_curr)
                     self._start_fetch(clean_curr)
                elif re.match(r'^(https?://)', curr.strip()):
                     self.url_var.set(curr)
                     self._start_fetch(curr)
            self.last_clipboard = curr
        except:
            pass
        self.after(1000, self.monitor_clipboard)
    
    def on_url_change_delayed(self, event):
        """DISABLED - User clicks Check button to fetch"""
        pass

    def cancel_download(self):
        if messagebox.askyesno(self.T("pop_confirm"), self.T("msg_stop_dl")):
            self.is_cancelled = True
            # [FIX] Also signal the engine to cancel
            self.engine.cancel()
            self.status_label.configure(text=self.T("status_cancel"), text_color="red")
            self.cancel_btn.configure(state="disabled")

    # ==========================
    # HELPER FUNCTIONS
    # ==========================
    
    def select_folder(self):
        d = filedialog.askdirectory()
        if d: self.path_var.set(d)
        
    def open_save_folder(self):
        if os.path.exists(self.path_var.get()): 
            os.startfile(self.path_var.get())
    
    def select_cookies(self):
        """Show cookie helper dialog with guidance + file upload option"""
        self.show_cookie_helper_dialog(error_msg="")
    
    def add_placeholder(self, entry, text):
        entry.configure(placeholder_text=text)
    
    def add_to_queue(self):
        """Add URL to queue with background info fetch if title not available"""
        url = self.url_var.get().strip()
        if not url: return

        # SNAPSHOT SETTINGS
        task_settings = {
            "url": url,
            "title": self.fetched_title if self.fetched_title else "Loading...",
            "dtype": self.type_var.get(),
            "download_sub": self.sub_var.get(),
            "subs": self.selected_sub_langs if self.sub_var.get() else [],
            "sub_format": self.selected_sub_format,
            
            # Cut info
            "cut_mode": self.cut_var.get(),
            "cut_method": self.settings.get("cut_method", "download_then_cut"), # Pass method
            "start_time": self._parse_time(self.start_entry.get()) if self.cut_var.get() else 0,
            "end_time": self._parse_time(self.end_entry.get()) if self.cut_var.get() else 0,
            
            # Additional flags
            "is_plist": self.playlist_var.get(),
            
            # Paths & Configs (Snapshot)
            "save_path": self.path_var.get(),
            "cookie_file": self.cookies_path_var.get(),
            "browser_source": self.browser_var.get() if hasattr(self, 'browser_var') else "none",
        }
        
        # Reset Cut Mode after adding (optional UX choice? No, keep it for repeated adds)
        # self.cut_var.set(False) 
        
        if self.fetched_title:
            self.download_queue.append(task_settings)
            
            # Display extra info in queue
            extra = ""
            if task_settings["cut_mode"]: extra += " [✂ Cut]"
            if task_settings["download_sub"]: extra += " [CC]"
            if "audio" in task_settings["dtype"]: extra += " [♫]"
            
            self.queue_tree.insert("", "end", values=(self.fetched_title + extra, url))
        else:
            idx = len(self.download_queue)
            self.download_queue.append(task_settings)
            self.queue_tree.insert("", "end", values=("⏳ Loading...", url))
            threading.Thread(target=self._bg_fetch_queue_title, args=(url, idx, self.queue_tree.get_children()[-1]), daemon=True).start()

    def _parse_time(self, t_str):
        try:
            parts = list(map(int, t_str.split(':')))
            if len(parts) == 3: return parts[0]*3600 + parts[1]*60 + parts[2]
            if len(parts) == 2: return parts[0]*60 + parts[1]
            return parts[0]
        except: return 0

    def _bg_fetch_queue_title(self, url, idx, tree_id):
        """Background thread to fetch title for queue item"""
        try:
            info = self.engine.fetch_info(url)
            title = info.get('title', 'Unknown') if info else 'Unknown'
            # Update data and UI
            if idx < len(self.download_queue):
                self.download_queue[idx]['title'] = title
            self.after(0, lambda: self._update_queue_item(tree_id, title, url))
        except:
            self.after(0, lambda: self._update_queue_item(tree_id, "Error", url))

    def _update_queue_item(self, tree_id, title, url):
        try:
            if self.queue_tree.exists(tree_id):
                self.queue_tree.item(tree_id, values=(title, url))
        except: pass

    def remove_from_queue(self):
        sel = self.queue_tree.selection()
        if sel: 
            idx = self.queue_tree.index(sel[0])
            self.queue_tree.delete(sel[0])
            if 0 <= idx < len(self.download_queue):
                self.download_queue.pop(idx)
    
    # ==========================
    # SMART COOKIE HELPER
    # ==========================
    
    def update_cookie_indicator(self):
        """Update cookie status indicator on Home tab"""
        browser = self.browser_var.get() if hasattr(self, 'browser_var') else 'none'
        
        if browser and browser.lower() != 'none':
            self.cookie_status_label.configure(
                text=f"🍪 Cookies: {browser.capitalize()}", 
                text_color="#4CAF50"  # Green
            )
        else:
            self.cookie_status_label.configure(
                text="🍪 Cookies: None", 
                text_color="gray"
            )
    
    def jump_to_cookie_settings(self):
        """Jump to Settings tab and focus on Browser Cookies option"""
        # Switch to Settings tab
        self.tab_view.set(self.T("tab_settings"))
        
        # Ensure settings tab is loaded
        if not self.is_settings_loaded:
            self.setup_settings_tab()
            self.is_settings_loaded = True
        
        # Show tooltip
        messagebox.showinfo(self.T("pop_info"), 
            "Browser Cookies setting:\n\n" +
            "Select your browser (Chrome, Edge, Firefox...)\n" +
            "Make sure you're logged in to the browser!\n\n" +
            "This works for age-restricted & premium videos.")
    
    def show_cookie_helper_dialog(self, error_msg=""):
        """Show smart cookie helper dialog (Redesigned - Extension Focus)"""
        dialog = ctk.CTkToplevel(self)
        
        # Title based on whether there's an error
        if error_msg:
            dialog.title(self.T("pop_error"))
            header_text = "⚠️ " + self.T("msg_cookie_required")
            header_color = "#FF5722"
        else:
            dialog.title("Cookie Helper")
            header_text = "🍪 " + "Cookie Guide"
            header_color = "#4FC3F7"
        
        dialog.geometry("500x420")
        dialog.resizable(False, False)
        dialog.transient(self)
        dialog.grab_set()
        
        # Center dialog
        dialog.update_idletasks()
        x = self.winfo_x() + (self.winfo_width() // 2) - (500 // 2)
        y = self.winfo_y() + (self.winfo_height() // 2) - (420 // 2)
        dialog.geometry(f"+{x}+{y}")
        
        # Main scroll frame
        scroll = ctk.CTkScrollableFrame(dialog, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=15, pady=10)
        
        # Header
        ctk.CTkLabel(scroll, text=header_text, 
                    font=("Segoe UI", 18, "bold"), text_color=header_color).pack(pady=(5, 5))
        
        # Error message if present
        if error_msg:
            # Clean up error message
            short_err = error_msg.split('\n')[0][:100]
            ctk.CTkLabel(scroll, text=f"{short_err}...", 
                        font=("Segoe UI", 11), text_color="#FFAB91", wraplength=440).pack(pady=(0, 10))
        
        # === Extension Method (The ONLY Method now) ===
        # Use a nice card design
        card = ctk.CTkFrame(scroll, fg_color="#1E4A3F", corner_radius=12) # Dark Green Theme
        card.pack(fill="x", pady=5)
        
        # Title
        ctk.CTkLabel(card, text="✅ " + self.T("lbl_method_extension").replace("Method 2: ", "").replace("Cách 2: ", ""), 
                    font=("Segoe UI", 14, "bold"), text_color="#A7FFEB").pack(anchor="w", padx=15, pady=(15, 5))
        
        # Description - 3 Steps
        desc_txt = f"{self.T('cookie_step_1')}\n{self.T('cookie_step_2')}\n{self.T('cookie_step_3')}"
        ctk.CTkLabel(card, text=desc_txt, 
                    font=("Segoe UI", 12), text_color="#E0F2F1", wraplength=420, justify="left").pack(anchor="w", padx=15, pady=(0, 15))
        
        # Buttons Row
        btn_row = ctk.CTkFrame(card, fg_color="transparent")
        btn_row.pack(pady=(0, 15), padx=15, fill="x")
        
        ctk.CTkButton(btn_row, text="📥 " + self.T("btn_install_extension"), 
                     command=lambda: webbrowser.open("https://chromewebstore.google.com/detail/get-cookiestxt-locally/cclelndahbckbenkjhflpdbgdldlbecc"),
                     fg_color="#00BCD4", hover_color="#0097A7", height=35).pack(side="left", fill="x", expand=True, padx=(0, 5))
        
        def on_load_cookie_file():
            dialog.destroy()
            self._browse_and_load_cookie_file()
        
        ctk.CTkButton(btn_row, text="📂 " + self.T("btn_load_cookie_file"), 
                     command=on_load_cookie_file, fg_color="#FF9800", hover_color="#F57C00",
                     height=35).pack(side="right", fill="x", expand=True, padx=(5, 0))
        
        
        # === Tips Section ===
        tips_frame = ctk.CTkFrame(scroll, fg_color="transparent", border_width=1, border_color="#546E7A", corner_radius=8)
        tips_frame.pack(fill="x", pady=15)
        
        ctk.CTkLabel(tips_frame, text="💡 " + self.T("lbl_tips"), 
                    font=("Segoe UI", 12, "bold"), text_color="#B0BEC5").pack(anchor="w", padx=15, pady=(8, 2))
                    
        ctk.CTkLabel(tips_frame, text=self.T("tips_cookie_usage"), 
                    font=("Segoe UI", 11), text_color="#90A4AE", wraplength=420, justify="left").pack(anchor="w", padx=15, pady=(0, 8))
        
        # Close button
        ctk.CTkButton(scroll, text=self.T("btn_close"), command=dialog.destroy,
                     fg_color="transparent", border_width=1, border_color="gray", 
                     text_color="gray", hover_color="#424242", width=100, height=30).pack(pady=5)
    
    def _apply_browser_cookies_and_retry(self, browser="chrome"):
        """Apply browser cookies and retry last download"""
        # Update browser setting
        self.browser_var.set(browser)
        self.update_cookie_indicator()
        
        # Show status
        # Show status
        self.status_label.configure(text=self.T("status_retrying_cookie").format(browser.capitalize()), 
                                   text_color="#FF9800")
        
        # Retry download
        threading.Thread(target=self.run_download_process, daemon=True).start()
    
    def jump_to_cookie_settings(self):
        """Switch to Settings tab and scroll to cookie section"""
        self.tab_view.set(self.T("tab_settings"))
        # Trigger tab load if not loaded
        if not self.is_settings_loaded:
            self.setup_settings_tab()
            self.is_settings_loaded = True
    
    def _browse_and_load_cookie_file(self):
        """Browse for cookies.txt file and load it"""
        file_path = filedialog.askopenfilename(
            title=self.T("btn_load_cookie_file"),
            filetypes=[("Cookie files", "*.txt"), ("All files", "*.*")]
        )
        if file_path and os.path.exists(file_path):
            self.settings["cookie_file"] = file_path
            self.cookies_path_var.set(file_path) # [FIX] UI update
            self.config_mgr.save_settings(self.settings)
            self.update_cookie_indicator() # [FIX] Visual update
            messagebox.showinfo(self.T("pop_success"), self.T("msg_cookie_loaded"))
    
    def _should_suggest_cookies(self, error_msg):
        """Detect if error message suggests cookies might help"""
        if not error_msg:
            return False
        
        error_lower = error_msg.lower()
        
        # Keywords that indicate cookie-related issues (matches yt-dlp error format)
        cookie_keywords = [
            '403', 'forbidden',
            'restricted', 'age-restricted', 'age restricted', 'confirm your age',
            'private', 'members-only', 'members only', 'member-only',
            'premium', 'requires login', 'sign in', 'login required',
            'unavailable', 'not available',
            'cookies', 'authentication', 'dpapi', 'failed to decrypt',
            'yêu cầu đăng nhập', 'cần cookie',  # Vietnamese messages
            'no video formats', 'no video found', 'fallback found nothing' # [FIX] Catch generic/Dailymotion errors
        ]
        
        result = any(keyword in error_lower for keyword in cookie_keywords)
        print(f"[DEBUG] _should_suggest_cookies: '{error_msg[:50]}...' -> {result}")
        return result
    
    # ==========================
    # TOOLS TAB FUNCTIONS
    # ==========================
    
    def tool_browse_file(self, var):
        f = filedialog.askopenfilename()
        if f: var.set(f)

    def tool_browse_out_folder(self):
        d = filedialog.askdirectory()
        if d: self.tool_out_path_var.set(d)

    def tool_browse_extra_file(self):
        """Browse for extra file (subtitle/image) based on current action"""
        act = self.tool_action_var.get()
        if act in ["soft_sub", "hard_sub"]:
            filetypes = [("Subtitle files", "*.srt *.ass *.vtt *.sub"), ("All files", "*.*")]
        elif act == "cover":
            filetypes = [("Image files", "*.jpg *.jpeg *.png *.bmp"), ("All files", "*.*")]
        else:
            filetypes = [("All files", "*.*")]
        
        f = filedialog.askopenfilename(filetypes=filetypes)
        if f:
            self.tool_extra_var.set(f)

    def tool_update_ui(self):
        act = self.tool_action_var.get()
        t = self.current_theme
        
        # Reset visibility
        self.cbo_rot.pack_forget()
        self.extra_row.pack_forget()
        self.pnl_tool_cut.pack_forget() # [FIX] Hide cut panel
        self.pnl_tool_time.pack_forget() # [FIX] Hide time panel
        self.lbl_extra.configure(text="")
        self.btn_extra_browse.pack_forget()
        
        if act not in ["compress", "extract_au", "remux", "fast_cut", "to_gif", "gif_to_video"]: 
            self.tool_param_var.set("0")
            
        show_extra = False
        show_param = False
        show_browse = False  # Show file browse button
        show_time = False    # Show time inputs (Start/End)

        # Actions that need file input (sub, cover)
        if act in ["soft_sub", "hard_sub"]:
            show_extra = True
            show_browse = True
            self.lbl_extra.configure(text=self.T("tool_lbl_sub_fmt"), text_color=t["accent"])
            self.tool_extra_var.set("")
        elif act == "cover":
            show_extra = True
            show_browse = True
            self.lbl_extra.configure(text=self.T("tool_lbl_img_fmt"), text_color=t["accent"])
            self.tool_extra_var.set("")
        
        # Actions that need time range
        elif act == "fast_cut":
            # show_extra = True # No longer showing the old text input
            # Show Cut Mode Options
            self.pnl_tool_cut.pack(fill="x", padx=10, pady=2)
            self.pnl_tool_time.pack(fill="x", padx=10, pady=5) # Show new time inputs
            self.tool_toggle_cut_inputs() # Ensure state update
            # self.tool_extra_var.set("00:00:00 - 00:00:10") # Legacy
        elif act == "to_gif":
            show_extra = True
            self.lbl_extra.configure(text=self.T("tool_lbl_time_range"), text_color=t["accent"])
            self.tool_extra_var.set("00:00:00 - 00:00:05")
        elif act == "gif_to_video":
            show_param = True
            self.lbl_extra.configure(text=self.T("tool_lbl_out_fmt"))
            self.cbo_rot.configure(values=["mp4", "webm", "avi"])
            self.cbo_rot.set("mp4")
        
        # Other param-based actions
        elif act == "remux":
            show_param = True
            self.lbl_extra.configure(text=self.T("tool_lbl_ext"))
            self.cbo_rot.configure(values=["mp4", "mkv", "avi", "mov", "webm", "flv"])
            self.cbo_rot.set("mp4")

        elif act == "fix_rot":
            show_param = True
            self.lbl_extra.configure(text=self.T("tool_lbl_rot"))
            self.cbo_rot.configure(values=["90", "180", "270"])
            self.cbo_rot.set("90")

        elif act == "compress":
            show_param = True
            self.lbl_extra.configure(text=self.T("tool_lbl_quality"))
            self.cbo_rot.configure(values=[self.T("val_comp_med"), self.T("val_comp_high"), self.T("val_comp_low")])
            self.cbo_rot.set(self.T("val_comp_med"))
            
        elif act == "extract_au":
            show_param = True
            self.lbl_extra.configure(text=self.T("tool_lbl_out_cfg"))
            self.cbo_rot.configure(values=[
                self.T("val_au_mp3_std"), 
                self.T("val_au_original"), 
                self.T("val_au_mp3_high"), 
                self.T("val_au_aac"), 
                self.T("val_au_wav")
            ])
            self.cbo_rot.set(self.T("val_au_mp3_std"))
            
        elif act == "conv_sub":
             show_param = True
             self.lbl_extra.configure(text=self.T("tool_lbl_sel_sub_fmt"))
             self.cbo_rot.configure(values=["srt", "ass", "vtt", "lrc"])
             self.cbo_rot.set("srt")

        # Show/hide widgets
        if show_extra:
            self.extra_row.pack(fill="x", padx=10, pady=5)
            self.ent_extra.pack(side="left", fill="x", expand=True)
            if show_browse:
                self.btn_extra_browse.pack(side="left", padx=5)
        if show_param:
            self.cbo_rot.pack(padx=10, pady=5, anchor="w")

    def start_tool_thread(self):
        inp = self.tool_input_var.get()
        if not inp or not os.path.exists(inp):
            messagebox.showerror(self.T("pop_error"), self.T("msg_file_missing"))
            return
            
        self.btn_tool_run.configure(state='disabled', text=self.T("tool_status_running"), fg_color="#7f8c8d")
        self.lbl_tool_status.configure(text=self.T("tool_status_running"), text_color="#e65100")
        
        threading.Thread(target=self.run_tool_process, daemon=True).start()

    def tool_toggle_cut_inputs(self):
        # Enable/Disable logic for tool tab time inputs
        # Start
        if self.tool_start_chk_var.get():
             self.tool_start_entry.configure(state="disabled")
        else:
             self.tool_start_entry.configure(state="normal")
             
        # End
        if self.tool_end_chk_var.get():
             self.tool_end_entry.configure(state="disabled")
        else:
             self.tool_end_entry.configure(state="normal")

    def run_tool_process(self):
        act = self.tool_action_var.get()
        inp = self.tool_input_var.get()
        extra = self.tool_extra_var.get()
        param = self.tool_param_var.get() 
        out_folder = self.tool_out_path_var.get()
        
        self.after(0, lambda: self.tool_progress_var.set(0))

        if not out_folder or not os.path.exists(out_folder):
            out_folder = os.path.dirname(inp)
            
        base_name = os.path.splitext(os.path.basename(inp))[0]
        ext = os.path.splitext(inp)[1]
        
        out = os.path.join(out_folder, f"{base_name}_{act}{ext}")
        if act == "remux": 
            target_ext = param if param else "mp4"
            out = os.path.join(out_folder, f"{base_name}_new.{target_ext}")
        elif act == "conv_sub": out = os.path.join(out_folder, f"{base_name}.{param}")
        elif act == "to_gif": out = os.path.join(out_folder, f"{base_name}.gif")
        elif act == "gif_to_video": 
            target_ext = param if param else "mp4"
            out = os.path.join(out_folder, f"{base_name}.{target_ext}")
        elif act == "fast_cut": out = os.path.join(out_folder, f"{base_name}_cut{ext}")
        elif act == "extract_au": 
            if "Original" in param: out = os.path.join(out_folder, f"{base_name}.m4a")
            elif "AAC" in param: out = os.path.join(out_folder, f"{base_name}.m4a")
            elif "WAV" in param: out = os.path.join(out_folder, f"{base_name}.wav")
            else: out = os.path.join(out_folder, f"{base_name}.mp3")
        
        success = False
        msg = ""

        def update_tool_progress(percent):
            val = percent / 100.0
            # Tools usually use a different variable tool_progress_var, check if it binds to a specific bar
            # Assuming tool_progress_var is DoubleVar linked to a ProgressBar, we need to adapt the widget or the var
            self.after(0, lambda: self.tool_progress_var.set(val))
            self.after(0, lambda: self.lbl_tool_status.configure(text=f"{self.T('tool_status_running')} {int(percent)}%"))

        try:
            total_duration = self.engine.get_duration(inp)
            
            if act == "remux":
                success, msg = self.engine.change_video_format(inp, out, duration=total_duration, callback=update_tool_progress)
            
            elif act == "compress":
                crf_val = 28
                if "CRF" in param:
                    try: crf_val = int(re.search(r'CRF (\d+)', param).group(1))
                    except: pass
                success, msg = self.engine.compress_video(inp, out, crf=crf_val, duration=total_duration, callback=update_tool_progress)

            elif act == "fast_cut":
                # Get Times from Spinbox
                if self.tool_start_chk_var.get(): s_str = "00:00:00"
                else: s_str = self.tool_start_entry.get()
                
                if self.tool_end_chk_var.get(): e_str = None
                else: e_str = self.tool_end_entry.get()
                
                if self.tool_cut_mode_var.get() == "acc":
                     # Advanced
                     success, msg = self.engine.accurate_cut(inp, out, s_str, e_str, duration=total_duration, callback=update_tool_progress)
                else:
                     # Fast
                     success, msg = self.engine.fast_cut(inp, out, s_str, e_str, duration=total_duration, callback=update_tool_progress)

            elif act == "extract_au":
                fmt = "mp3"; bitrate = "192k"
                if "Original" in param: fmt = "copy"
                elif "AAC" in param: fmt = "aac"
                elif "WAV" in param: fmt = "wav"
                if "320" in param: bitrate = "320k"
                success, msg = self.engine.extract_audio(inp, out, format=fmt, bitrate=bitrate, duration=total_duration, callback=update_tool_progress)

            else:
                update_tool_progress(50)
                if act == "fix_rot": success, msg = self.engine.fix_rotation(inp, out, int(param) if param.isdigit() else 0)
                elif act == "norm_au": success, msg = self.engine.normalize_audio(inp, out)
                elif act == "soft_sub": success, msg = self.engine.embed_subtitle(inp, extra, out)
                elif act == "hard_sub": success, msg = self.engine.burn_subtitle(inp, extra, out)
                elif act == "cover": success, msg = self.engine.embed_cover(inp, extra, out)
                elif act == "conv_sub": success, msg = self.engine.convert_subtitle(inp, out) if hasattr(self.engine, 'convert_subtitle') else (False, "Core Error")
                elif act == "to_gif":
                    # Parse time range for GIF
                    parts = extra.split('-')
                    if len(parts) == 2:
                        start_str, end_str = parts[0].strip(), parts[1].strip()
                        success, msg = self.engine.video_to_gif_range(inp, out, start_str, end_str)
                    else:
                        success, msg = self.engine.video_to_gif(inp, out)
                elif act == "gif_to_video":
                    success, msg = self.engine.gif_to_video(inp, out)
                elif act == "mute": success, msg = self.engine.remove_audio(inp, out)

        except Exception as e:
            msg = str(e)
            print(e)
        
        self.after(0, lambda: self._tool_done(success, msg, out))

    def _tool_done(self, success, msg, out_path):
        self.btn_tool_run.configure(state='normal', text=self.T("tool_btn_run"), fg_color=self.current_theme["accent"])
        if success:
            self.lbl_tool_status.configure(text=self.T("tool_msg_success"), text_color=self.current_theme["success"])
            if messagebox.askyesno(self.T("pop_success"), f"{self.T('tool_msg_success')}\nFile: {os.path.basename(out_path)}\n\n{self.T('chk_open_done')}?"):
                self._safe_open_file_on_main_thread(out_path)
        else:
            self.lbl_tool_status.configure(text=self.T("tool_msg_fail"), text_color="red")
            messagebox.showerror(self.T("pop_error"), f"{self.T('tool_msg_fail')}\n{msg}")
    
    # ==========================
    # SETTINGS \& RESTART FUNCTIONS
    # ==========================
    
    def save_settings(self, skip_restart_prompt=False):
        # 1. Capture Network
        self.settings["proxy_url"] = self.proxy_var.get()
        self.settings["geo_bypass_country"] = self.geo_var.get()
        
        # [CUT SETTINGS]
        if hasattr(self, 'cut_method_var'):
            self.settings["cut_method"] = self.cut_method_var.get()
        
        # Handle Display Vars if they exist (were created in settings tab), else fallback to internal vars or defaults
        if hasattr(self, 'browser_display_var'):
            self.settings["browser_source"] = self.browser_display_var.get().lower()
            self.browser_var.set(self.settings["browser_source"]) # Sync back
        else:
            self.settings["browser_source"] = self.browser_var.get()
        
        # 2. Capture Format
        if hasattr(self, 'video_ext_display_var'):
            self.settings["default_video_ext"] = self.video_ext_display_var.get().lower()
            self.video_ext_var.set(self.settings["default_video_ext"])
        else:
            self.settings["default_video_ext"] = self.video_ext_var.get()
            
        if hasattr(self, 'audio_ext_display_var'):
            self.settings["default_audio_ext"] = self.audio_ext_display_var.get().lower()
            self.audio_ext_var.set(self.settings["default_audio_ext"])
        else:
            self.settings["default_audio_ext"] = self.audio_ext_var.get()

        self.settings["video_codec_priority"] = self.codec_var.get() if hasattr(self, 'codec_var') else "auto"
        self.settings["embed_thumbnail"] = self.thumb_embed_var.get()
        
        # 3. Capture System
        self.settings["language"] = self.lang_var.get()
        self.settings["theme"] = self.theme_var.get()
        self.settings["add_metadata"] = self.meta_var.get()
        self.settings["minimize_to_tray"] = self.tray_var.get()
        self.settings["run_on_startup"] = self.startup_var.get()
        self.settings["auto_paste"] = self.auto_paste_var.get()
        self.settings["show_finished_popup"] = self.show_popup_var.get()
        self.settings["auto_check_update"] = self.auto_update_var.get()
        
        # 4. Capture Advanced (Vars in setup_settings but also used globally)
        self.settings["split_chapters"] = self.chapter_var.get()
        self.settings["use_archive"] = self.archive_var.get()
        
        # 5. Capture SponsorBlock
        self.settings["enable_sponsorblock"] = any([
            self.sb_sponsor_var.get(), self.sb_intro_var.get(), self.sb_outro_var.get(),
            self.sb_selfpromo_var.get(), self.sb_interaction_var.get(), 
            self.sb_music_off_var.get(), self.sb_preview_var.get()
        ])
        
        self.settings["sb_sponsor"] = self.sb_sponsor_var.get()
        self.settings["sb_intro"] = self.sb_intro_var.get()
        self.settings["sb_outro"] = self.sb_outro_var.get()
        self.settings["sb_selfpromo"] = self.sb_selfpromo_var.get()
        self.settings["sb_interaction"] = self.sb_interaction_var.get()
        self.settings["sb_music_offtopic"] = self.sb_music_off_var.get()
        self.settings["sb_preview"] = self.sb_preview_var.get()

        # Save to disk
        if self.config_mgr.save_settings(self.settings):
            # Check if theme or language changed (requires restart)
            old_lang = self.lang  # Set during __init__
            old_theme = ctk.get_appearance_mode()  # Current theme before save
            
            new_lang = self.lang_var.get()
            new_theme = self.theme_var.get()
            
            needs_restart = (new_lang != old_lang) or (new_theme != old_theme)
            
            # Apply Theme immediately (will take effect for some elements)
            ctk.set_appearance_mode(new_theme)
            
            # Update auto-start registry
            threading.Thread(target=set_autostart_registry, args=(self.startup_var.get(),), daemon=True).start()
            
            # Show success message (only if not skipping restart prompt)
            if not skip_restart_prompt:
                messagebox.showinfo(self.T("pop_info"), self.T("msg_saved"))
            
            # Ask for restart if theme/language changed (unless skipping)
            if needs_restart and not skip_restart_prompt:
                # Create bilingual message based on current language
                lang = self.lang_var.get()
                if lang == "vi":
                    restart_msg = "Cài đặt đã lưu!\n\nKhởi động lại ứng dụng để áp dụng thay đổi theme/ngôn ngữ?"
                elif lang == "zh":
                    restart_msg = "设置已保存！\n\n重启应用以应用主题/语言更改？"
                elif lang == "ja":
                    restart_msg = "設定が保存されました！\n\nテーマ/言語の変更を適用するためにアプリを再起動しますか？"
                elif lang == "ko":
                    restart_msg = "설정이 저장되었습니다!\n\n테마/언어 변경을 적용하려면 앱을 다시 시작하시겠습니까?"
                elif lang == "es":
                    restart_msg = "¡Configuración guardada!\n\n¿Reiniciar la aplicación para aplicar cambios de tema/idioma?"
                elif lang == "ru":
                    restart_msg = "Настройки сохранены!\n\nПерезапустить приложение для применения изменений темы/языка?"
                elif lang == "fr":
                    restart_msg = "Paramètres enregistrés!\n\nRedémarrer l'application pour appliquer les changements de thème/langue?"
                elif lang == "pt":
                    restart_msg = "Configurações salvas!\n\nReiniciar o aplicativo para aplicar alterações de tema/idioma?"
                elif lang == "de":
                    restart_msg = "Einstellungen gespeichert!\n\nApp neu starten, um Theme-/Sprachänderungen anzuwenden?"
                else:  # English default
                    restart_msg = "Settings saved!\n\nRestart app to apply theme/language changes?"
                
                if messagebox.askyesno(self.T("pop_confirm"), restart_msg):
                    self.restart_app()

    def on_theme_change_ui(self, value):
        """Update theme variable when user changes theme in settings"""
        if value == self.T("val_theme_light"): 
            self.theme_var.set("Light")
        else: 
            self.theme_var.set("Dark")
        # Note: Restart will be prompted when user clicks Save

    def on_lang_change_ui(self, value):
        """Update language variable when user changes language in settings"""
        if hasattr(self, 'LANG_MAP') and value in self.LANG_MAP:
            self.lang_var.set(self.LANG_MAP[value])
        # Note: Restart will be prompted when user clicks Save

    def _prompt_restart_for_settings(self):
        """Ask user if they want to restart app after changing theme/language"""
        if messagebox.askyesno(self.T("pop_confirm"), self.T("msg_restart_confirm")):
            self.restart_app()

    def restart_app(self, save_first=False):
        """Force restart the application"""
        import sys
        
        # Only save if explicitly requested (e.g. from Refresh button)
        # NOT when called from save_settings (to avoid loop)
        if save_first:
            self.save_settings(skip_restart_prompt=True)
        
        python = sys.executable
        script = sys.argv[0]
        self.destroy()  # Close current window
        os.execl(python, python, script, *sys.argv[1:])
    
    
    # ==========================
    # DOWNLOAD FUNCTIONS
    # ==========================
    
    def _validate_download_inputs(self):
        if self.cut_var.get():
            s_str = self.start_entry.get().strip()
            e_str = self.end_entry.get().strip()
            s_sec = time_to_seconds(s_str)
            e_sec = time_to_seconds(e_str)
            
            if self.start_chk_var.get(): s_sec = 0
            if self.end_chk_var.get(): e_sec = 999999
            
            if s_sec == -1 or e_sec == -1:
                messagebox.showerror(self.T("pop_error"), self.T("msg_err_time_fmt"))
                return False

            if s_sec >= e_sec:
                messagebox.showerror(self.T("pop_error"), self.T("msg_err_time_order"))
                return False
                
            raw_dur = getattr(self, 'fetched_duration', 0)
            if raw_dur and raw_dur > 0:
                if s_sec >= raw_dur:
                    messagebox.showerror(self.T("pop_error"), self.T("msg_err_start_exceed").format(s_sec, raw_dur))
                    return False
                if not self.end_chk_var.get() and e_sec > raw_dur:
                     messagebox.showwarning(self.T("pop_warning"), self.T("msg_warn_end_exceed").format(raw_dur))

        vid_ext = self.video_ext_var.get()
        codec = self.codec_display_var.get()
        if vid_ext == "webm" and "h264" in codec.lower():
            if messagebox.askyesno(self.T("pop_warning"), self.T("msg_warn_webm_h264")):
                self.codec_display_var.set(self.T("val_codec_auto"))
                self.settings["video_codec_priority"] = "auto"
            else:
                return False 
        
        if self.type_var.get() == "sub_only" and not self.selected_sub_langs:
            messagebox.showerror(self.T("pop_error"), self.T("msg_err_no_sub_lang"))
            self.show_subtitle_selector()
            return False
            
        return True

    def start_download_thread(self):
        if not self._validate_download_inputs(): return
        self.is_cancelled = False
        
        # [UI] Check if Cut Mode - If so, show "Start Cutting" state immediately
        if self.cut_var.get():
             self.download_btn.configure(state="disabled", text=self.T("status_starting"), fg_color="#7f8c8d")
             # Immediate Feedback for Cut
             self.progress_bar.configure(mode="determinate", progress_color="#FF9800")
             self.progress_bar.set(1.0)
             self.status_label.configure(text=self.T("msg_cut_wait"), text_color="#e65100")
        else:
             self.download_btn.configure(state="disabled", text=self.T("status_starting"), fg_color="#7f8c8d") 
        
        self.cancel_btn.configure(state="normal", fg_color="#d32f2f")
        threading.Thread(target=self.run_download_process, daemon=True).start()

    def _ask_playlist_range(self, total_count):
        # Helper to ask range on main thread
        result = {"val": None}
        ev = threading.Event()
        
        def ask():
            ans = simpledialog.askstring(self.T("chk_playlist"), 
                                       self.T("msg_playlist_range").format(total_count),
                                       parent=self)
            result["val"] = ans
            ev.set()
            
        self.after(0, ask)
        ev.wait()
        return result["val"]

    def run_download_process(self):
        # [FIX PLAYLIST] Detect if this is a playlist task
        initial_url = self.url_var.get().strip()
        is_playlist_mode = self.playlist_var.get()
        
        # 0. INIT TASKS
        tasks = list(self.download_queue)
        if not tasks:
            base_task = {
                "url": initial_url, 
                "title": self.fetched_title,
                "is_plist": is_playlist_mode, 
                "name": self.name_var.get().strip(),
                "subs": list(self.selected_sub_langs),
                "sub_format": self.selected_sub_format, 
                "sub_format": self.selected_sub_format, 
                "cut_mode": self.cut_var.get(),
                "cut_correct_mode": (self.cut_mode_var.get() == "acc"),
                "start_time": time_to_seconds(self.start_entry.get()),
                "end_time": time_to_seconds(self.end_entry.get()),
                "dtype": self.type_var.get(),
                "download_sub": True if self.type_var.get() == "sub_only" else self.sub_var.get()
            }
            # Only add if URL exists
            if initial_url: tasks.append(base_task)
        
        if not tasks:
            self.after(0, lambda: self.reset_ui())
            return

        # 1. SETUP SETTINGS
        self.settings["save_path"] = self.path_var.get()
        self.settings["default_video_ext"] = self.video_ext_var.get()
        self.settings["default_audio_ext"] = self.audio_ext_var.get()
        self.settings["browser_source"] = self.browser_var.get()
        self.settings["video_codec_priority"] = self.codec_var.get()
        self.settings["add_metadata"] = self.meta_var.get()
        self.settings["embed_thumbnail"] = self.thumb_embed_var.get()

        success_count = 0
        fail_count = 0
        failed_links = []
        
        self.after(0, lambda: self.download_btn.configure(text=self.T("status_downloading")))

        # 2. PROCESS TASKS
        # [FIX UI] Shared context to allow callbacks to know current task state
        ctx = {'is_cut': False}

        def on_progress_callback(per, msg):
            if self.is_cancelled: return

            # [STRICT FIX] If in Cut Mode, BLINDLY overwrite everything
            if ctx['is_cut']:
                # Force strictly 100% and Wait message
                self.progress_bar.configure(mode="determinate", progress_color="#FF9800") 
                try: self.progress_bar.stop() 
                except: pass
                self.progress_bar.set(1.0)
                
                # Check if it was the magic message, otherwise default to translated wait
                final_msg = self.T("msg_cut_wait")
                self.after(0, lambda: self.status_label.configure(text=final_msg, text_color="#e65100"))
                return

            if msg == "MSG_CUT_WAIT":
                 # Fallback catch
                 msg = self.T("msg_cut_wait")
                 self.progress_bar.configure(progress_color="#FF9800", mode="determinate")
                 self.progress_bar.set(1.0)
            
            elif msg == "SPECIAL_MECHANISM":
                 # [UI] Blue Full Load for Fallback
                 self.progress_bar.configure(progress_color="#2196F3", mode="determinate")
                 try: self.progress_bar.stop()
                 except: pass
                 self.progress_bar.set(1.0)
                 # Message is updated via on_status below, so we just set the visual state here 
            
            elif "Cut" in msg or "Process" in msg or "xử lý" in msg.lower():
                 self.progress_bar.configure(progress_color="#FF9800") # Orange for processing
                 if per == 0:
                     self.progress_bar.configure(mode="indeterminate")
                     try: self.progress_bar.start()
                     except: pass
                 else:
                     self.progress_bar.configure(mode="determinate")
                     try: self.progress_bar.stop() 
                     except: pass
                     self.progress_bar.set(per/100.0)
            else:
                 # Normal Download
                 self.progress_bar.configure(progress_color=self.current_theme["accent"], mode="determinate")
                 try: self.progress_bar.stop()
                 except: pass
                 self.progress_bar.set(per/100.0)

            # Only update text if NOT in cut mode (Cut mode handled above)
            if not ctx['is_cut']:
                self.after(0, lambda: self.status_label.configure(text=msg, text_color=self.current_theme["accent"]))
        
        def on_status_callback(msg):
            # [STRICT FIX] Ignore status updates in Cut Mode unless we want them
            if ctx['is_cut']:
                 # Force Wait Message
                 final_msg = self.T("msg_cut_wait")
                 self.after(0, lambda: self.status_label.configure(text=final_msg, text_color="#e65100"))
                 return

            if msg == "MSG_CUT_WAIT": msg = self.T("msg_cut_wait")
            self.after(0, lambda: self.status_label.configure(text=msg, text_color=("#e65100" if msg == self.T("msg_cut_wait") else self.current_theme["accent"])))

        callbacks = {'on_progress': on_progress_callback, 'on_status': on_status_callback}

        task_queue = list(tasks)
        processed_tasks = 0
        
        while task_queue:
            if self.is_cancelled: 
                self.engine.cancel()
                break
                
            task = task_queue.pop(0) # Get first
            ctx['is_cut'] = task.get("cut_mode", False) # Update context for callbacks
            
            # --- PLAYLIST EXPANSION LOGIC ---
            if task.get("is_plist", False):
                on_status_callback(self.T("status_analyzing_playlist"))
                pl_info = self.engine.extract_playlist_flat(task["url"])
                
                if pl_info and 'entries' in pl_info:
                    entries = list(pl_info['entries'])
                    total = len(entries)
                    
                    # Ask for range if > 20
                    selected_entries = entries
                    if total > 20: 
                        r_str = self._ask_playlist_range(total)
                        if not r_str: r_str = "all" # Default to all if canceled/empty? Or cancel?
                        
                        # Parse Range
                        try:
                            subset = []
                            r_str = r_str.lower().strip()
                            if r_str == "all":
                                subset = entries
                            else:
                                parts = r_str.split(',')
                                for p in parts:
                                    if '-' in p:
                                        s, e = map(int, p.split('-'))
                                        subset.extend(entries[max(0, s-1):min(total, e)])
                                    elif p.strip().isdigit():
                                        idx = int(p.strip())
                                        if 1 <= idx <= total: subset.append(entries[idx-1])
                            if subset: selected_entries = subset
                        except:
                            pass # Fallback to all
                    
                    # Convert to indiv tasks and PREPEND to queue
                    new_subtasks = []
                    for idx, entry in enumerate(selected_entries):
                        t_clone = task.copy()
                        t_clone["is_plist"] = False # Prevent recursion
                        t_clone["url"] = entry.get('url', task["url"])
                        t_clone["title"] = entry.get('title', f"Item {idx+1}")
                        new_subtasks.append(t_clone)
                    
                    # Add to front of queue
                    for t in reversed(new_subtasks):
                         task_queue.insert(0, t)
                         
                    on_status_callback(self.T("status_expanded_playlist").format(len(new_subtasks)))
                    continue # Skip downloading the playlist URL itself
            # --------------------------------
            
            # Normal Download
            on_status_callback(self.T("status_downloading_file").format(task.get('title','...')))
            success, msg, history_item = self.engine.download_single(task, self.settings, callbacks)
            
            if self.is_cancelled: break

            if success: 
                success_count += 1
                if history_item: 
                    self.after(0, lambda h=history_item: self.add_to_history(h))
                    if self.open_finished_var.get() and history_item.get("path"):
                        file_path = history_item["path"]
                        self.after(0, lambda p=file_path: self._safe_open_file_on_main_thread(p))
            else:
                fail_count += 1
                failed_links.append(f"{task.get('title', self.T('val_unknown'))} -> {msg}")
                
                # Smart Cookie Helper: Detect if error might need cookies
                if self._should_suggest_cookies(msg):
                    # Show helper dialog (only for first error in batch)
                    if fail_count == 1:
                        self.after(0, lambda m=msg: self.show_cookie_helper_dialog(m))
            
            
            # Reset bar between tasks
            self.after(0, lambda: self.progress_var.set(0))
            def reset_bar_style():
                self.progress_bar.configure(progress_color=self.current_theme["accent"], mode="determinate")
                try: self.progress_bar.stop()
                except: pass
            self.after(0, reset_bar_style)
            self.after(0, lambda: self.status_label.configure(text="..."))

            # Update Queue UI if strictly following queue mode (optional/visual only)
            if self.download_queue:
                 try: self.download_queue.pop(0) 
                 except: pass
                 # Visual update helper
                 def del_first():
                    ch = self.queue_tree.get_children()
                    if ch: self.queue_tree.delete(ch[0])
                 self.after(0, del_first)
        
        self.after(0, lambda: self.reset_ui())
        self.after(0, lambda: self.progress_var.set(0))

        if self.is_cancelled:
            self.after(0, lambda: self.status_label.configure(text=self.T("status_cancel"), text_color="red"))
        elif fail_count == 0:
            if self.show_popup_var.get():
                self.after(0, lambda: messagebox.showinfo(self.T("pop_success"), self.T("msg_all_done").format(success_count)))
            self.after(0, lambda: self.status_label.configure(text=self.T("status_done"), text_color=self.current_theme["success"]))
        else:
             err_details = "\n".join(failed_links)
             msg_txt = self.T("msg_partial_done").format(success_count, fail_count)
             self.after(0, lambda: messagebox.showwarning(self.T("pop_warning"), f"{msg_txt}\n{err_details}"))

    def reset_ui(self):
        self.download_btn.configure(state="normal", text=self.T("btn_download"), fg_color=self.current_theme["accent"])
        self.cancel_btn.configure(state="disabled", fg_color="gray")

    def _show_first_run_dialog_safe(self):
        """Safe wrapper to show first run dialog after mainloop has started"""
        try:
            # Close splash screen first
            self._close_splash_screen()
            # Show the dialog
            self.show_first_run_language_dialog()
        except Exception as e:
            print(f"Error showing first run dialog: {e}")
            # If dialog fails, save default English settings so app doesn't crash on next start
            self.config_mgr.save_settings(self.settings)

    def _close_splash_screen(self):
        """Close the splash screen process if it's running"""
        try:
            import subprocess
            # Try to find and kill splash screen process
            if sys.platform == 'win32':
                subprocess.run(['taskkill', '/F', '/IM', 'python.exe', '/FI', 'WINDOWTITLE eq TSUFUTUBE*'], 
                             capture_output=True, timeout=1)
        except:
            pass
    
    def show_first_run_language_dialog(self):
        """Show language selection dialog on first run"""
        # Create a modal dialog
        dialog = ctk.CTkToplevel(self)
        dialog.title("Language Selection / Chọn Ngôn Ngữ")
        dialog.geometry("500x600")
        dialog.resizable(False, False)
        
        # Make it modal and center
        dialog.transient(self)
        dialog.grab_set()
        
        # Center on screen
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (500 // 2)
        y = (dialog.winfo_screenheight() // 2) - (600 // 2)
        dialog.geometry(f"+{x}+{y}")
        
        # Main frame
        main_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Header
        ctk.CTkLabel(
            main_frame, 
            text="🌍 Welcome / Chào mừng", 
            font=("Segoe UI", 24, "bold")
        ).pack(pady=(10, 5))
        
        ctk.CTkLabel(
            main_frame,
            text="Please select your language\nVui lòng chọn ngôn ngữ của bạn",
            font=("Segoe UI", 12),
            text_color="gray"
        ).pack(pady=(0, 20))
        
        # Language options with flags and names
        languages = [
            ("en", "🇺🇸", "English"),
            ("vi", "🇻🇳", "Tiếng Việt"),
            ("zh", "🇨🇳", "中文 (简体)"),
            ("ja", "🇯🇵", "日本語"),
            ("ko", "🇰🇷", "한국어"),
            ("es", "🇪🇸", "Español"),
            ("fr", "🇫🇷", "Français"),
            ("de", "🇩🇪", "Deutsch"),
            ("pt", "🇧🇷", "Português"),
            ("ru", "🇷🇺", "Русский"),
        ]
        
        # Use simple dict instead of StringVar to avoid main loop issues
        selection = {"lang": "en"}
        
        # Scrollable frame for languages
        scroll_frame = ctk.CTkScrollableFrame(main_frame, height=350)
        scroll_frame.pack(fill="both", expand=True, pady=10)
        
        def on_select(lang_code):
            selection["lang"] = lang_code
            # Update all buttons
            for btn, code in button_map.items():
                if code == lang_code:
                    btn.configure(fg_color="#2196F3", border_width=2, border_color="#4fc3f7")
                else:
                    btn.configure(fg_color="transparent", border_width=1, border_color="gray")
        
        button_map = {}
        
        for lang_code, flag, lang_name in languages:
            btn = ctk.CTkButton(
                scroll_frame,
                text=f"{flag}  {lang_name}",
                font=("Segoe UI", 14),
                height=50,
                fg_color="transparent",
                border_width=1,
                border_color="gray",
                hover_color="#1565C0",
                anchor="w",
                command=lambda lc=lang_code: on_select(lc)
            )
            btn.pack(fill="x", pady=5, padx=10)
            button_map[btn] = lang_code
        
        # Set default selection (English)
        on_select("en")
        
        # Confirm button
        def confirm():
            lang = selection["lang"]
            # Save to settings
            self.settings["language"] = lang
            self.lang = lang
            self.config_mgr.save_settings(self.settings)
            
            dialog.destroy()
            
            # Restart app to apply new language to all UI elements
            # Since tabs were already created with old language, we need a full restart
            self.restart_app(save_first=False)
        
        ctk.CTkButton(
            main_frame,
            text="✓ Confirm / Xác nhận",
            font=("Segoe UI", 14, "bold"),
            height=45,
            fg_color="#4CAF50",
            hover_color="#388E3C",
            command=confirm
        ).pack(fill="x", pady=(10, 0))
        
        # Wait for user to close dialog
        self.wait_window(dialog)


    
    def show_subtitle_selector(self):
        if hasattr(self, 'sub_selector_window') and self.sub_selector_window is not None and self.sub_selector_window.winfo_exists():
            self.sub_selector_window.lift()
            self.sub_selector_window.focus()
            return

        if not self.available_subtitles:
            messagebox.showinfo("Info", "No subtitles found.")
            self.sub_var.set(False)
            return
            
        top = ctk.CTkToplevel(self)
        self.sub_selector_window = top
        top.title("Select Subtitles")
        top.geometry("500x700")
        top.attributes("-topmost", True)
        
        # Subtitle Format
        fmt_frame = ctk.CTkFrame(top, fg_color="transparent")
        fmt_frame.pack(fill="x", padx=20, pady=10)
        ctk.CTkLabel(fmt_frame, text="Format:", font=("Segoe UI", 12, "bold")).pack(side="left")
        
        fmt_combo = ctk.CTkComboBox(fmt_frame, values=["srt", "ass", "vtt", "lrc", "json3"], state="readonly", width=100)
        fmt_combo.set(self.selected_sub_format) 
        fmt_combo.pack(side="left", padx=10)
        
        # Scrollable Area
        scroll_frame = ctk.CTkScrollableFrame(top)
        scroll_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        self.sub_check_vars = {}

        def draw_section(title, sub_dict, color_header):
            if not sub_dict: return
            
            # Header
            header = ctk.CTkLabel(scroll_frame, text=f"{title} ({len(sub_dict)})", font=("Segoe UI", 12, "bold"), text_color=color_header)
            header.pack(anchor="w", pady=(10, 5))
            
            # Sort: priority langs first
            priority = ['vi', 'en', 'ja', 'ko', 'zh']
            sorted_keys = sorted(sub_dict.keys(), key=lambda x: (x not in priority, x))
            
            for lang_code in sorted_keys:
                subs = sub_dict[lang_code]
                lang_name = subs[0].get('name', lang_code) if subs else lang_code
                
                var = tk.BooleanVar(value=(lang_code in self.selected_sub_langs))
                unique_key = f"{title}_{lang_code}" 
                
                chk = ctk.CTkCheckBox(scroll_frame, text=f"[{lang_code}] {lang_name}", variable=var, font=("Segoe UI", 11))
                chk.pack(anchor="w", padx=10, pady=2)
                
                self.sub_check_vars[unique_key] = {'code': lang_code, 'var': var}

        draw_section("Official Subtitles", getattr(self, 'official_subs', {}), "#4caf50")
        draw_section("Auto-generated", getattr(self, 'auto_subs', {}), "#ff9800")

        def confirm_selection():
            selected_codes = set()
            for key, item in self.sub_check_vars.items():
                if item['var'].get():
                    selected_codes.add(item['code'])
            
            self.selected_sub_langs = list(selected_codes)
            self.selected_sub_format = fmt_combo.get()
            
            count = len(self.selected_sub_langs)
            if count > 0: 
                prefix = "[Locked] " if self.type_var.get() == "sub_only" else ""
                self.sub_chk.configure(text=f"{prefix}Selected {count} ({self.selected_sub_format})")
            else:
                self.sub_var.set(False)
                self.sub_chk.configure(text=self.T("chk_sub"))
                if self.type_var.get() == "sub_only":
                    self.type_var.set("video_1080")

            top.destroy()
            
        ctk.CTkButton(top, text="CONFIRM", command=confirm_selection, height=40).pack(fill="x", padx=20, pady=20)

    def on_sub_toggled(self):
        if not self.sub_var.get(): 
            if self.type_var.get() == "sub_only":
                self.sub_var.set(True)
                return
            self.sub_chk.configure(text=self.T("chk_sub"))
            return
        
        if not self.fetched_title:
            messagebox.showwarning(self.T("pop_warning"), "Please add link and check first.")
            self.sub_var.set(False) 
            return
        if not self.available_subtitles:
            messagebox.showinfo(self.T("pop_warning"), "No allowed subtitles found.")
            self.sub_var.set(False) 
            return
        self.show_subtitle_selector()
        
    def on_sub_only_click(self):
        """When 'Only Subtitles' is selected, show subtitle selector"""
        if not self.fetched_title:
            messagebox.showinfo(self.T("pop_warning"), "Please fetch video info first (paste link and click Check)")
            self.type_var.set("video_1080")  # Reset to default
            return
        if not self.available_subtitles:
            messagebox.showinfo(self.T("pop_warning"), "No subtitles available for this video.")
            self.type_var.set("video_1080")  # Reset to default
            return
        self.show_subtitle_selector()
        
    def on_type_changed(self, *args):
        # If user selects sub_only via trace (not click), also trigger selector
        if self.type_var.get() == "sub_only" and self.available_subtitles:
            self.show_subtitle_selector()

    def add_to_history(self, item):
        item["_checked"] = False
        self.history_data.insert(0, item)
        self.config_mgr.save_history(self.history_data)
        if self.is_history_loaded:
            self.refresh_history_view()

    def refresh_history_view(self):
        if not self.history_tree: return
        
        self.history_tree.delete(*self.history_tree.get_children())
        
        limit = 200
        data_to_show = self.history_data[:limit]
        
        for idx, item in enumerate(data_to_show):
            check_mark = "☑" if item.get("_checked", False) else "☐"
            path = item.get("path", "")
            display_title = item.get("title", "Unknown")
            fmt = item.get("format", "")
            if not fmt and path: 
                try: fmt = os.path.splitext(path)[1].replace(".", "").upper()
                except: fmt = "?"
            
            # Check if file exists on disk
            file_exists = os.path.exists(path) if path else False
            tags = () if file_exists else ('missing',)
            
            # Add visual indicator for missing files
            if not file_exists and path:
                display_title = "[MISSING] " + display_title
            
            self.history_tree.insert("", tk.END, iid=idx, values=(
                check_mark, 
                item.get("platform", "Unknown"), 
                display_title,
                fmt, 
                item.get("size", "0 MB"), 
                item.get("date", "")
            ), tags=tags)
            
        self.update_bulk_btn_state()

    def update_bulk_btn_state(self):
        count = sum(1 for item in self.history_data if item.get("_checked", False))
        if count > 0: 
            self.lbl_del_sel.configure(text=self.T("btn_del_sel").format(count), state="normal", fg_color="#d32f2f")
        else: 
            self.lbl_del_sel.configure(text=self.T("btn_del_sel").format(0), state="disabled", fg_color="gray")
    
    def on_tree_select(self, event):
        """Update button states when row selection changes"""
        # Enable delete button if something is selected OR checked
        sel = self.history_tree.selection()
        checked_count = sum(1 for item in self.history_data if item.get("_checked", False))
        
        # Logic: If checked > 0, button shows count. If checked=0 but row selected, button enabled for single item.
        if checked_count > 0:
            self.lbl_del_sel.configure(text=self.T("btn_del_sel").format(checked_count), state="normal", fg_color="#d32f2f")
        elif sel:
            self.lbl_del_sel.configure(text=self.T("ctx_delete"), state="normal", fg_color="#d32f2f")
        else:
            self.lbl_del_sel.configure(text=self.T("btn_del_sel").format(0), state="disabled", fg_color="gray")

    # ... (Add queue import at top if needed, but we can use queue.Queue if imported or just append to list)
    # Actually, queue module needs import. Assuming it's available or we include it.
    
    def on_history_click(self, event):
        region = self.history_tree.identify("region", event.x, event.y)
        if region == "heading": return
        item_id = self.history_tree.identify_row(event.y)
        col = self.history_tree.identify_column(event.x)
        if item_id and col == "#1":
            try:
                idx = int(item_id)
                if idx < len(self.history_data):
                    self.history_data[idx]["_checked"] = not self.history_data[idx]["_checked"]
                    self.refresh_history_view()
                return "break"
            except ValueError: pass
            
    def on_history_double_click(self, event):
        """Handle double click to open file directly"""
        region = self.history_tree.identify("region", event.x, event.y)
        if region == "heading": return
        
        # Ensure we don't conflict with checkbox click (though regions differ)
        col = self.history_tree.identify_column(event.x)
        if col == "#1": return # Let single click handle checkbox
        
        self.history_open_file() # Re-use single file open logic

    def init_history_tab(self):
        tab = self.tab_view.tab(self.T("tab_history"))
        for w in tab.winfo_children(): w.destroy()
        
        header = ctk.CTkFrame(tab, fg_color="transparent")
        header.pack(fill="x", pady=10)
        ctk.CTkLabel(header, text=self.T("tab_history"), font=("Segoe UI", 20, "bold")).pack(side="left")
        
        btn_box = ctk.CTkFrame(header, fg_color="transparent")
        btn_box.pack(side="right")
        
        ctk.CTkButton(btn_box, text="📂 " + self.T("ctx_open_folder"), command=self.history_open_folder_selected, fg_color="#009688", width=120).pack(side="right", padx=5)
        ctk.CTkButton(btn_box, text="📄 " + self.T("ctx_open_file"), command=self.history_open_file_selected, fg_color="#2196F3", width=120).pack(side="right", padx=5)
        


        # Treeview
        tree_frame = ctk.CTkFrame(tab)
        tree_frame.pack(fill="both", expand=True, pady=10)
        
        cols = ("check", "platform", "title", "fmt", "size", "date")
        self.history_tree = ttk.Treeview(tree_frame, columns=cols, show="headings", selectmode="browse")
        
        self.history_tree.heading("check", text=self.T("col_check"))
        self.history_tree.column("check", width=50, anchor="center")
        self.history_tree.heading("platform", text=self.T("col_platform"))
        self.history_tree.column("platform", width=100, anchor="center")
        self.history_tree.heading("title", text=self.T("col_title"))
        self.history_tree.column("title", width=400)
        self.history_tree.heading("fmt", text="Format")
        self.history_tree.column("fmt", width=80, anchor="center")
        self.history_tree.heading("size", text=self.T("col_size"))
        self.history_tree.column("size", width=100, anchor="center")
        self.history_tree.heading("date", text=self.T("col_date"))
        self.history_tree.column("date", width=150, anchor="center")

        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.history_tree.yview)
        self.history_tree.configure(yscrollcommand=scrollbar.set)
        
        self.history_tree.pack(side="left", fill="both", expand=True, padx=2, pady=2)
        scrollbar.pack(side="right", fill="y")
        
        self.history_tree.bind("<Button-1>", self.on_history_click)
        self.history_tree.bind("<Double-1>", self.on_history_double_click) # [NEW] Double click to open
        self.history_tree.bind("<Button-3>", self.on_history_right_click)
        self.history_tree.bind("<<TreeviewSelect>>", self.on_tree_select) # [NEW] Selection change
        self.create_history_context_menu() # Create menu
        
        # Ensure style is applied
        self.style_treeview()
        # Delay refresh to ensure widget is ready/visible
        self.after(100, self.refresh_history_view)
        
        # Footer Bar (Tools Left, Controls Right)
        footer_bar = ctk.CTkFrame(tab, fg_color="transparent")
        footer_bar.pack(fill="x", pady=10)
        
        # Tools Button (Left)
        ctk.CTkButton(footer_bar, text=self.T("btn_tool_switch"), command=self.history_send_to_tools, fg_color="#FF9800", text_color="black").pack(side="left", padx=5)
        
        # History Controls (Right - Reverse order for pack side=right)
        ctk.CTkButton(footer_bar, text="🔄 Refresh", command=self.refresh_history_view, fg_color="#607D8B", width=100).pack(side="right", padx=5)
        self.lbl_del_sel = ctk.CTkButton(footer_bar, text=self.T("btn_del_sel").format(0), command=self.delete_selected_history, fg_color="#d32f2f", state="disabled")
        self.lbl_del_sel.pack(side="right", padx=5)
        ctk.CTkButton(footer_bar, text=self.T("btn_sel_all"), command=self.history_select_all, width=100).pack(side="right", padx=5)

    def queue_update(self, func):
        self.msg_queue.put(func)

        
        
    def history_send_to_tools(self):
        item = self.get_selected_history_item()
        if not item: return
        path = item.get("path")
        if path and os.path.exists(path):
            self.tool_input_var.set(path)
            self.tab_view.set(self.T("tab_tools"))

    def get_selected_history_item(self):
        sel = self.history_tree.selection()
        if not sel: return None
        try:
            priority_idx = int(sel[0])
            if priority_idx < len(self.history_data):
                return self.history_data[priority_idx]
        except: pass
        return None

    def safe_check_updates(self, manual=False):
        """Legacy method - redirects to new check_for_updates"""
        self.check_for_updates(manual=manual)
    
    def check_for_updates(self, manual=False):
        """Check for updates using the new UpdateChecker module."""
        # Skip if auto-check is disabled and this is not manual
        if not manual and not self.settings.get("auto_check_update", True):
            return
        
        def on_update_result(release_info, checker):
            if release_info:
                # Check if this version was skipped
                skipped_version = self.settings.get("skipped_version", "")
                if not manual and skipped_version == release_info['version']:
                    print(f"Skipping update notification for {skipped_version}")
                    return
                
                # Show update dialog on main thread
                self.after(0, lambda: self.show_update_dialog(release_info, checker))
            elif manual:
                self.after(0, lambda: messagebox.showinfo(
                    self.T("pop_info"), 
                    self.T("update_no_update").format(APP_VERSION)
                ))
        
        # Run check in background
        check_update_async(on_update_result, self.config_mgr)
    
    def show_update_dialog(self, release_info, checker):
        """Show update available dialog with full changelog."""
        dialog = ctk.CTkToplevel(self)
        dialog.title(self.T("update_title"))
        dialog.geometry("550x500")
        dialog.transient(self)
        dialog.grab_set()
        
        # Center on parent
        dialog.update_idletasks()
        x = self.winfo_x() + (self.winfo_width() - 550) // 2
        y = self.winfo_y() + (self.winfo_height() - 500) // 2
        dialog.geometry(f"+{x}+{y}")
        
        # Header
        header = ctk.CTkFrame(dialog, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=(20, 10))
        
        ctk.CTkLabel(header, text="🎉 " + self.T("update_new_version").format(release_info['version']), 
                    font=("Segoe UI", 18, "bold"), text_color="#4CAF50").pack(anchor="w")
        ctk.CTkLabel(header, text=self.T("update_current_version").format(APP_VERSION), 
                    font=("Segoe UI", 12), text_color="gray").pack(anchor="w")
        
        # Changelog section
        ctk.CTkLabel(dialog, text=self.T("update_changelog"), 
                    font=("Segoe UI", 12, "bold")).pack(anchor="w", padx=20, pady=(10, 5))
        
        changelog_frame = ctk.CTkFrame(dialog)
        changelog_frame.pack(fill="both", expand=True, padx=20, pady=5)
        
        changelog_text = ctk.CTkTextbox(changelog_frame, wrap="word", font=("Consolas", 11))
        changelog_text.pack(fill="both", expand=True, padx=5, pady=5)
        changelog_text.insert("1.0", release_info.get('body', 'No changelog available.'))
        changelog_text.configure(state="disabled")
        
        # Skip checkbox
        skip_var = tk.BooleanVar(value=False)
        ctk.CTkCheckBox(dialog, text=self.T("update_chk_no_remind"), 
                       variable=skip_var).pack(anchor="w", padx=20, pady=10)
        
        # Progress bar (hidden initially)
        self.update_progress_var = tk.DoubleVar(value=0)
        self.update_progress_bar = ctk.CTkProgressBar(dialog, variable=self.update_progress_var)
        self.update_progress_label = ctk.CTkLabel(dialog, text="", font=("Segoe UI", 10))
        
        # Buttons
        btn_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=(10, 20))
        
        def on_update_now():
            # Show progress UI
            self.update_progress_bar.pack(fill="x", padx=20, pady=5)
            self.update_progress_label.pack(pady=5)
            self.update_progress_label.configure(text=self.T("update_downloading").format(0))
            
            def progress_callback(progress, downloaded, total):
                self.after(0, lambda: self._update_download_progress(progress))
            
            def do_download():
                try:
                    url = checker.get_download_url()
                    if not url:
                        self.after(0, lambda: messagebox.showerror(
                            self.T("pop_error"), self.T("update_download_failed")))
                        return
                    
                    filepath = checker.download_update(url, progress_callback)
                    if filepath:
                        self.after(0, lambda: self._apply_update(filepath, checker, dialog))
                    else:
                        self.after(0, lambda: messagebox.showerror(
                            self.T("pop_error"), self.T("update_download_failed")))
                except Exception as e:
                    self.after(0, lambda: messagebox.showerror(
                        self.T("pop_error"), f"{self.T('update_download_failed')}\n{e}"))
            
            threading.Thread(target=do_download, daemon=True).start()
        
        def on_skip():
            if skip_var.get():
                self.settings["skipped_version"] = release_info['version']
                self.config_mgr.save_settings(self.settings)
            dialog.destroy()
        
        def on_later():
            dialog.destroy()
        
        def on_github():
            webbrowser.open(release_info.get('html_url', 'https://github.com/tsufuwu/tsufutube_downloader/releases'))
            dialog.destroy()
        
        ctk.CTkButton(btn_frame, text=self.T("update_btn_now"), command=on_update_now,
                     fg_color="#4CAF50", hover_color="#388E3C", width=100).pack(side="left", padx=3)
        ctk.CTkButton(btn_frame, text="⬇ GitHub", command=on_github,
                     fg_color="black", hover_color="#333", width=80).pack(side="left", padx=3)
        ctk.CTkButton(btn_frame, text=self.T("update_btn_skip"), command=on_skip,
                     fg_color="#FF9800", hover_color="#F57C00", width=100).pack(side="left", padx=3)
        ctk.CTkButton(btn_frame, text=self.T("update_btn_later"), command=on_later,
                     fg_color="#757575", hover_color="#616161", width=100).pack(side="left", padx=3)
    
    def _update_download_progress(self, progress):
        """Update the download progress bar."""
        self.update_progress_var.set(progress / 100)
        self.update_progress_label.configure(text=self.T("update_downloading").format(int(progress)))
    
    def _apply_update(self, filepath, checker, dialog):
        """Apply the downloaded update."""
        self.update_progress_label.configure(text=self.T("update_applying"))
        
        if checker.is_portable:
            script = checker.apply_portable_update(filepath)
        else:
            script = checker.apply_installer_update(filepath)
        
        if script:
            messagebox.showinfo(self.T("pop_info"), self.T("update_restart_required"))
            dialog.destroy()
            checker.run_update_script(script)
            self.quit()
        else:
            messagebox.showerror(self.T("pop_error"), self.T("update_download_failed"))

    # Legacy method for backward compatibility
    def show_update_popup(self, latest, url, manual):
        """Legacy popup - kept for compatibility but redirects to new system."""
        if latest and latest != VERSION:
             if messagebox.askyesno("Update", self.T("msg_update_avail").format(latest, VERSION)):
                 webbrowser.open(url)
        elif manual:
             messagebox.showinfo("Update", self.T("msg_latest").format(VERSION))
    
    def show_bug_report(self):
        """Show bug report dialog."""
        import urllib.parse
        import platform
        
        dialog = ctk.CTkToplevel(self)
        dialog.title(self.T("bug_title"))
        dialog.geometry("450x400")
        dialog.transient(self)
        dialog.grab_set()
        
        # Center
        dialog.update_idletasks()
        x = self.winfo_x() + (self.winfo_width() - 450) // 2
        y = self.winfo_y() + (self.winfo_height() - 400) // 2
        dialog.geometry(f"+{x}+{y}")
        
        # Header
        ctk.CTkLabel(dialog, text="🐛 " + self.T("bug_title"), 
                    font=("Segoe UI", 18, "bold")).pack(pady=(20, 10))
        ctk.CTkLabel(dialog, text=self.T("bug_desc"), 
                    font=("Segoe UI", 11), text_color="gray").pack(padx=20)
        
        # Subject
        ctk.CTkLabel(dialog, text=self.T("bug_subject"), 
                    font=("Segoe UI", 11, "bold")).pack(anchor="w", padx=20, pady=(15, 5))
        subject_entry = ctk.CTkEntry(dialog, width=400, placeholder_text="e.g. App crashes when...")
        subject_entry.pack(padx=20)
        
        # Description
        ctk.CTkLabel(dialog, text=self.T("bug_details"), 
                    font=("Segoe UI", 11, "bold")).pack(anchor="w", padx=20, pady=(15, 5))
        desc_text = ctk.CTkTextbox(dialog, width=400, height=120)
        desc_text.pack(padx=20)
        desc_text.insert("1.0", self.T("bug_template"))
        
        def send_report():
            subject = subject_entry.get().strip() or "Bug Report"
            body = desc_text.get("1.0", "end").strip()
            
            # Add system info
            sys_info = f"\n\n--- System Info ---\nApp Version: {VERSION}\nOS: {platform.system()} {platform.release()}\nPython: {platform.python_version()}"
            full_body = body + sys_info
            
            # Create mailto URL
            mailto = f"mailto:phultt.it@gmail.com?subject={urllib.parse.quote(f'[Tsufutube Bug] {subject}')}&body={urllib.parse.quote(full_body)}"
            webbrowser.open(mailto)
            dialog.destroy()
        
        # Buttons
        btn_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        btn_frame.pack(pady=20)
        
        ctk.CTkButton(btn_frame, text=self.T("bug_send"), command=send_report,
                     fg_color="#4CAF50", hover_color="#388E3C", width=120).pack(side="left", padx=5)
        ctk.CTkButton(btn_frame, text=self.T("btn_close"), command=dialog.destroy,
                     fg_color="#757575", hover_color="#616161", width=100).pack(side="left", padx=5)

    def _safe_open_file_on_main_thread(self, path):
        if path and os.path.exists(path):
            try: 
                os.startfile(path)
            except Exception as e: 
                print(f"Open Err: {e}")
        elif path:
            # File doesn't exist - show error popup and refresh history
            messagebox.showerror(
                self.T("pop_error"), 
                f"File not found!\n\nThe file may have been moved or deleted:\n{path}"
            )
            # Automatically refresh history to update missing file indicators
            self.refresh_history_view()

    def create_history_context_menu(self):
        self.history_menu = tk.Menu(self, tearoff=0)
        self.history_menu.add_command(label=self.T("ctx_open_file"), command=self.history_open_file)
        self.history_menu.add_command(label=self.T("ctx_open_folder"), command=self.history_open_folder)
        self.history_menu.add_separator()
        self.history_menu.add_command(label=self.T("btn_tool_switch"), command=self.history_send_to_tools)
        self.history_menu.add_separator()
        self.history_menu.add_command(label=self.T("ctx_delete"), command=self.history_delete_single)

    def on_history_right_click(self, event):
        item_id = self.history_tree.identify_row(event.y)
        if item_id:
            self.history_tree.selection_set(item_id)
            try:
                self.history_menu.tk_popup(event.x_root, event.y_root)
            finally:
                self.history_menu.grab_release()

    # --- CROSS PLATFORM HELPERS ---
    def _native_open(self, path):
        """Open a file or directory using the OS default application."""
        if not path or not os.path.exists(path): return
        
        try:
            if os.name == 'nt':
                os.startfile(path)
            elif sys.platform == 'darwin':
                subprocess.run(['open', path], check=False)
            else: # Linux
                subprocess.run(['xdg-open', path], check=False)
        except Exception as e:
            print(f"Error opening path {path}: {e}")

    def _native_highlight(self, path):
        """Open parent folder and highlight the file."""
        if not path or not os.path.exists(path): return
        
        try:
            if os.name == 'nt':
                subprocess.run(f'explorer /select,"{os.path.abspath(path)}"')
            elif sys.platform == 'darwin':
                subprocess.run(['open', '-R', path], check=False)
            else: # Linux
                # Linux file managers don't have a standard "highlight" command.
                # Just open the parent folder.
                parent = os.path.dirname(path)
                subprocess.run(['xdg-open', parent], check=False)
        except Exception as e:
            print(f"Error highlighting path {path}: {e}")

    def history_open_file(self):
        """Open file from right-click menu (single file)"""
        item = self.get_selected_history_item()
        if item: self._native_open(item.get("path"))

    def history_open_folder(self):
        """Open folder from right-click menu (single file)"""
        item = self.get_selected_history_item()
        if item: self._native_highlight(item.get("path"))
    
    def history_open_file_selected(self):
        """Open all checked files OR current selected row if none checked"""
        selected = [x for x in self.history_data if x.get("_checked")]
        
        # Fallback to selected row if no checkboxes
        if not selected:
             item = self.get_selected_history_item()
             if item: selected = [item]

        if not selected:
            messagebox.showinfo(self.T("pop_info"), "Please select items first")
            return
            
        for item in selected:
            self._native_open(item.get("path"))
    
    def history_open_folder_selected(self):
        """Open folder of first checked file OR selected row"""
        selected = [x for x in self.history_data if x.get("_checked")]
        
        # Fallback to selected row
        if not selected:
             item = self.get_selected_history_item()
             if item: selected = [item]
             
        if not selected:
            messagebox.showinfo(self.T("pop_info"), "Please select items first")
            return
        
        # Open folder of first item (opening multiple folders is chaotic)
        p = selected[0].get("path")
        if p: self._native_highlight(p)

    def delete_selected_history(self):
        to_delete_indices = [i for i, x in enumerate(self.history_data) if x.get("_checked")]
        
        # Fallback: If nothing checked, try deleting currently selected row
        if not to_delete_indices:
             sel = self.history_tree.selection()
             if sel:
                 try: 
                     idx = int(sel[0])
                     if idx < len(self.history_data): to_delete_indices = [idx]
                 except: pass

        count = len(to_delete_indices)
        if count == 0: return

        # Create custom delete dialog
        dialog = ctk.CTkToplevel(self)
        dialog.title(self.T("msg_del_title"))
        dialog.geometry("400x200")
        dialog.resizable(False, False)
        dialog.transient(self)
        dialog.grab_set()
        
        # Center dialog
        dialog.update_idletasks()
        x = self.winfo_x() + (self.winfo_width() // 2) - (400 // 2)
        y = self.winfo_y() + (self.winfo_height() // 2) - (200 // 2)
        dialog.geometry(f"+{x}+{y}")
        
        # Content
        ctk.CTkLabel(dialog, text=self.T("msg_del_confirm"), font=("Segoe UI", 14, "bold")).pack(pady=20)
        ctk.CTkLabel(dialog, text=f"{count} items selected", font=("Segoe UI", 12), text_color="gray").pack(pady=5)
        
        result = {"action": None}
        
        def on_delete_records_only():
            result["action"] = "records_only"
            dialog.destroy()
        
        def on_delete_both():
            result["action"] = "both"
            dialog.destroy()
        
        def on_cancel():
            dialog.destroy()
        
        # Buttons
        btn_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        btn_frame.pack(pady=20, padx=20, fill="x")
        
        ctk.CTkButton(btn_frame, text=self.T("btn_del_rec"), command=on_delete_records_only, 
                     fg_color="#FFA726", hover_color="#FF9800", width=120).pack(side="left", padx=5)
        ctk.CTkButton(btn_frame, text=self.T("btn_del_both"), command=on_delete_both,
                     fg_color="#d32f2f", hover_color="#b71c1c", width=120).pack(side="left", padx=5)
        ctk.CTkButton(btn_frame, text=self.T("btn_del_cancel"), command=on_cancel,
                     fg_color="gray", hover_color="#616161", width=120).pack(side="left", padx=5)
        
        # Wait for dialog
        self.wait_window(dialog)
        
        # Process result
        if result["action"] in ["records_only", "both"]:
            delete_files = (result["action"] == "both")
            
            for i in sorted(to_delete_indices, reverse=True):
                if delete_files:
                    path = self.history_data[i].get("path")
                    if path and os.path.exists(path):
                        try: os.remove(path)
                        except: pass
                self.history_data.pop(i)
            
            self.config_mgr.save_history(self.history_data)
            self.refresh_history_view()

    def history_select_all(self):
        limit = 200
        visible_data = self.history_data[:limit]
        if not visible_data: return
        
        # If all currently visible are checked, uncheck all. Otherwise check all.
        all_checked = all(item.get("_checked", False) for item in visible_data)
        target_state = not all_checked
        
        for item in visible_data: 
            item["_checked"] = target_state
            
        self.refresh_history_view()

    def history_delete_single(self):
        sel = self.history_tree.selection()
        if not sel: return
        idx = int(sel[0])
        if idx < len(self.history_data):
            if messagebox.askyesno(self.T("msg_del_title"), self.T("msg_del_confirm")):
                self.history_data.pop(idx)
                self.config_mgr.save_history(self.history_data)
                self.refresh_history_view()

    def open_donate_link(self): webbrowser.open("https://tsufu.gitbook.io/donate/") 
    def open_update_link(self): webbrowser.open("https://github.com/tsufuwu/tsufutube_downloader")

    def on_window_map(self, event):
        """Called when window is mapped (shown/restored). Do NOT stop tray icon (Persistent Mode)."""
        pass
        # if self.state() == 'normal' and getattr(self, 'tray_icon', None):
        #     try:
        #         self.tray_icon.stop()
        #         self.tray_icon = None
        #     except Exception as e:
        #         print(f"Error stopping tray: {e}")

    def on_close(self):
        if self.settings.get("minimize_to_tray", False):
            self.withdraw()
            # Tray is already running in background if enabled
        else:
            self.destroy()

    def _run_tray_icon(self):
        try:
            try:
                import pystray
                from PIL import Image as PILImage
                global HAS_PYSTRAY 
                HAS_PYSTRAY = True
            except ImportError:
                print("Warning: pystray or PIL not found. Tray icon disabled.")
                return

            image = None
            try:
                image = PILImage.open(resource_path(os.path.join("assets", "icon.ico")))
            except:
                try:
                    image = PILImage.new('RGB', (64, 64), color = 'red')
                except: pass

            if image:
                self.tray_icon = pystray.Icon("Tsufutube", image, "Tsufutube Downloader", menu=pystray.Menu(
                    pystray.MenuItem("Open", self._on_tray_open, default=True),
                    pystray.MenuItem("Exit", self._on_tray_exit)
                ))
                self.tray_icon.run()
        except Exception as e:
            print(f"Tray Error: {e}")

    def _on_tray_open(self, icon, item):
        try:
            self.msg_queue.put(("tray_open", None))
        except Exception as e:
            print(f"Tray Open Error: {e}")

    def _on_tray_exit(self, icon, item):
        try:
            icon.stop()
            self.msg_queue.put(("tray_exit", None))
        except Exception as e:
            print(f"Tray Exit Error: {e}")
        except Exception as e:
            print(f"Tray Error: {e}")
            try: messagebox.showerror("Error", f"Tray Icon Error: {e}")
            except: pass
            self.after(0, self.destroy)
