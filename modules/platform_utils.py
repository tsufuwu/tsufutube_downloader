"""
Platform Utilities - Cross-Platform Abstraction Layer
Provides OS-agnostic implementations for system-specific operations.
Supports Windows, MacOS, and Linux without affecting existing Windows functionality.
"""

import os
import sys
import platform
import subprocess
import tempfile

# =========================================================================
#  CONSTANTS
# =========================================================================

IS_WINDOWS = sys.platform == 'win32'
IS_MACOS = sys.platform == 'darwin'
IS_LINUX = sys.platform.startswith('linux')
IS_FROZEN = getattr(sys, 'frozen', False)

# =========================================================================
#  PATH UTILITIES
# =========================================================================

def get_app_data_dir(app_name: str = "Tsufutube") -> str:
    """
    Get the appropriate application data directory for the current OS.
    - Windows: %LOCALAPPDATA%/AppName or %APPDATA%/AppName
    - MacOS: ~/Library/Application Support/AppName
    - Linux: ~/.config/AppName
    """
    if IS_WINDOWS:
        base = os.getenv('LOCALAPPDATA') or os.getenv('APPDATA') or os.path.expanduser("~")
        return os.path.join(base, app_name)
    elif IS_MACOS:
        return os.path.join(os.path.expanduser("~"), "Library", "Application Support", app_name)
    else:  # Linux and others
        xdg_config = os.getenv('XDG_CONFIG_HOME') or os.path.join(os.path.expanduser("~"), ".config")
        return os.path.join(xdg_config, app_name)


def get_temp_dir(app_name: str = "Tsufutube") -> str:
    """Get a temp directory for the application."""
    return os.path.join(tempfile.gettempdir(), app_name)


def get_executable_dir() -> str:
    """Get the directory containing the main executable or script."""
    if IS_FROZEN:
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


def get_ffmpeg_path() -> str:
    """
    Get the path to FFmpeg executable.
    - Windows: Look for bundled ffmpeg.exe in app directory
    - MacOS/Linux: Look in sys._MEIPASS (bundled), ensure +x permission, then fallback to system
    """
    # Check PyInstaller Temp Dir (sys._MEIPASS) first for bundled assets
    # Fallback to exe dir (folder mode) or dev dir
    base_dir = getattr(sys, '_MEIPASS', get_executable_dir())
    exe_dir = get_executable_dir()
    
    if IS_WINDOWS:
        # Windows: bundled ffmpeg in _MEIPASS or next to exe
        params = [
            os.path.join(base_dir, "ffmpeg", "ffmpeg.exe"),
            os.path.join(exe_dir, "ffmpeg", "ffmpeg.exe")
        ]
        for p in params:
            if os.path.exists(p): return p
            
        return "ffmpeg.exe"
    else:
        # MacOS/Linux: try bundled first
        bundled_paths = [
            os.path.join(base_dir, "ffmpeg", "ffmpeg"),
            os.path.join(base_dir, "bin", "ffmpeg"),
            os.path.join(base_dir, "Resources", "ffmpeg"),  # MacOS .app
            os.path.join(exe_dir, "ffmpeg", "ffmpeg")       # Folder mode fallback
        ]
        
        for path in bundled_paths:
            if os.path.exists(path):
                # [CRITICAL FIX] Ensure executable permission on Linux/Mac
                # PyInstaller extraction might lose +x flag
                try:
                    st = os.stat(path)
                    os.chmod(path, st.st_mode | 0o111) # Add +x
                except Exception as e:
                    print(f"Warning: Failed to set +x on {path}: {e}")
                
                return path
        
        # Try system FFmpeg
        try:
            result = subprocess.run(["which", "ffmpeg"], capture_output=True, text=True)
            if result.returncode == 0:
                path = result.stdout.strip()
                if path: return path
        except:
            pass
        
        # Fallback
        return "ffmpeg"


# =========================================================================
#  SUBPROCESS UTILITIES
# =========================================================================

def get_subprocess_creation_flags() -> int:
    """
    Get platform-appropriate subprocess creation flags.
    Windows: Returns CREATE_NO_WINDOW to hide console windows.
    Others: Returns 0.
    """
    if IS_WINDOWS:
        return getattr(subprocess, 'CREATE_NO_WINDOW', 0x08000000)
    return 0


