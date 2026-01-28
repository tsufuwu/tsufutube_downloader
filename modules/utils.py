import os
import sys

# Lazy import or safeguard winreg
try:
    import winreg
except ImportError:
    winreg = None

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        if getattr(sys, 'frozen', False):
             # Fallback for frozen if _MEIPASS is somehow missing (rare)
             base_path = os.path.dirname(sys.executable)
        else:
             # Dev Mode: 'modules' folder is where this file resides
             # We need to go up one level to root
             base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    return os.path.join(base_path, relative_path)

def time_to_seconds(t):
    try:
        parts = list(map(int, t.strip().split(':')))
        if len(parts) == 3: return parts[0]*3600 + parts[1]*60 + parts[2]
        if len(parts) == 2: return parts[0]*60 + parts[1]
        if len(parts) == 1: return parts[0]
        return 0
    except: return -1 # Trả về -1 nếu lỗi parse

def set_autostart_registry(enable=True, app_name="TsufutubeDownloader"):
    """
    Thêm hoặc xóa ứng dụng khỏi Registry Startup của Windows.
    Returns: (success: bool, message: str)
    """
    if sys.platform != 'win32' or winreg is None:
        return False
        
    key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
    
    try:
        # Xác định đường dẫn thực thi
        if getattr(sys, 'frozen', False):
            # Đã build thành .exe (PyInstaller, Nuitka, etc.)
            # sys.executable sẽ trỏ tới file .exe
            exe_path = sys.executable
            cmd = f'"{exe_path}" --silent'
        else:
            # Đang chạy code Python thuần (.py)
            exe_path = sys.executable  # python.exe
            script_path = os.path.abspath(sys.argv[0])
            cmd = f'"{exe_path}" "{script_path}" --silent'
        
        # Mở Key Registry với quyền ghi
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_ALL_ACCESS)
        
        if enable:
            # Thêm vào startup
            winreg.SetValueEx(key, app_name, 0, winreg.REG_SZ, cmd)
            
            # [CLEANUP] Remove old legacy keys if they exist
            try: winreg.DeleteValue(key, "Tsufutube downloader") 
            except: pass
            try: winreg.DeleteValue(key, "Tsufutube-Downloader") # Try another variant just in case if different from current app_name
            except: pass
            
            winreg.CloseKey(key)
            
            # Verify that the entry was created
            verify_key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_READ)
            try:
                value, _ = winreg.QueryValueEx(verify_key, app_name)
                winreg.CloseKey(verify_key)
                if value == cmd:
                    print(f"✓ Added to startup: {app_name}")
                    return True
                else:
                    print(f"Registry value mismatch. Expected: {cmd}, Got: {value}")
                    return False
            except FileNotFoundError:
                winreg.CloseKey(verify_key)
                print("Failed to verify registry entry")
                return False
        else:
            # Xóa khỏi startup
            try:
                winreg.DeleteValue(key, app_name)
                winreg.CloseKey(key)
                print(f"✓ Removed from startup: {app_name}")
                return True
            except FileNotFoundError:
                winreg.CloseKey(key)
                print("Entry already removed or never existed")
                return True
    
    except PermissionError as e:
        print(f"Permission denied. Please run as administrator. Error: {e}")
        return False
    except Exception as e:
        print(f"Registry error: {type(e).__name__} - {e}")
        return False