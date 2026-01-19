# 🔨 Build Script cho Tsufutube Downloader

## Recommended: --onedir (Folder Distribution)

### Build Command (Windows)

```bash
pyinstaller --onedir ^
  --windowed ^
  --name="Tsufutube-Downloader" ^
  --icon=assets/icon.ico ^
  --add-data="assets;assets" ^
  --add-data="data.py;." ^
  --add-binary="ffmpeg/ffmpeg.exe;ffmpeg" ^
  --add-binary="ffmpeg/ffprobe.exe;ffmpeg" ^
  --hidden-import=PIL._tkinter_finder ^
  --hidden-import=selenium ^
  --hidden-import=yt_dlp ^
  --exclude-module=matplotlib ^
  --exclude-module=numpy ^
  --exclude-module=pandas ^
  --noconsole ^
  --clean ^
  "Tsufutube downloader.py"
```

### Giải thích các option:

- `--onedir`: Build thành folder (RECOMMENDED)
- `--windowed`: Không hiện console
- `--name`: Tên file .exe
- `--icon`: Icon file
- `--add-data`: Thêm assets folder
- `--add-binary`: Thêm FFmpeg executables
- `--hidden-import`: Import các module ẩn
- `--exclude-module`: Loại bỏ dependencies không cần (giảm size)
- `--noconsole`: Không hiện cmd window
- `--clean`: Xóa cache cũ trước khi build

### Kết quả:

```
dist/
└── Tsufutube-Downloader/
    ├── Tsufutube-Downloader.exe  ← Main executable (nhỏ, ~10MB)
    ├── _internal/                ← Dependencies
    │   ├── customtkinter/
    │   ├── PIL/
    │   ├── yt_dlp/
    │   ├── ffmpeg/
    │   └── ... (nhiều DLLs)
    ├── assets/
    └── data.py
```

---

## 📦 Package for Distribution

### Option 1: ZIP Archive (RECOMMENDED)

```bash
# Sau khi build xong
cd dist
powershell Compress-Archive -Path "Tsufutube-Downloader" -DestinationPath "Tsufutube-Downloader-v1.0.0-win64.zip"
```

**Ưu điểm:**
- ✅ Dễ upload GitHub (< 100MB sau nén)
- ✅ User extract và chạy
- ✅ Portable, không cần install

### Option 2: Installer (Nâng cao)

Dùng Inno Setup để tạo installer:

```iss
[Setup]
AppName=Tsufutube Downloader
AppVersion=1.0.0
DefaultDirName={pf}\Tsufutube Downloader
DefaultGroupName=Tsufutube Downloader
OutputBaseFilename=Tsufutube-Downloader-Setup-v1.0.0
Compression=lzma2/max
SolidCompression=yes

[Files]
Source: "dist\Tsufutube-Downloader\*"; DestDir: "{app}"; Flags: recursesubdirs

[Icons]
Name: "{group}\Tsufutube Downloader"; Filename: "{app}\Tsufutube-Downloader.exe"
Name: "{commondesktop}\Tsufutube Downloader"; Filename: "{app}\Tsufutube-Downloader.exe"

[Run]
Filename: "{app}\Tsufutube-Downloader.exe"; Description: "Launch Tsufutube Downloader"; Flags: postinstall nowait skipifsilent
```

**Ưu điểm:**
- ✅ Cài đặt vào Program Files
- ✅ Tạo Desktop shortcut
- ✅ Uninstaller tự động
- ✅ Trông professional

---

## 🎯 Recommended Distribution Strategy

**Cung cấp CẢ HAI option:**

### GitHub Release Assets:

```
📦 Tsufutube-Downloader-v1.0.0-win64.zip (Portable)
   Size: ~85MB
   For: Users muốn chạy trực tiếp, không cần install

📦 Tsufutube-Downloader-Setup-v1.0.0.exe (Installer)  
   Size: ~90MB
   For: Users muốn cài đặt vào máy

📄 SHA256SUMS.txt
   Checksums để verify
```

**README.md nên viết:**
```markdown
## 📥 Download

Choose one:

**Option 1: Portable (Recommended for most users)**
- Download: [Tsufutube-v1.0.0-Portable.zip](link)
- Extract and run `Tsufutube-Downloader.exe`
- No installation needed

**Option 2: Installer**
- Download: [Tsufutube-v1.0.0-Setup.exe](link)
- Install to Program Files
- Auto-creates desktop shortcut
```

---

## 🔧 Advanced Optimization

### Giảm kích thước build:

```bash
# 1. Exclude unnecessary modules
--exclude-module=matplotlib
--exclude-module=numpy
--exclude-module=pandas
--exclude-module=scipy
--exclude-module=cv2

# 2. Strip binaries (Linux/Mac)
strip dist/Tsufutube-Downloader/*

# 3. UPX compression (risky, có thể false positive)
--upx-dir=C:\upx
--upx-exclude=vcruntime140.dll
```

### Tối ưu startup:

```python
# Trong main file, lazy import heavy modules
def lazy_import_heavy_modules():
    global yt_dlp, PIL
    import yt_dlp
    from PIL import Image
    
# Gọi khi cần dùng, không import lúc startup
```

---

## 📊 Performance Comparison

| Metric | --onefile | --onedir |
|--------|-----------|----------|
| Build size | 200MB | 150MB (folder) |
| Startup time | 5-10s | <1s ⚡ |
| RAM usage | 300MB | 200MB |
| Antivirus false positive | 40% | 10% |
| Update size | 200MB | 10MB (exe only) |
| Professional | ❌ | ✅ |

---

## ✅ Final Recommendation

**Use --onedir + ZIP for GitHub Release**

Lý do:
1. ⚡ Startup nhanh gấp 10 lần
2. 🛡️ Ít bị antivirus block
3. 🔧 Dễ debug và maintain
4. 📦 User vẫn chỉ cần download 1 file ZIP
5. 💾 Tiết kiệm RAM
6. 🎯 Professional hơn