def get_subprocess_startupinfo():
    """
    Get platform-appropriate subprocess startup info.
    Windows: Returns STARTUPINFO with hidden window flag.
    Others: Returns None.
    """
    if IS_WINDOWS:
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        return startupinfo
    return None


# =========================================================================
#  SINGLE INSTANCE LOCK
# =========================================================================

_lock_file_handle = None

def acquire_single_instance_lock(app_name: str = "TsufutubeDownloader") -> bool:
    """
    Attempt to acquire a single-instance lock.
    Returns True if lock acquired (we are the only instance).
    Returns False if another instance is already running.
    """
    global _lock_file_handle
    
    if IS_WINDOWS:
        # Windows: Use Mutex (handled in main script for compatibility)
        # This function returns True to indicate caller should proceed with Windows-specific logic
        return True
    else:
        # Unix: Use file locking
        import fcntl
        lock_path = os.path.join(tempfile.gettempdir(), f"{app_name}.lock")
        
        try:
            _lock_file_handle = open(lock_path, 'w')
            fcntl.flock(_lock_file_handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            _lock_file_handle.write(str(os.getpid()))
            _lock_file_handle.flush()
            return True
        except (IOError, OSError):
            # Lock already held by another process
            return False


def release_single_instance_lock():
    """Release the single-instance lock."""
    global _lock_file_handle
    
    if _lock_file_handle:
        try:
            if not IS_WINDOWS:
                import fcntl
                fcntl.flock(_lock_file_handle.fileno(), fcntl.LOCK_UN)
            _lock_file_handle.close()
        except:
            pass
        _lock_file_handle = None


# =========================================================================
#  STARTUP / AUTORUN
# =========================================================================

def get_startup_entry_path(app_name: str = "Tsufutube Downloader") -> str:
    """
    Get the path where startup entry should be created.
    - Windows: Startup folder shortcut path (or registry key name)
    - MacOS: ~/Library/LaunchAgents/com.tsufutube.downloader.plist
    - Linux: ~/.config/autostart/tsufutube.desktop
    """
    if IS_WINDOWS:
        startup_folder = os.path.join(
            os.getenv('APPDATA', ''),
            "Microsoft", "Windows", "Start Menu", "Programs", "Startup"
        )
        return os.path.join(startup_folder, f"{app_name}.lnk")
    elif IS_MACOS:
        return os.path.join(
            os.path.expanduser("~"),
            "Library", "LaunchAgents", "com.tsufutube.downloader.plist"
        )
    else:  # Linux
        autostart_dir = os.path.join(
            os.getenv('XDG_CONFIG_HOME', os.path.expanduser("~/.config")),
            "autostart"
        )
        return os.path.join(autostart_dir, "tsufutube.desktop")


def enable_run_on_startup(app_name: str = "Tsufutube Downloader", executable_path: str = None) -> bool:
    """
    Enable application to run on system startup.
    Returns True on success.
    """
    if executable_path is None:
        executable_path = sys.executable if IS_FROZEN else os.path.abspath(__file__)
    
    if IS_WINDOWS:
        return _enable_startup_windows(app_name, executable_path)
    elif IS_MACOS:
        return _enable_startup_macos(app_name, executable_path)
    else:
        return _enable_startup_linux(app_name, executable_path)


def disable_run_on_startup(app_name: str = "Tsufutube Downloader") -> bool:
    """
    Disable application from running on system startup.
    Returns True on success.
    """
    if IS_WINDOWS:
        return _disable_startup_windows(app_name)
    elif IS_MACOS:
        return _disable_startup_macos()
    else:
        return _disable_startup_linux()


def is_run_on_startup_enabled(app_name: str = "Tsufutube Downloader") -> bool:
    """Check if run on startup is currently enabled."""
    startup_path = get_startup_entry_path(app_name)
    return os.path.exists(startup_path)


# --- Windows Startup ---
def _enable_startup_windows(app_name: str, executable_path: str) -> bool:
    """Create Windows startup shortcut."""
    try:
        import winreg
        key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE) as key:
            winreg.SetValueEx(key, app_name, 0, winreg.REG_SZ, f'"{executable_path}" --silent')
        return True
    except Exception as e:
        print(f"Failed to enable startup (Windows): {e}")
        return False


