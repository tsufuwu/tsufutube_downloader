import sys
import ctypes
import os

# [FIX] Force CWD to App Directory (Fix System32 PermissionError)
if getattr(sys, 'frozen', False):
    os.chdir(os.path.dirname(sys.executable))
else:
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

# --- HANDLING SPLASH PROCESS (BEFORE SINGLE INSTANCE) ---
if "--splash" in sys.argv:
    try:
        import splash_screen
        splash_screen.main()
    except Exception as e:
        # If splash fails, just exit silently
        pass
    sys.exit(0)

# --- FORCE YT-DLP IMPORT (Critical for PyInstaller bundling) ---
try:
    import yt_dlp
    import yt_dlp.utils
    import yt_dlp.extractor
except ImportError:
    pass  # Will be handled later if truly missing

# [OPTIMIZATION] Single Instance Logic - Run BEFORE any heavy imports
if __name__ == "__main__":
    # --- LAUNCH SPLASH SCREEN IMMEDIATELY ---
    # We spawn a separate process for the splash screen so it animates smoothly
    # while the main process (this one) loads heavy imports.
    splash_process = None
    try:
        import subprocess
        import os
        
        # Check if running bundled
        if getattr(sys, 'frozen', False):
            # In bundled exe, running the exe with --splash flag IS the splash screen
            splash_process = subprocess.Popen(
                [sys.executable, '--splash'],
                creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0
            )
        else:
            # In dev mode, run the script directly
            script_dir = os.path.dirname(os.path.abspath(__file__))
            splash_script = os.path.join(script_dir, "splash_screen.py")
            
            if os.path.exists(splash_script):
                splash_process = subprocess.Popen(
                    [sys.executable, splash_script],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0
                )
    except Exception as e:
        print(f"Splash subprocess error: {e}")

    # Fix DPI scaling & App ID (Windows Only)
    if os.name == 'nt':
        try: 
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("tsufu.tsufutube.downloader")
            ctypes.windll.user32.SetProcessDPIAware()
        except: pass

        # --- SINGLE INSTANCE MUTEX & RESTORE LOGIC (Windows Only) ---
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

    # --- FIRST RUN LANGUAGE SELECTION ---
    # Check if settings file exists. If not, show language selection FIRST (quickly)
    import json
    
    # Determine config path
    if os.name == 'nt': 
        app_data = os.getenv('LOCALAPPDATA') or os.getenv('APPDATA')
    else: 
        app_data = os.path.expanduser("~/.config")
    
    config_dir = os.path.join(app_data, "Tsufutube")
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
            root.geometry("220x350")
            root.resizable(False, False)
            root.configure(bg="#2b2b2b")
            
            # Center on screen
            root.update_idletasks()
            x = (root.winfo_screenwidth() - 220) // 2
            y = (root.winfo_screenheight() - 320) // 2
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
            if getattr(sys, 'frozen', False):
                splash_process = subprocess.Popen([sys.executable, '--splash'], creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0)
            else:   
                 if os.path.exists(splash_script):
                    splash_process = subprocess.Popen([sys.executable, splash_script], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0)
        except: pass

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
    if splash_process:
        try:
            splash_process.terminate()
            splash_process.wait(timeout=1)
        except:
            try:
                splash_process.kill()
            except:
                pass
    
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
