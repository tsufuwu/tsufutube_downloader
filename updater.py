"""
Tsufutube Downloader - Auto Update Module
Handles checking for updates from GitHub Releases and applying them.
"""

import os
import sys
import json
import threading
import tempfile
import zipfile
import shutil
import subprocess
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError
from packaging import version

from constant import APP_VERSION, REPO_API_URL


class UpdateChecker:
    """Handles checking and applying updates from GitHub Releases."""
    
    def __init__(self, config_mgr=None):
        self.config_mgr = config_mgr
        self.latest_release = None
        self.is_portable = self._detect_install_type()
        
        # Import platform utils for cross-platform support
        try:
            import platform_utils
            self.platform_utils = platform_utils
        except ImportError:
            self.platform_utils = None
    
    def _detect_install_type(self) -> bool:
        """
        Detect if running as Portable or Installed version.
        Returns True if Portable, False if Installed.
        
        Detection logic:
        - Portable: Has 'ffmpeg' folder next to exe OR no uninstall registry
        - Installer: Located in Program Files or has uninstall entry
        - MacOS/Linux: Always treated as Portable (no installer mechanism)
        """
        if not getattr(sys, 'frozen', False):
            # Running from source - treat as Portable for dev
            return True
        
        # MacOS and Linux: Always portable (no installer mechanism yet)
        if sys.platform != 'win32':
            return True
        
        exe_dir = os.path.dirname(sys.executable)
        
        # Check 1: If in Program Files, it's likely installed (Windows only)
        program_files = os.environ.get('PROGRAMFILES', 'C:\\Program Files')
        program_files_x86 = os.environ.get('PROGRAMFILES(X86)', 'C:\\Program Files (x86)')
        
        if exe_dir.startswith(program_files) or exe_dir.startswith(program_files_x86):
            return False  # Installed version
        
        # Check 2: If ffmpeg folder exists next to exe, it's Portable
        if os.path.exists(os.path.join(exe_dir, 'ffmpeg')):
            return True  # Portable version
        
        # Default: Assume Portable
        return True
    
    def check_for_updates(self) -> dict | None:
        """
        Check GitHub for new releases.
        Returns release info dict if update available, None otherwise.
        """
        try:
            req = Request(
                REPO_API_URL,
                headers={'User-Agent': 'Tsufutube-Downloader', 'Accept': 'application/vnd.github.v3+json'}
            )
            
            with urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode('utf-8'))
            
            # Parse version from tag (e.g., "v1.0.1" -> "1.0.1")
            latest_tag = data.get('tag_name', '').lstrip('v')
            
            if not latest_tag:
                return None
            
            # Compare versions
            try:
                current = version.parse(APP_VERSION)
                latest = version.parse(latest_tag)
                
                if latest > current:
                    self.latest_release = {
                        'version': latest_tag,
                        'tag_name': data.get('tag_name'),
                        'name': data.get('name', f'Version {latest_tag}'),
                        'body': data.get('body', ''),  # Changelog/Release notes
                        'html_url': data.get('html_url'),
                        'published_at': data.get('published_at'),
                        'assets': data.get('assets', [])
                    }
                    return self.latest_release
            except Exception as e:
                print(f"Version parse error: {e}")
                return None
                
        except (URLError, HTTPError) as e:
            print(f"Update check failed: {e}")
            return None
        except Exception as e:
            print(f"Unexpected error checking updates: {e}")
            return None
        
        return None
    
    def get_download_url(self) -> str | None:
        """
        Get the appropriate download URL based on install type.
        Returns URL for installer (.exe) or portable (.zip).
        """
        if not self.latest_release:
            return None
        
        assets = self.latest_release.get('assets', [])
        
        for asset in assets:
            name = asset.get('name', '').lower()
            url = asset.get('browser_download_url')
            
            if self.is_portable:
                # Look for portable ZIP
                if 'portable' in name and name.endswith('.zip'):
                    return url
                # Fallback: any ZIP that's not source
                if name.endswith('.zip') and 'source' not in name:
                    return url
            else:
                # Look for installer
                if 'setup' in name and name.endswith('.exe'):
                    return url
                if 'installer' in name and name.endswith('.exe'):
                    return url
                # Fallback: any EXE
                if name.endswith('.exe'):
                    return url
        
        return None
    
    def download_update(self, url: str, progress_callback=None) -> str | None:
        """
        Download update file to temp directory.
        Returns path to downloaded file.
        """
        try:
            req = Request(url, headers={'User-Agent': 'Tsufutube-Downloader'})
            
            # Get filename from URL
            filename = url.split('/')[-1]
            temp_dir = tempfile.gettempdir()
            filepath = os.path.join(temp_dir, filename)
            
            with urlopen(req, timeout=60) as response:
                total_size = int(response.headers.get('Content-Length', 0))
                downloaded = 0
                chunk_size = 8192
                
                with open(filepath, 'wb') as f:
                    while True:
                        chunk = response.read(chunk_size)
                        if not chunk:
                            break
                        f.write(chunk)
                        downloaded += len(chunk)
                        
                        if progress_callback and total_size > 0:
                            progress = (downloaded / total_size) * 100
                            progress_callback(progress, downloaded, total_size)
            
            return filepath
            
        except Exception as e:
            print(f"Download failed: {e}")
            return None
    
    def apply_portable_update(self, zip_path: str) -> bool:
        """
        Apply update for Portable version.
        Extracts ZIP and replaces files (preserving config).
        """
        try:
            exe_dir = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.getcwd()
            
            # Create backup of important files
            config_backup = {}
            config_files = ['tsufu_settings.json']  # Settings are in LOCALAPPDATA, not here
            
            # Extract to temp location first
            temp_extract = os.path.join(tempfile.gettempdir(), 'tsufutube_update')
            if os.path.exists(temp_extract):
                shutil.rmtree(temp_extract)
            
            with zipfile.ZipFile(zip_path, 'r') as zf:
                zf.extractall(temp_extract)
            
            # Find the actual content folder (might be nested)
            extracted_content = temp_extract
            items = os.listdir(temp_extract)
            if len(items) == 1 and os.path.isdir(os.path.join(temp_extract, items[0])):
                extracted_content = os.path.join(temp_extract, items[0])
            
            # Create update script that runs after app closes (cross-platform)
            if self.platform_utils:
                # Determine executable name based on platform
                if sys.platform == 'win32':
                    exe_name = "Tsufutube-Downloader.exe"
                elif sys.platform == 'darwin':
                    exe_name = "Tsufutube Downloader.app/Contents/MacOS/Tsufutube Downloader"
                else:
                    exe_name = "tsufutube-downloader"
                
                update_script = self.platform_utils.create_update_script(
                    extracted_content, exe_dir, exe_name
                )
            else:
                # Fallback: Windows batch script
                update_script = os.path.join(tempfile.gettempdir(), 'tsufutube_update.bat')
                
                with open(update_script, 'w', encoding='utf-8') as f:
                    f.write('@echo off\n')
                    f.write('echo Updating Tsufutube Downloader...\n')
                    f.write('timeout /t 2 /nobreak > nul\n')  # Wait for app to close
                    f.write(f'xcopy /E /Y /I "{extracted_content}\\*" "{exe_dir}\\"\n')
                    f.write(f'rmdir /S /Q "{temp_extract}"\n')
                    f.write(f'start "" "{os.path.join(exe_dir, "Tsufutube-Downloader.exe")}"\n')
                    f.write('del "%~f0"\n')  # Self-delete
            
            return update_script
            
        except Exception as e:
            print(f"Portable update failed: {e}")
            return None
    
    def apply_installer_update(self, installer_path: str) -> bool:
        """
        Apply update for Installed version.
        Runs the installer and exits current app.
        """
        try:
            # Create script to run installer after app closes
            update_script = os.path.join(tempfile.gettempdir(), 'tsufutube_update.bat')
            
            with open(update_script, 'w', encoding='utf-8') as f:
                f.write('@echo off\n')
                f.write('echo Starting Tsufutube Downloader Installer...\n')
                f.write('timeout /t 2 /nobreak > nul\n')  # Wait for app to close
                f.write(f'start "" "{installer_path}"\n')
                f.write('del "%~f0"\n')  # Self-delete
            
            return update_script
            
        except Exception as e:
            print(f"Installer update failed: {e}")
            return None
    
    def run_update_script(self, script_path: str):
        """Run the update script and exit the application (cross-platform)."""
        try:
            if self.platform_utils:
                self.platform_utils.run_update_script(script_path)
            else:
                # Fallback: Windows
                subprocess.Popen(
                    ['cmd', '/c', script_path],
                    creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0,
                    close_fds=True
                )
        except Exception as e:
            print(f"Failed to run update script: {e}")


def check_update_async(callback, config_mgr=None):
    """
    Check for updates in a background thread.
    Calls callback(release_info) when done. release_info is None if no update.
    """
    def _check():
        checker = UpdateChecker(config_mgr)
        result = checker.check_for_updates()
        callback(result, checker)
    
    thread = threading.Thread(target=_check, daemon=True)
    thread.start()
    return thread
