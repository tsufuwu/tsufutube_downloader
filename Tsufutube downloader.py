import sys
import ctypes

# --- HANDLING SPLASH PROCESS (BEFORE SINGLE INSTANCE) ---
if "--splash" in sys.argv:
    try:
        import splash_screen
        splash_screen.main()
    except Exception as e:
        # If splash fails, just exit silently
        pass
    sys.exit(0)

# [OPTIMIZATION] Single Instance Logic - Run BEFORE any heavy imports
if __name__ == "__main__":
    # Fix DPI scaling & App ID
    try: 
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("tsufu.tsufutube.downloader")
        ctypes.windll.user32.SetProcessDPIAware()
    except: pass

    # --- SINGLE INSTANCE MUTEX & RESTORE LOGIC ---
    ERROR_ALREADY_EXISTS = 183
    SW_RESTORE = 9
    
    mutex_name = "Global\\TsufutubeDownloaderMutex_v1"
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
        else:
            # Only import tkinter here if needed for error message
            try:
                import tkinter.messagebox
                import tkinter as tk
                root = tk.Tk()
                root.withdraw() # Hide root window
                tkinter.messagebox.showinfo("Tsufutube Downloader", "The application is already running in the System Tray.")
                root.destroy()
            except: pass
            
        sys.exit(0)

    # --- SPLASH SCREEN ---
    # We spawn a separate process for the splash screen so it animates smoothly
    # during the heavy import/init phase of the main app.
    
    import subprocess
    import os
    
    splash_process = None
    is_bundled = getattr(sys, 'frozen', False)
    
    try:
        if is_bundled:
             # In bundled mode, launch OURSELVES with --splash flag
             # This runs the splash logic in a new process using the same exe
             splash_process = subprocess.Popen(
                [sys.executable, "--splash"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW')    else 0
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
