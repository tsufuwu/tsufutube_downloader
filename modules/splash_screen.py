# splash_screen.py - Standalone splash screen process
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import sys
import os
import time
import json

# Translation Dictionary
SPLASH_TEXT = {
    "en": {
        "slogan": "An all-in-one media downloader solution",
        "loading": "Loading...",
        "tip": "Tip: Use Media-Player-Classic for the best experience",
        "msgs": ["Loading modules...", "Initializing UI...", "Preparing engine...", "Almost ready..."]
    },
    "vi": {
        "slogan": "Giải pháp tải xuống đa phương tiện tất cả trong một",
        "loading": "Đang tải...",
        "tip": "Mẹo: Dùng Media-Player-Classic để có trải nghiệm tốt nhất",
        "msgs": ["Đang tải module...", "Khởi tạo giao diện...", "Chuẩn bị engine...", "Sắp xong..."]
    },
    "de": {
        "slogan": "All-in-One Medien-Downloader",
        "loading": "Lädt...",
        "tip": "Tipp: Verwenden Sie Media-Player-Classic",
        "msgs": ["Lade Module...", "GUI initialisieren...", "Engine start...", "Fast fertig..."]
    },
    "es": {
        "slogan": "Solución de descarga multimedia todo en uno",
        "loading": "Cargando...",
        "tip": "Consejo: Usa Media-Player-Classic",
        "msgs": ["Cargando módulos...", "Iniciando UI...", "Preparando motor...", "Casi listo..."]
    },
    "fr": {
        "slogan": "Solution de téléchargement média tout-en-un",
        "loading": "Chargement...",
        "tip": "Astuce : Utilisez Media-Player-Classic",
        "msgs": ["Chargement modules...", "Initialisation UI...", "Préparation moteur...", "Presque prêt..."]
    },
    "ja": {
        "slogan": "オールインワンのメディアダウンローダー",
        "loading": "読み込み中...",
        "tip": "ヒント: Media-Player-Classicの使用を推奨",
        "msgs": ["モジュール読み込み...", "UI初期化中...", "エンジン準備中...", "まもなく完了..."]
    },
    "ko": {
        "slogan": "올인원 미디어 다운로더 솔루션",
        "loading": "로딩 중...",
        "tip": "팁: 최상의 경험을 위해 Media-Player-Classic 사용",
        "msgs": ["모듈 로딩 중...", "UI 초기화 중...", "엔진 준비 중...", "거의 완료..."]
    },
    "pt": {
        "slogan": "Solução de download de mídia tudo-em-um",
        "loading": "Carregando...",
        "tip": "Dica: Use Media-Player-Classic",
        "msgs": ["Carregando módulos...", "Iniciando UI...", "Preparando motor...", "Quase pronto..."]
    },
    "ru": {
        "slogan": "Универсальный загрузчик медиа",
        "loading": "Загрузка...",
        "tip": "Совет: Используйте Media-Player-Classic",
        "msgs": ["Загрузка модулей...", "Инициализация...", "Подготовка...", "Почти готово..."]
    },
    "zh": {
        "slogan": "多合一媒体下载解决方案",
        "loading": "加载中...",
        "tip": "提示：使用 Media-Player-Classic 以获得最佳体验",
        "msgs": ["加载模块...", "初始化界面...", "准备引擎...", "即将完成..."]
    }
}

def resource_path(relative_path):
    """Get absolute path to resource for PyInstaller"""
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        # Dev Mode: Go up one level from 'modules'
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)

def get_language():
    """Detect language from settings file"""
    try:
        # Check for portable 'data' folder first
        exe_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
        portable_data = os.path.join(exe_dir, "data")
        
        if os.path.exists(portable_data):
             config_dir = portable_data
        elif os.name == 'nt': 
            app_data = os.getenv('LOCALAPPDATA') or os.getenv('APPDATA')
            config_dir = os.path.join(app_data, "Tsufutube")
        else: 
            config_dir = os.path.join(os.path.expanduser("~/.config"), "Tsufutube")
        
        settings_file = os.path.join(config_dir, "tsufu_settings.json")
        if os.path.exists(settings_file):
            with open(settings_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("language", "en")
    except:
        pass
    return "en"

def main():
    """Run the splash screen."""
    root = tk.Tk()
    root.overrideredirect(True)
    root.attributes("-topmost", True)
    root.configure(bg="#1a1a2e")
    
    # Language Setup
    lang = get_language()
    texts = SPLASH_TEXT.get(lang, SPLASH_TEXT["en"])
    
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
    tk.Label(frame, text="TSUFUTUBE", font=("Segoe UI", 28, "bold"), fg="#4fc3f7", bg="#1a1a2e").pack(pady=(5, 0))
    tk.Label(frame, text=texts["slogan"], font=("Segoe UI", 12), fg="#888888", bg="#1a1a2e").pack(pady=(0, 15))
    
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
    status_label = tk.Label(frame, text=texts["loading"], font=("Segoe UI", 10), fg="#4fc3f7", bg="#1a1a2e")
    status_label.pack(pady=(0, 5))

    # Tip label
    tk.Label(frame, text=texts["tip"], font=("Segoe UI", 9, "italic"), fg="#aaaaaa", bg="#1a1a2e").pack(pady=(0, 15))
    
    # Status messages
    messages = texts["msgs"]
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
