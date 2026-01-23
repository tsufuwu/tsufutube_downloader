# -*- coding: utf-8 -*-
"""
BBDown Engine - Priority Bilibili Downloader
Wrapper for BBDown.exe CLI.
"""
import os
import subprocess
import json
import sys

class BBDownEngine:
    def __init__(self, bbdown_path="BBDown.exe"):
        self.bbdown_path = self._find_bbdown(bbdown_path)

    def _find_bbdown(self, path):
        # Check current dir, bin/, tools/
        dirs = [
            os.getcwd(),
            os.path.join(os.getcwd(), "bin"),
            os.path.join(os.getcwd(), "tools"),
            os.path.dirname(sys.executable)
        ]
        
        # Also check relative to this module
        dirs.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

        target = "BBDown.exe" if sys.platform == "win32" else "BBDown"

        for d in dirs:
            f = os.path.join(d, target)
            if os.path.exists(f):
                return f
        
        # Check PATH
        try:
            subprocess.run([target, "--version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return target
        except:
            return None

    def is_available(self):
        return self.bbdown_path is not None

    def download(self, url, save_dir, callback=None):
        """
        Download using BBDown.
        callback(percent, msg)
        """
        if not self.is_available():
            return False, "BBDown executable not found."

        if callback: callback(0, "Starting BBDown...")
        
        # BBDown commands
        # --work-dir <dir>: set work dir
        # --multi-thread: enable multi-thread
        # --video-only / --audio-only: (optional)
        
        cmd = [
            self.bbdown_path,
            url,
            "--work-dir", save_dir,
            "--file-pattern", "<videoTitle>", # Simple pattern
            "--nop" # No parse (interact)
        ]

        print(f"[BBDown] Running: {' '.join(cmd)}")
        
        try:
            # Creation flags to hide window on Windows
            creation_flags = subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
            
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                encoding='utf-8', 
                errors='ignore',
                creationflags=creation_flags
            )
            
            while True:
                line = process.stdout.readline()
                if not line and process.poll() is not None:
                    break
                
                if line:
                    line = line.strip()
                    # Parse progress if possible
                    # BBDown output format: Progress: 25.55% ...
                    if "%" in line:
                         if callback: callback(50, f"BBDown: {line[-20:]}") # Generic update
            
            if process.returncode == 0:
                return True, "Success"
            else:
                return False, "BBDown returned error code"

        except Exception as e:
            return False, f"BBDown Error: {e}"
