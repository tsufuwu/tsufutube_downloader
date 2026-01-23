# -*- coding: utf-8 -*-
"""
DEPRECATED: Browser helper module.
DrissionPage uses system browser, no installation needed.
This file exists only for backward compatibility.
"""

BROWSER_NOT_FOUND_ERROR = "BROWSER_NOT_FOUND"


def get_playwright_browsers_path():
    """Deprecated - DrissionPage uses system browser."""
    return None


def check_chromium_installed():
    """
    Check if a compatible browser is available.
    DrissionPage uses system Chrome/Edge, so we just check if DrissionPage works.
    Returns (is_available: bool, browser_path: str or None)
    """
    try:
        from DrissionPage import ChromiumPage, ChromiumOptions
        # Try to detect browser
        co = ChromiumOptions()
        co.headless()
        co.set_argument('--no-sandbox')
        
        # This will raise if no browser found
        page = ChromiumPage(co)
        page.quit()
        return True, "System Chrome/Edge"
    except ImportError:
        return False, None
    except Exception as e:
        error_str = str(e).lower()
        if "chrome" in error_str or "edge" in error_str or "browser" in error_str:
            return False, None
        # Other errors might mean browser exists but something else failed
        return True, "System Browser"


def install_playwright_chromium(callback=None):
    """
    Deprecated - DrissionPage uses system browser.
    Returns instructions to install Chrome instead.
    """
    if callback:
        callback("error", "DrissionPage uses your system's Chrome/Edge browser.")
    
    return False, (
        "DrissionPage uses your system's Chrome or Edge browser.\n"
        "Please install Google Chrome or Microsoft Edge to use this feature.\n"
        "Download Chrome: https://www.google.com/chrome/"
    )


def is_browser_not_found_error(error_message):
    """Check if error indicates browser not found."""
    if not error_message:
        return False
    
    error_lower = error_message.lower()
    indicators = [
        "browser_not_found",
        "chrome not found",
        "edge not found", 
        "没有找到",
        "no browser",
        "browsernotfounderror"
    ]
    
    return any(indicator in error_lower for indicator in indicators)


def get_browser_install_instructions():
    """Get instructions for installing a browser."""
    return {
        "title": "Cần cài đặt trình duyệt",
        "message": (
            "Tính năng này yêu cầu Google Chrome hoặc Microsoft Edge.\n\n"
            "Vui lòng cài đặt một trong hai trình duyệt trên.\n"
            "Download Chrome: https://www.google.com/chrome/"
        ),
        "manual_command": "Tải Chrome tại: https://www.google.com/chrome/"
    }
