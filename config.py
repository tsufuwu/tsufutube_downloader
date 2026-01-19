import os
import json
from tkinter import messagebox  # Để dùng cho các thông báo lỗi nếu cần

class ConfigManager:
    def __init__(self):
        # --- ĐOẠN NÀY LẤY TỪ PHẦN ĐẦU __INIT__ CỦA CODE GỐC ---
        # Xác định đường dẫn lưu file config
        if os.name == 'nt': 
            app_data = os.getenv('LOCALAPPDATA')
            if not app_data: app_data = os.getenv('APPDATA')
        else: 
            app_data = os.path.expanduser("~/.config")

        self.config_dir = os.path.join(app_data, "Tsufutube")
        if not os.path.exists(self.config_dir):
            try: os.makedirs(self.config_dir)
            except: self.config_dir = os.getcwd() 

        self.settings_file = os.path.join(self.config_dir, "tsufu_settings.json")
        self.history_file = os.path.join(self.config_dir, "tsufu_history.json")

    # --- ĐOẠN NÀY LÀ HÀM load_settings CŨ (đã chỉnh sửa nhẹ) ---
    def load_settings(self, default_settings):
        """
        Load settings từ file JSON.
        Nếu file không tồn tại hoặc lỗi, trả về default_settings.
        """
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, "r", encoding="utf-8") as f:
                    loaded_settings = json.load(f)
                    # Merge với default để đảm bảo không thiếu key
                    for k, v in default_settings.items():
                        loaded_settings.setdefault(k, v)
                    return loaded_settings
            else: 
                return default_settings
        except: 
            return default_settings

    # --- ĐOẠN NÀY LÀ HÀM save_settings CŨ ---
    def save_settings(self, current_settings):
        try:
            with open(self.settings_file, "w", encoding="utf-8") as f: 
                json.dump(current_settings, f, ensure_ascii=False, indent=4)
            return True
        except Exception as e: 
            print(f"Lỗi lưu settings: {e}")
            return False

    # --- ĐOẠN NÀY LÀ HÀM load_history CŨ ---
    def load_history(self):
        try:
            if os.path.exists(self.history_file):
                with open(self.history_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    # Inject trạng thái checked mặc định là False
                    for item in data: item["_checked"] = False
                    return data
            else: 
                return []
        except: 
            return []

    # --- ĐOẠN NÀY LÀ HÀM save_history CŨ ---
    def save_history(self, history_data):
        # Loại bỏ _checked trước khi lưu
        data_to_save = []
        for item in history_data:
            clean_item = item.copy()
            if "_checked" in clean_item: del clean_item["_checked"]
            data_to_save.append(clean_item)
            
        try:
            with open(self.history_file, "w", encoding="utf-8") as f:
                json.dump(data_to_save, f, ensure_ascii=False, indent=4)
        except: pass