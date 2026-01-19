# splash_screen.py - Standalone splash screen process
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import sys
import os
import time

def resource_path(relative_path):
    """Get absolute path to resource for PyInstaller"""
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)

def main():
    """Run the splash screen."""
    root = tk.Tk()
    root.overrideredirect(True)
    root.attributes("-topmost", True)
    root.configure(bg="#1a1a2e")
    
    # Center splash
    w, h = 450, 450
    ws = root.winfo_screenwidth()
    hs = root.winfo_screenheight()
    x = (ws - w) // 2
    y = (hs - h) // 2
    root.geometry(f'{w}x{h}+{x}+{y}')
    
    # Main frame
    frame = tk.Frame(root, bg="#1a1a2e")
    frame.pack(expand=True, fill="both", padx=2, pady=2)
    
    # Load and display splash art image
    try:
        img_path = resource_path(os.path.join("assets", "splash_art.png"))
        img = Image.open(img_path)
        # Resize to smaller size to leave room for progress bar (max 200x200)
        img.thumbnail((200, 200), Image.Resampling.LANCZOS)
        photo = ImageTk.PhotoImage(img)
        
        img_label = tk.Label(frame, image=photo, bg="#1a1a2e")
        img_label.image = photo  # Keep a reference
        img_label.pack(pady=(15, 5))
    except Exception as e:
        # Fallback to emoji if image not found
        print(f"Could not load splash_art.png: {e}")
        tk.Label(frame, text="🎬", font=("Segoe UI Emoji", 36), fg="#4fc3f7", bg="#1a1a2e").pack(pady=(40, 5))
    
    # App title
    # App title
    tk.Label(frame, text="TSUFUTUBE", font=("Segoe UI", 28, "bold"), fg="#4fc3f7", bg="#1a1a2e").pack(pady=(5, 0))
    tk.Label(frame, text="An all-in-one media downloader solution", font=("Segoe UI", 12), fg="#888888", bg="#1a1a2e").pack(pady=(0, 15))
    
    # Progress Bar
    style = ttk.Style()
    style.theme_use('default')
    style.configure("Custom.Horizontal.TProgressbar", 
                   background="#4fc3f7", 
                   troughcolor="#2d2d44",
                   bordercolor="#1a1a2e",
                   lightcolor="#1a1a2e",
                   darkcolor="#1a1a2e",
                   thickness=20)  # Make progress bar more visible
    
    progress = ttk.Progressbar(frame, orient="horizontal", length=320, 
                               mode="indeterminate", style="Custom.Horizontal.TProgressbar")
    progress.pack(pady=(10, 10))
    progress.start(10)  # Faster animation
    
    # Status label
    status_label = tk.Label(frame, text="Loading...", font=("Segoe UI", 10), fg="#4fc3f7", bg="#1a1a2e")
    status_label.pack(pady=(0, 5))

    # Tip label
    tk.Label(frame, text="💡 Tip: Use Media-Player-Classic for the best experience", font=("Segoe UI", 9, "italic"), fg="#aaaaaa", bg="#1a1a2e").pack(pady=(0, 15))
    
    # Status messages
    messages = ["Loading modules...", "Initializing UI...", "Preparing engine...", "Almost ready..."]
    msg_idx = [0]
    start_time = time.time()
    
    def update_status():
        elapsed = time.time() - start_time
        new_idx = min(int(elapsed / 2.5), len(messages) - 1)  # Change every 2.5s
        if new_idx != msg_idx[0]:
            msg_idx[0] = new_idx
            status_label.configure(text=messages[msg_idx[0]])
        root.after(100, update_status)
    
    def check_stdin():
        """Check if parent process sent close signal."""
        try:
            # Non-blocking check (won't work perfectly but good enough)
            root.after(100, check_stdin)
        except:
            root.quit()
    
    update_status()
    check_stdin()
    
    # Run for max 30 seconds then auto-close
    root.after(30000, root.quit)
    
    root.mainloop()

if __name__ == "__main__":
    main()