def _disable_startup_windows(app_name: str) -> bool:
    """Remove Windows startup entry."""
    try:
        import winreg
        key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE) as key:
            try:
                winreg.DeleteValue(key, app_name)
            except FileNotFoundError:
                pass  # Already removed
        return True
    except Exception as e:
        print(f"Failed to disable startup (Windows): {e}")
        return False


# --- MacOS Startup ---
def _enable_startup_macos(app_name: str, executable_path: str) -> bool:
    """Create MacOS LaunchAgent plist."""
    plist_path = get_startup_entry_path(app_name)
    plist_dir = os.path.dirname(plist_path)
    
    try:
        os.makedirs(plist_dir, exist_ok=True)
        
        plist_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.tsufutube.downloader</string>
    <key>ProgramArguments</key>
    <array>
        <string>{executable_path}</string>
        <string>--silent</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <false/>
</dict>
</plist>
'''
        with open(plist_path, 'w') as f:
            f.write(plist_content)
        
        return True
    except Exception as e:
        print(f"Failed to enable startup (MacOS): {e}")
        return False


def _disable_startup_macos() -> bool:
    """Remove MacOS LaunchAgent plist."""
    plist_path = get_startup_entry_path()
    try:
        if os.path.exists(plist_path):
            os.remove(plist_path)
        return True
    except Exception as e:
        print(f"Failed to disable startup (MacOS): {e}")
        return False


# --- Linux Startup ---
def _enable_startup_linux(app_name: str, executable_path: str) -> bool:
    """Create Linux XDG autostart .desktop file."""
    desktop_path = get_startup_entry_path(app_name)
    desktop_dir = os.path.dirname(desktop_path)
    
    try:
        os.makedirs(desktop_dir, exist_ok=True)
        
        desktop_content = f'''[Desktop Entry]
