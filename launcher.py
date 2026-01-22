import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk
import sys
import os
import json
import subprocess
import ctypes

# Constants
MAIN_EXE = "Tsufutube-Downloader.exe"
DATA_DIR = "data"
SETTINGS_FILE = "tsufu_settings.json"

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

def resource_path(relative_path):
    """Get absolute path to resource for PyInstaller"""
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)

class LauncherApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.title("Tsufutube Setup & Launcher")
        self.geometry("900x650")
        self.resizable(False, False)
        
        # Grid layout
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1) # Main content
        self.grid_rowconfigure(1, weight=0) # Footer
        
        # --- Main Content Frame ---
        self.main_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.main_frame.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
        
        # 1. Header
        self.header = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.header.pack(fill="x", pady=(0, 20))
        ctk.CTkLabel(self.header, text="TSUFUTUBE PORTABLE", font=("Segoe UI", 28, "bold"), text_color="#4fc3f7").pack()
        ctk.CTkLabel(self.header, text="Setup & Launcher", font=("Segoe UI", 14), text_color="gray").pack()
        
        # 2. SmartScreen Guide Section
        self.create_smartscreen_guide()
        
        # 3. Settings Section
        self.create_settings_section()
        
        # --- Footer (Action Bar) ---
        self.footer = ctk.CTkFrame(self, height=80, fg_color="#1a1a2e")
        self.footer.grid(row=1, column=0, sticky="ew")
        self.footer.grid_propagate(False) 
        
        self.btn_launch = ctk.CTkButton(self.footer, text="APPLY & LAUNCH 🚀", 
                                      font=("Segoe UI", 16, "bold"),
                                      height=50, width=300,
                                      fg_color="#00C853", hover_color="#00E676",
                                      command=self.launch_app)
        self.btn_launch.pack(pady=15)
        
    def create_smartscreen_guide(self):
        frame = ctk.CTkFrame(self.main_frame, border_width=1, border_color="#333333")
        frame.pack(fill="x", pady=10)
        
        # Title
        title_frame = ctk.CTkFrame(frame, fg_color="#cf2d2d", height=40, corner_radius=6)
        title_frame.pack(fill="x", padx=10, pady=10)
        ctk.CTkLabel(title_frame, text="⚠️ WINDOWS PROTECTED YOUR PC?", font=("Segoe UI", 16, "bold"), text_color="white").pack(pady=5)
        
        # Content Grid
        grid = ctk.CTkFrame(frame, fg_color="transparent")
        grid.pack(fill="x", padx=10, pady=10)
        
        # Step 1
        step1 = ctk.CTkFrame(grid, fg_color="transparent")
        step1.pack(side="left", expand=True, fill="both", padx=5)
        ctk.CTkLabel(step1, text="Step 1: Click 'More info'", font=("Segoe UI", 14, "bold"), text_color="#4fc3f7").pack(pady=5)
        try:
            img1 = Image.open(resource_path(os.path.join("assets", "install_manual", "step 1.png")))
            # specific size? Keep aspect ratio
            img1.thumbnail((350, 250))
            photo1 = ctk.CTkImage(img1, size=img1.size)
            ctk.CTkLabel(step1, image=photo1, text="").pack(pady=5)
        except Exception as e:
            ctk.CTkLabel(step1, text=f"[Image Not Found: step 1.png]", text_color="red").pack()

        # Step 2
        step2 = ctk.CTkFrame(grid, fg_color="transparent")
        step2.pack(side="left", expand=True, fill="both", padx=5)
        ctk.CTkLabel(step2, text="Step 2: Click 'Run anyway'", font=("Segoe UI", 14, "bold"), text_color="#4fc3f7").pack(pady=5)
        try:
            img2 = Image.open(resource_path(os.path.join("assets", "install_manual", "step 2.png")))
            img2.thumbnail((350, 250))
            photo2 = ctk.CTkImage(img2, size=img2.size)
            ctk.CTkLabel(step2, image=photo2, text="").pack(pady=5)
        except:
             ctk.CTkLabel(step2, text=f"[Image Not Found: step 2.png]", text_color="red").pack()

        ctk.CTkLabel(frame, text="*This warning appears because the app is not signed with a Microsoft Certificate ($$$). It is completely safe.", 
                     font=("Segoe UI", 11, "italic"), text_color="gray").pack(pady=(0, 10))

    def create_settings_section(self):
        frame = ctk.CTkFrame(self.main_frame, border_width=1, border_color="#333333")
        frame.pack(fill="x", pady=10)
        
        ctk.CTkLabel(frame, text="⚙ INITIAL SETUP", font=("Segoe UI", 16, "bold")).pack(pady=10, anchor="w", padx=20)
        
        # Language
        row1 = ctk.CTkFrame(frame, fg_color="transparent")
        row1.pack(fill="x", padx=20, pady=5)
        ctk.CTkLabel(row1, text="Application Language:", width=150, anchor="w").pack(side="left")
        
        self.lang_var = ctk.StringVar(value="English")
        self.lang_map = {
            "English": "en", "Tiếng Việt": "vi", "Deutsch": "de", "Español": "es", 
            "Français": "fr", "日本語": "ja", "한국어": "ko", "Português": "pt", 
            "Русский": "ru", "中文": "zh"
        }
        self.combo_lang = ctk.CTkComboBox(row1, values=list(self.lang_map.keys()), variable=self.lang_var, width=200)
        self.combo_lang.pack(side="left", padx=10)
        
        # Shortcut
        row2 = ctk.CTkFrame(frame, fg_color="transparent")
        row2.pack(fill="x", padx=20, pady=5)
        self.chk_shortcut = ctk.CTkCheckBox(row2, text="Create Desktop Shortcut", onvalue=True, offvalue=False)
        self.chk_shortcut.select()
        self.chk_shortcut.pack(side="left")
        
    def create_desktop_shortcut(self):
        try:
            shell = ctypes.Dispatch("WScript.Shell") # Use ctypes? No, need win32com or simple vbs file execution.
            # Using standard lib: create a .vbs file and run it.
            desktop = os.path.join(os.environ["USERPROFILE"], "Desktop")
            exe_path = os.path.dirname(os.path.abspath(sys.argv[0]))
            target = os.path.join(exe_path, MAIN_EXE)
            
            link_path = os.path.join(desktop, "Tsufutube Downloader.lnk")
            
            vbs_script = f"""
            Set oWS = WScript.CreateObject("WScript.Shell")
            sLinkFile = "{link_path}"
            Set oLink = oWS.CreateShortcut(sLinkFile)
            oLink.TargetPath = "{target}"
            oLink.WorkingDirectory = "{exe_path}"
            oLink.Description = "Tsufutube All-in-One Downloader"
            oLink.IconLocation = "{target},0"
            oLink.Save
            """
            
            vbs_file = os.path.join(exe_path, "create_shortcut.vbs")
            with open(vbs_file, "w") as f:
                f.write(vbs_script)
            
            subprocess.run(["cscript", "//Nologo", vbs_file], check=True)
            os.remove(vbs_file)
            return True
        except Exception as e:
            messagebox.showerror("Error", f"Failed to create shortcut: {e}")
            return False

    def launch_app(self):
        exe_path = os.path.join(os.path.dirname(os.path.abspath(sys.argv[0])), MAIN_EXE)
        
        # 1. Check EXE
        if not os.path.exists(exe_path):
            messagebox.showerror("Error", f"Executable '{MAIN_EXE}' not found in current folder!\n\nPlease place this Launcher inside the Tsufutube Portable folder.")
            return

        # 2. Save Settings
        try:
            exe_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
            data_dir = os.path.join(exe_dir, DATA_DIR)
            if not os.path.exists(data_dir):
                os.makedirs(data_dir)
            
            lang_code = self.lang_map[self.lang_var.get()]
            
            settings_path = os.path.join(data_dir, SETTINGS_FILE)
            
            # Load existing if any
            settings = {}
            if os.path.exists(settings_path):
                try: 
                    with open(settings_path, "r", encoding="utf-8") as f: settings = json.load(f)
                except: pass
            
            # Update Language
            settings["language"] = lang_code
            
            # Save
            with open(settings_path, "w", encoding="utf-8") as f:
                json.dump(settings, f, ensure_ascii=False, indent=4)
                
        except Exception as e:
            messagebox.showwarning("Warning", f"Could not save settings: {e}")
            
        # 3. Create Shortcut
        if self.chk_shortcut.get():
            self.create_desktop_shortcut()
            
        # 4. Launch
        try:
            subprocess.Popen([exe_path], cwd=os.path.dirname(exe_path))
            self.quit()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to launch app: {e}")

if __name__ == "__main__":
    app = LauncherApp()
    app.mainloop()
