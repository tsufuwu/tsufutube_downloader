# tsufutube/data.py

# --- TRANSLATIONS ---
# [OPTIMIZED] Translations are now loaded from assets/locales/{lang}.json
TRANSLATIONS = {}

# --- THEMES ---
THEMES = {
    "Dark": {
        "bg_color": "#212121",
        "card_color": "#303030",
        "text_color": "#ffffff",
        "accent": "#2196F3",
        "success": "#4CAF50"
    },
    "Light": {
        "bg_color": "#f5f5f5",
        "card_color": "#ffffff",
        "text_color": "#000000",
        "accent": "#1976D2",
        "success": "#4CAF50"
    }
}

# --- TIPS CONTENT (Externalized for Multi-line support) ---
TIPS_CONTENT = {
    "vi": """MẸO SỬ DỤNG & THỦ THUẬT (TIPS & TRICKS)

1. SỬ DỤNG MEDIA PLAYER CLASSIC (MPC)
   - Khuyên dùng MPC-HC hoặc MPC-BE để xem video tải về.
   - Đây là trình phát video nhẹ, mượt và hỗ trợ tự động nhận diện Subtitle tốt nhất (hơn hẳn trình mặc định của Win 10/11).
   - Mẹo: Chuột phải vào Video đang phát -> Chọn Subtitles -> Enable để bật/tắt phụ đề nhanh.
   - Tên file subtitle sẽ có dạng "Tên Video.vi.srt" hoặc "Tên Video.en.srt" -> MPC sẽ tự nhận diện và cho phép bạn chọn ngôn ngữ.

2. CÁCH TẠO BẢN DỊCH SUBTITLE AI HOÀN CHỈNH
   (Dành cho video không có sẵn sub tiếng Việt, bạn có thể tự làm bản dịch xịn)

   ► Bước 1: Tải video kèm theo bản subtitle gốc (thường là Tiếng Anh, chọn định dạng .vtt hoặc .srt).
   
   ► Bước 2: Bấm chuột phải vào file .vtt/.srt đã tải -> Open with -> Chọn Notepad (hoặc Text Document, Edit Plus...).
   
   ► Bước 3: Copy toàn bộ nội dung bên trong file đó.
   
   ► Bước 4: Paste vào các mô hình AI (ChatGPT, Gemini, Claude...) hoặc Google Dịch.
      Gõ lệnh: "Dịch nội dung file sub VTT này sang Tiếng Việt, giữ nguyên timecode". Bạn càng cho nhiều thông tin về ngữ cảnh của video, AI càng dịch chính xác.
   
   ► Bước 5: Copy kết quả AI trả về.
      - Quay lại file .vtt cũ, xóa hết nội dung cũ, paste cái mới vào và Save lại.
      - Hoặc tạo file mới với tên GIỐNG HỆT tên video (Ví dụ: Video.mp4 -> Video.vtt).
   
   ► Bước 6: Mở video bằng MPC và thưởng thức thành quả bản dịch của chính bạn!

3. XỬ LÝ NHANH VIDEO (CẮT/NÉN)
    - Ở tab "Lịch sử" (History), bạn có thể chuột phải vào video đã tải -> Chọn "Gửi tới Tools".
    - Tại đó bạn có thể Cắt, Nén, hoặc Đổi đuôi video cực nhanh mà không cần tải lại.

4. TẢI VIDEO CHẤT LƯỢNG CAO (4K/PREMIUM)
    - Để đạt chất lượng tốt nhất hoặc tải video giới hạn độ tuổi, hãy chủ động nhập Cookies của bạn.
    - Bấm nút "Cookies ⚙" ở trang chủ sẽ có hướng dẫn lấy cookies chi tiết.
""",
    "en": """TIPS & TRICKS

1. USE MEDIA PLAYER CLASSIC (MPC)
   - We highly recommend MPC-HC or MPC-BE for watching downloaded videos.
   - It is lightweight, smooth, and handles subtitles much better than the default Windows player.
   - Tip: Right-click the playing video -> Subtitles -> Enable to quickly toggle subtitles.
   - The app preserves subtitle language codes (e.g., "Video.vi.srt"), allowing MPC to automatically detect languages.

2. CREATE PERFECT AI-TRANSLATED SUBTITLES
   (For videos without your native language subtitles)

   ► Step 1: Download the video with the original subtitle (usually English .vtt or .srt).
   
   ► Step 2: Right-click the .vtt/.srt file -> Open with -> Notepad.
   
   ► Step 3: Copy all content inside.
   
   ► Step 4: Paste into AI models (ChatGPT, Gemini, Claude...).
      Prompt: "Translate this VTT subtitle content to [Your Language], keeping the timecodes intact". The more context you provide, the better the translation.
   
   ► Step 5: Copy the AI result.
      - Paste it back into the .vtt file (overwrite old content) and Save.
   
   ► Step 6: Open the video with MPC and enjoy!

3. QUICK TOOLS USAGE (CUT/COMPRESS)
    - In the "History" tab, right-click any downloaded video -> "Send to Tools".
    - You can quickly Cut, Compress, or Convert the video there without re-downloading.

4. DOWNLOAD HIGH QUALITY (4K/PREMIUM)
    - To get the best quality or download age-restricted videos, please import your Cookies.
    - Click the "Cookies ⚙" button on the home screen for detailed instructions.
"""
}