Type=Application
Name={app_name}
Exec="{executable_path}" --silent
Hidden=false
NoDisplay=false
X-GNOME-Autostart-enabled=true
Comment=Video Downloader
'''
        with open(desktop_path, 'w') as f:
            f.write(desktop_content)
        
        # Make it executable
        os.chmod(desktop_path, 0o755)
        return True
    except Exception as e:
        print(f"Failed to enable startup (Linux): {e}")
        return False


def _disable_startup_linux() -> bool:
    """Remove Linux XDG autostart entry."""
    desktop_path = get_startup_entry_path()
    try:
        if os.path.exists(desktop_path):
            os.remove(desktop_path)
        return True
    except Exception as e:
        print(f"Failed to disable startup (Linux): {e}")
        return False


# =========================================================================
#  UPDATE SCRIPT GENERATION
# =========================================================================

def create_update_script(source_dir: str, target_dir: str, executable_name: str) -> str:
    """
    Create a platform-appropriate update script.
    Returns path to the script.
    """
    if IS_WINDOWS:
        return _create_update_script_windows(source_dir, target_dir, executable_name)
    else:
        return _create_update_script_unix(source_dir, target_dir, executable_name)


def _create_update_script_windows(source_dir: str, target_dir: str, executable_name: str) -> str:
    """Create Windows batch update script."""
    script_path = os.path.join(tempfile.gettempdir(), 'tsufutube_update.bat')
    
    with open(script_path, 'w', encoding='utf-8') as f:
        f.write('@echo off\n')
        f.write('echo Updating Tsufutube Downloader...\n')
        f.write('timeout /t 2 /nobreak > nul\n')
        f.write(f'xcopy /E /Y /I "{source_dir}\\*" "{target_dir}\\"\n')
        f.write(f'rmdir /S /Q "{source_dir}"\n')
        f.write(f'start "" "{os.path.join(target_dir, executable_name)}"\n')
        f.write('del "%~f0"\n')
    
    return script_path


def _create_update_script_unix(source_dir: str, target_dir: str, executable_name: str) -> str:
    """Create Unix shell update script."""
    script_path = os.path.join(tempfile.gettempdir(), 'tsufutube_update.sh')
    
    with open(script_path, 'w') as f:
        f.write('#!/bin/bash\n')
        f.write('echo "Updating Tsufutube Downloader..."\n')
        f.write('sleep 2\n')
        f.write(f'cp -rf "{source_dir}"/* "{target_dir}/"\n')
        f.write(f'rm -rf "{source_dir}"\n')
        f.write(f'"{os.path.join(target_dir, executable_name)}" &\n')
        f.write('rm -- "$0"\n')  # Self-delete
    
    os.chmod(script_path, 0o755)
    return script_path


def run_update_script(script_path: str):
    """Run the update script in background."""
    if IS_WINDOWS:
        subprocess.Popen(
            ['cmd', '/c', script_path],
            creationflags=get_subprocess_creation_flags(),
            close_fds=True
        )
    else:
        subprocess.Popen(
            ['bash', script_path],
            start_new_session=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )


# =========================================================================
#  BROWSER COOKIE PATHS
# =========================================================================

def get_browser_cookie_paths() -> dict:
    """
    Get default cookie database paths for common browsers on current OS.
    Returns dict: {browser_name: cookie_path}
    """
    home = os.path.expanduser("~")
    
    if IS_WINDOWS:
        local_app_data = os.getenv('LOCALAPPDATA', '')
        return {
            "chrome": os.path.join(local_app_data, "Google", "Chrome", "User Data", "Default", "Network", "Cookies"),
            "edge": os.path.join(local_app_data, "Microsoft", "Edge", "User Data", "Default", "Network", "Cookies"),
            "brave": os.path.join(local_app_data, "BraveSoftware", "Brave-Browser", "User Data", "Default", "Network", "Cookies"),
            "firefox": os.path.join(os.getenv('APPDATA', ''), "Mozilla", "Firefox", "Profiles"),
        }
    elif IS_MACOS:
        return {
            "chrome": os.path.join(home, "Library", "Application Support", "Google", "Chrome", "Default", "Cookies"),
            "edge": os.path.join(home, "Library", "Application Support", "Microsoft Edge", "Default", "Cookies"),
            "brave": os.path.join(home, "Library", "Application Support", "BraveSoftware", "Brave-Browser", "Default", "Cookies"),
            "firefox": os.path.join(home, "Library", "Application Support", "Firefox", "Profiles"),
            "safari": os.path.join(home, "Library", "Cookies", "Cookies.binarycookies"),
        }
    else:  # Linux
        config_home = os.getenv('XDG_CONFIG_HOME', os.path.join(home, ".config"))
        return {
            "chrome": os.path.join(config_home, "google-chrome", "Default", "Cookies"),
            "chromium": os.path.join(config_home, "chromium", "Default", "Cookies"),
            "edge": os.path.join(config_home, "microsoft-edge", "Default", "Cookies"),
            "brave": os.path.join(config_home, "BraveSoftware", "Brave-Browser", "Default", "Cookies"),
            "firefox": os.path.join(home, ".mozilla", "firefox"),
        }


# =========================================================================
#  SYSTEM INTEGRATION
# =========================================================================

def set_dpi_awareness():
    """Set DPI awareness on Windows. No-op on other platforms."""
    if IS_WINDOWS:
        try:
            import ctypes
            ctypes.windll.user32.SetProcessDPIAware()
        except:
            pass


def set_app_user_model_id(app_id: str = "tsufu.tsufutube.downloader"):
    """Set Windows App User Model ID for taskbar grouping. No-op on other platforms."""
    if IS_WINDOWS:
        try:
            import ctypes
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(app_id)
        except:
            pass


def open_file_manager(path: str):
    """Open the system file manager at the specified path."""
    try:
        if IS_WINDOWS:
            os.startfile(os.path.dirname(path))
        elif IS_MACOS:
            subprocess.run(['open', '-R', path])
        else:
            subprocess.run(['xdg-open', os.path.dirname(path)])
    except Exception as e:
        print(f"Failed to open file manager: {e}")


def open_url(url: str):
    """Open URL in default browser."""
    try:
        import webbrowser
        webbrowser.open(url)
    except Exception as e:
        print(f"Failed to open URL: {e}")
