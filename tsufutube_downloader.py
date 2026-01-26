import sys
import os

# [FIX] Force CWD to App Directory (Fix System32 PermissionError)
if getattr(sys, 'frozen', False):
    os.chdir(os.path.dirname(sys.executable))
else:
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

# --- HANDLING SPLASH PROCESS (BEFORE SINGLE INSTANCE) ---
if "--splash" in sys.argv:
    try:
        from modules import splash_screen
        splash_screen.main()
    except Exception as e:
        # If splash fails, show error (critical for debugging frozen app)
        try:
            import tkinter.messagebox
            import tkinter as tk
            root = tk.Tk()
            root.withdraw()
            tkinter.messagebox.showerror("Splash Error", f"Failed to launch splash: {e}")
            root.destroy()
        except: pass
        # Just exit silently after error to avoid hanging
    sys.exit(0)

# --- FORCE YT-DLP IMPORT (Critical for PyInstaller bundling) ---
try:
    import yt_dlp
    import yt_dlp.utils
    import yt_dlp.extractor
except ImportError:
    pass  # Will be handled later if truly missing

# Import platform utilities for cross-platform support
try:
    from modules import platform_utils
except ImportError:
    platform_utils = None

# [OPTIMIZATION] Single Instance Logic - Run BEFORE any heavy imports
if __name__ == "__main__":
    # --- LAUNCH SPLASH SCREEN IMMEDIATELY ---
    # We spawn a separate process for the splash screen so it animates smoothly
    # while the main process (this one) loads heavy imports.
    # Skip splash when running silently (e.g., on Windows startup)
    splash_process = None
    show_splash = "--silent" not in sys.argv
    
    if show_splash:
        try:
            import subprocess
            
            # Get creation flags for hiding console window (cross-platform)
            creation_flags = platform_utils.get_subprocess_creation_flags() if platform_utils else 0
            
            # Check if running bundled
            if getattr(sys, 'frozen', False):
                # In bundled exe, running the exe with --splash flag IS the splash screen
                splash_process = subprocess.Popen(
                    [sys.executable, '--splash'],
                    creationflags=creation_flags
                )
            else:
                # In dev mode, run the script directly
                script_dir = os.path.dirname(os.path.abspath(__file__))
                splash_script = os.path.join(script_dir, "modules", "splash_screen.py")
                
                if os.path.exists(splash_script):
                    splash_process = subprocess.Popen(
                        [sys.executable, splash_script],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                        creationflags=creation_flags
                    )
        except Exception as e:
            print(f"Splash subprocess error: {e}")

    # --- PLATFORM-SPECIFIC INITIALIZATION ---
    if platform_utils:
        platform_utils.set_dpi_awareness()
        platform_utils.set_app_user_model_id()
    elif os.name == 'nt':
        # Fallback for Windows if platform_utils not available
        try:
            import ctypes
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("tsufu.tsufutube.downloader")
            ctypes.windll.user32.SetProcessDPIAware()
        except: pass

    # --- SINGLE INSTANCE CHECK ---
    if os.name == 'nt':
        # Windows: Use Mutex for single instance
        import ctypes
        ERROR_ALREADY_EXISTS = 183
        SW_RESTORE = 9
        
        mutex_name = "Global\\TsufutubeDownloaderMutex_v1"
        try:
            kernel32 = ctypes.windll.kernel32
            mutex = kernel32.CreateMutexW(None, False, mutex_name)
            last_error = kernel32.GetLastError()
            
            if last_error == ERROR_ALREADY_EXISTS:
                # App is already running - RESTORE IT
                user32 = ctypes.windll.user32
                WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)
                target_hwnd = []
                
                def enum_window_callback(hwnd, _):
                    length = user32.GetWindowTextLengthW(hwnd)
                    if length > 0:
                        buff = ctypes.create_unicode_buffer(length + 1)
                        user32.GetWindowTextW(hwnd, buff, length + 1)
                        if buff.value.startswith("Tsufutube Downloader"):
                            target_hwnd.append(hwnd)
                            return False
                    return True
                    
                try: user32.EnumWindows(WNDENUMPROC(enum_window_callback), 0)
                except: pass
                    
                if target_hwnd:
                    user32.ShowWindow(target_hwnd[0], SW_RESTORE)
                    user32.SetForegroundWindow(target_hwnd[0])
                    
                    # Close Splash if we aren't starting
                    if splash_process:
                        try: splash_process.terminate() 
                        except: pass
                else:
                    # Only import tkinter here if needed for error message
                    # Close splash first
                    if splash_process:
                        try: splash_process.terminate() 
                        except: pass
                        
                    try:
                        import tkinter.messagebox
                        import tkinter as tk
                        root = tk.Tk()
                        root.withdraw() # Hide root window
                        tkinter.messagebox.showinfo("Tsufutube Downloader", "The application is already running in the System Tray.")
                        root.destroy()
                    except: pass
                    
                sys.exit(0)
        except Exception as e:
            print(f"Mutex error: {e}")
    else:
        # Unix (MacOS/Linux): Use file locking for single instance
        if platform_utils and not platform_utils.acquire_single_instance_lock():
            # Another instance is running
            if splash_process:
                try: splash_process.terminate()
                except: pass
            
            try:
                import tkinter.messagebox
                import tkinter as tk
                root = tk.Tk()
                root.withdraw()
                tkinter.messagebox.showinfo("Tsufutube Downloader", "The application is already running.")
                root.destroy()
            except: pass
            
            sys.exit(0)

    # --- FIRST RUN LANGUAGE SELECTION ---
    # Check if settings file exists. If not, show language selection FIRST (quickly)
    import json
    
    # Determine config path (cross-platform)
    # Check for portable 'data' folder first
    exe_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
    portable_data = os.path.join(exe_dir, "data")
    
    if os.path.exists(portable_data):
        config_dir = portable_data
    elif platform_utils:
        config_dir = platform_utils.get_app_data_dir("Tsufutube")
    elif os.name == 'nt': 
        app_data = os.getenv('LOCALAPPDATA') or os.getenv('APPDATA')
        config_dir = os.path.join(app_data, "Tsufutube")
    else: 
        config_dir = os.path.join(os.path.expanduser("~/.config"), "Tsufutube")
    
    settings_file = os.path.join(config_dir, "tsufu_settings.json")
    
    # Default settings template
    DEFAULT_SETTINGS = {
        "language": "en", "theme": "Dark", "minimize_to_tray": True, 
        "auto_clear_link": True, "auto_paste": True, "show_finished_popup": True, 
        "default_video_ext": "mp4", "default_audio_ext": "mp3", 
        "video_codec_priority": "h264", "add_metadata": False, 
        "embed_thumbnail": False, "run_on_startup": True
    }
    
    # Check if first run (no settings file)
    is_first_run = not os.path.exists(settings_file)
    
    if is_first_run:
        # STEP 1: Create config dir and default settings file FIRST
        # If we need input, we might want to kill splash temporarily or just let it run?
        # Actually, showing dialog OVER splash is fine, or kill splash first.
        # Let's kill splash effectively if we need interaction
        if splash_process:
             try: splash_process.terminate()
             except: pass
             splash_process = None

        try:
            if not os.path.exists(config_dir):
                os.makedirs(config_dir)
            # Create default settings file (in case dialog crashes)
            with open(settings_file, "w", encoding="utf-8") as f:
                json.dump(DEFAULT_SETTINGS, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"Error creating default settings: {e}")
        
        # STEP 2: Show ULTRA-MINIMAL language selection (Speed optimized)
        result = {"lang": "en"}
        
        try:
            import tkinter as tk
            
            # Minimal Tk instance - no extra imports
            root = tk.Tk()
            root.title("🌐 Language")
            root.geometry("300x450")
            root.resizable(False, False)
            root.configure(bg="#2b2b2b")
            
            # Center on screen
            root.update_idletasks()
            x = (root.winfo_screenwidth() - 300) // 2
            y = (root.winfo_screenheight() - 450) // 2
            root.geometry(f"+{x}+{y}")
            root.attributes("-topmost", True)
            
            # Language options (minimal)
            langs = [("en", "English"), ("vi", "Tiếng Việt"), ("zh", "中文"), 
                     ("ja", "日本語"), ("ko", "한국어"), ("es", "Español"),
                     ("fr", "Français"), ("de", "Deutsch"), ("pt", "Português"), ("ru", "Русский")]
            
            selected = tk.StringVar(value="en")
            
            # Radio buttons - fastest widget
            for code, name in langs:
                tk.Radiobutton(root, text=name, variable=selected, value=code,
                              font=("Segoe UI", 10), bg="#2b2b2b", fg="white",
                              selectcolor="#444", activebackground="#2b2b2b",
                              activeforeground="white", anchor="w").pack(fill="x", padx=15, pady=1)
            
            def confirm():
                result["lang"] = selected.get()
                try:
                    DEFAULT_SETTINGS["language"] = result["lang"]
                    with open(settings_file, "w", encoding="utf-8") as f:
                        json.dump(DEFAULT_SETTINGS, f, ensure_ascii=False, indent=4)
                except: pass
                root.destroy()
            
            # OK Button
            tk.Button(root, text="OK", command=confirm, font=("Segoe UI", 10, "bold"),
                     bg="#4CAF50", fg="white", height=1, width=10).pack(pady=10)
            
            root.protocol("WM_DELETE_WINDOW", confirm)
            root.mainloop()

        except Exception as e:
            print(f"Dialog Error: {e}")
        
        # Finally re-launch splash if we want (or just proceed to app load)
        # Usually user expects app to load now. Let's restart splash for loading
        try: 
            creation_flags = platform_utils.get_subprocess_creation_flags() if platform_utils else 0
            if getattr(sys, 'frozen', False):
                splash_process = subprocess.Popen([sys.executable, '--splash'], creationflags=creation_flags)
            else:   
                 if os.path.exists(splash_script):
                    splash_process = subprocess.Popen([sys.executable, splash_script], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, creationflags=creation_flags)
        except: pass

    # Note: DrissionPage uses system Chrome/Edge, no browser installation needed

    # Now do the slow stuff while splash is showing
    app = None
    error_msg = None
    
    try:
        # Import (fast if cached)
        from ui.app import YoutubeDownloaderApp
        
        # Create app instance (THIS IS THE SLOW PART - 10+ seconds)
        start_silent = "--silent" in sys.argv
        app = YoutubeDownloaderApp(start_silently=start_silent)
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        error_msg = str(e)
    
    # Kill splash now that app is ready
    # Kill splash now that app is ready
    if splash_process:
        try:
            # Force kill immediately on Windows for responsiveness
            if os.name == 'nt':
                 subprocess.run(['taskkill', '/F', '/PID', str(splash_process.pid)], 
                                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            else:
                 splash_process.terminate()
        except:
             try: splash_process.kill()
             except: pass
    
    # Handle errors
    if error_msg:
        import tkinter as tk
        import tkinter.messagebox
        root = tk.Tk()
        root.withdraw()
        tkinter.messagebox.showerror("Error", f"Startup failed:\n{error_msg}")
        sys.exit(1)
    
    # Run app
    if app:
        app.mainloop()
    else:
        import tkinter as tk
        import tkinter.messagebox
        root = tk.Tk()
        root.withdraw()
        tkinter.messagebox.showerror("Error", "Failed to load app")
        sys.exit(1)
