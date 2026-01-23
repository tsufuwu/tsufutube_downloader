# -*- coding: utf-8 -*-
"""
Playwright browser management helper.
Handles browser installation checks and auto-install functionality.
"""
import subprocess
import sys
import os
import shutil
import time

# Error message constants
BROWSER_NOT_FOUND_ERROR = "PLAYWRIGHT_BROWSER_NOT_INSTALLED"


def get_playwright_browsers_path():
    """Get the Playwright browsers installation path."""
    # Default path: %LOCALAPPDATA%\ms-playwright on Windows
    if sys.platform == 'win32':
        local_app_data = os.getenv('LOCALAPPDATA', '')
        if local_app_data:
            return os.path.join(local_app_data, 'ms-playwright')
    elif sys.platform == 'darwin':  # macOS
        return os.path.expanduser('~/Library/Caches/ms-playwright')
    else:  # Linux
        return os.path.expanduser('~/.cache/ms-playwright')
    return None


def check_chromium_installed():
    """
    Check if Playwright chromium browser is installed.
    Returns (is_installed: bool, path: str or None)
    """
    browsers_path = get_playwright_browsers_path()
    if not browsers_path or not os.path.exists(browsers_path):
        print(f"[PlaywrightHelper] Browsers path not found: {browsers_path}")
        return False, None
    
    # Look for chromium folder (e.g., chromium-1200, chromium_headless-shell-1200)
    for item in os.listdir(browsers_path):
        if 'chromium' in item.lower():
            chromium_path = os.path.join(browsers_path, item)
            if os.path.isdir(chromium_path):
                # Check if there's an executable inside
                for root, dirs, files in os.walk(chromium_path):
                    for f in files:
                        if f.endswith('.exe') or f == 'chrome' or f == 'chromium':
                            return True, os.path.join(root, f)
    
    return False, None


def install_playwright_chromium(callback=None):
    """
    Install Playwright chromium browser.
    
    Args:
        callback: Optional function(status, message) for progress updates
    
    Returns:
        (success: bool, message: str)
    """
    try:
        if callback:
            callback("installing", "Đang cài đặt Playwright Chromium...")
        
        cmd = []
        env = os.environ.copy()
        
        # Strategy 1: Find driver directly (Works for both Dev & Frozen if package is importable)
        try:
            import playwright
            base_path = os.path.dirname(os.path.abspath(playwright.__file__))
            driver_dir = os.path.join(base_path, 'driver', 'package', 'bin')
            
            if sys.platform == 'win32':
                driver_exe = os.path.join(driver_dir, 'playwright.cmd')
            else:
                driver_exe = os.path.join(driver_dir, 'playwright')
                
            if os.path.exists(driver_exe):
                print(f"[PlaywrightHelper] Found driver at: {driver_exe}")
                cmd = [driver_exe, 'install']
            else:
                # Fallback: Invoke node.exe directly (common in some wheel distributions)
                # Structure: .../site-packages/playwright/driver/node.exe
                # CLI: .../site-packages/playwright/driver/package/cli.js
                playwright_dir = os.path.join(base_path, 'driver')
                package_dir = os.path.join(playwright_dir, 'package')
                
                node_exe = os.path.join(playwright_dir, 'node.exe')
                cli_js = os.path.join(package_dir, 'cli.js')
                
                if os.path.exists(node_exe) and os.path.exists(cli_js):
                    print(f"[PlaywrightHelper] Found node.exe at: {node_exe}")
                    cmd = [node_exe, cli_js, 'install']
                else:
                    print(f"[PlaywrightHelper] Driver/Node not found. Checked: {driver_exe}, {node_exe}")
                
        except ImportError:
            print("[PlaywrightHelper] Could not import playwright for driver detection")

        # Strategy 2: Fallback to python -m (Only if Strategy 1 failed)
        if not cmd:
            print("[PlaywrightHelper] Falling back to 'python -m playwright'...")
            cmd = [sys.executable, '-m', 'playwright', 'install']

        if not cmd:
            return False, "Could not determine installation command"

        # Execute
        print(f"[PlaywrightHelper] Running install command: {cmd}")
        
        # [FIX] Force PLAYWRIGHT_BROWSERS_PATH to be safe?
        # env['PLAYWRIGHT_BROWSERS_PATH'] = get_playwright_browsers_path()
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=1200,  # 20 minutes
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0,
            env=env
        )
        
        if result.returncode == 0:
            if callback:
                callback("success", "Cài đặt thành công!")
            return True, "Playwright Chromium installed successfully"
        else:
            error_msg = result.stderr or result.stdout or "Unknown error"
            if callback:
                callback("error", f"Lỗi: {error_msg}")
            return False, f"Installation failed: {error_msg}"
            
    except subprocess.TimeoutExpired:
        msg = "Installation timed out after 10 minutes"
        if callback:
            callback("error", msg)
        return False, msg
    except Exception as e:
        msg = f"Installation error: {str(e)}"
        if callback:
            callback("error", msg)
        return False, msg


def is_browser_not_found_error(error_message):
    """
    Check if the error message indicates Playwright browser is not installed.
    """
    if not error_message:
        return False
    
    error_lower = error_message.lower()
    indicators = [
        "executable doesn't exist",
        "executable does not exist",
        "browsertype.launch",
        "playwright install",
        "browser was just installed",
        "chromium_headless",
        "chrome-headless-shell"
    ]
    
    return any(indicator in error_lower for indicator in indicators)


def get_browser_install_instructions():
    """
    Get user-friendly instructions for installing Playwright browsers.
    """
    return {
        "title": "Cần cài đặt trình duyệt Playwright",
        "message": (
            "Tính năng này yêu cầu trình duyệt Chromium của Playwright.\n\n"
            "Bạn có muốn tự động cài đặt không?\n"
            "(Cần kết nối internet, ~200MB)"
        ),
        "manual_command": "python -m playwright install chromium"
    }
