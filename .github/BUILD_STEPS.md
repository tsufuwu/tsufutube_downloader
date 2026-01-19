# 📦 Hướng dẫn Build Complete (Portable + Installer)

## 🎯 Tổng quan

Sau khi build xong, bạn sẽ có 2 file để release:

1. **Portable Version** (ZIP): User extract và chạy, không cần install
2. **Installer Version** (EXE): Setup wizard, cài vào Program Files

---

## 📋 Bước 1: Cài đặt Tools

### 1.1. PyInstaller (Đã có)
```bash
pip install pyinstaller
```

### 1.2. Inno Setup (Download)
- **Download:** https://jrsoftware.org/isdl.php
- **Version:** Inno Setup 6.x (latest)
- **Install:** Chạy installer, next next next
- **Path:** Mặc định `C:\Program Files (x86)\Inno Setup 6\`

**Verify installation:**
```bash
# Kiểm tra Inno Setup đã cài chưa
dir "C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
```

---

## 📋 Bước 2: Build với PyInstaller

### 2.1. Prepare FFmpeg binaries

Đảm bảo bạn có FFmpeg:
```
D:\Tsufutube\
├── ffmpeg/
│   ├── ffmpeg.exe
│   └── ffprobe.exe
```

Nếu chưa có, download từ: https://github.com/BtbN/FFmpeg-Builds/releases

### 2.2. Run PyInstaller

```bash
# Di chuyển vào thư mục project
cd D:\Tsufutube

# Build với --onedir
pyinstaller --onedir ^
  --windowed ^
  --icon=assets\icon.ico ^
  --name="Tsufutube-Downloader" ^
  --add-data="assets;assets" ^
  --add-data="data.py;." ^
  --add-binary="ffmpeg\ffmpeg.exe;ffmpeg" ^
  --add-binary="ffmpeg\ffprobe.exe;ffmpeg" ^
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

**Thời gian build:** 2-5 phút (tùy máy)

### 2.3. Kiểm tra kết quả

```
dist/
└── Tsufutube-Downloader/          ← Folder portable
    ├── Tsufutube-Downloader.exe
    ├── _internal/
    └── assets/
```

### 2.4. Test

```bash
# Chạy thử
cd dist\Tsufutube-Downloader
.\Tsufutube-Downloader.exe

# Nếu chạy OK → Tiếp tục bước 3
```

---

## 📋 Bước 3: Tạo Portable ZIP

```bash
# Di chuyển vào thư mục dist
cd dist

# Tạo ZIP với PowerShell
powershell Compress-Archive -Path "Tsufutube-Downloader" -DestinationPath "Tsufutube-v1.0.0-Portable.zip" -Force

# Hoặc dùng 7-Zip (nén tốt hơn)
"C:\Program Files\7-Zip\7z.exe" a -tzip -mx9 "Tsufutube-v1.0.0-Portable.zip" "Tsufutube-Downloader"
```

**Kết quả:**
```
dist/
├── Tsufutube-Downloader/          (folder gốc)
└── Tsufutube-v1.0.0-Portable.zip  ← Upload lên GitHub ✓
```

**File size:** ~80-100MB (sau nén)

---

## 📋 Bước 4: Tạo Installer với Inno Setup

### 4.1. Mở file installer.iss

File `installer.iss` đã được tạo sẵn trong thư mục project.

**Chỉnh sửa nếu cần:**
- Line 4: `#define MyAppPublisher "Your Name"` → Đổi tên
- Line 5: `#define MyAppURL` → Đổi GitHub URL
- Line 10: `AppId` → Generate GUID mới (xem bên dưới)

**Generate GUID:**
```powershell
# Trong PowerShell
[guid]::NewGuid().ToString().ToUpper()
# Output: ABC12345-6789-...
```

### 4.2. Compile Installer

**Option A: Dùng GUI**
1. Mở Inno Setup Compiler
2. File → Open → Chọn `installer.iss`
3. Build → Compile (hoặc F9)
4. Đợi 30-60 giây
5. Done! File installer ở `installer_output/`

**Option B: Dùng Command Line**
```bash
# Compile từ command line
"C:\Program Files (x86)\Inno Setup 6\ISCC.exe" installer.iss
```

### 4.3. Kết quả

```
installer_output/
└── Tsufutube-Downloader-Setup-v1.0.0.exe  ← Upload lên GitHub ✓
```

**File size:** ~85-105MB

### 4.4. Test Installer

```bash
# Chạy thử installer
.\installer_output\Tsufutube-Downloader-Setup-v1.0.0.exe

# Kiểm tra:
# - Cài đặt vào Program Files?
# - Desktop shortcut được tạo?
# - Start Menu được tạo?
# - App chạy được?
# - Uninstaller hoạt động?
```

---

## 📋 Bước 5: Tạo Checksums (SHA256)

```powershell
# Trong PowerShell, cd vào thư mục chứa files

# Tính SHA256 cho Portable
Get-FileHash "Tsufutube-v1.0.0-Portable.zip" -Algorithm SHA256 | Format-List

# Tính SHA256 cho Installer
Get-FileHash "..\installer_output\Tsufutube-Downloader-Setup-v1.0.0.exe" -Algorithm SHA256 | Format-List

# Hoặc tạo file checksums
@"
Tsufutube-v1.0.0-Portable.zip
SHA256: $(Get-FileHash 'Tsufutube-v1.0.0-Portable.zip' -Algorithm SHA256 | Select-Object -ExpandProperty Hash)

Tsufutube-Downloader-Setup-v1.0.0.exe
SHA256: $(Get-FileHash '..\installer_output\Tsufutube-Downloader-Setup-v1.0.0.exe' -Algorithm SHA256 | Select-Object -ExpandProperty Hash)
"@ | Out-File "SHA256SUMS.txt"
```

---

## 📋 Bước 6: Virus Scan (Khuyến nghị)

### Upload lên VirusTotal:
- https://www.virustotal.com/
- Upload cả 2 files
- Đợi scan xong
- Copy link kết quả
- Thêm vào README.md

**Ví dụ:**
```markdown
## 🛡️ Security

Scanned by VirusTotal:
- Portable: [Results](virustotal-link) - 0/70 detections
- Installer: [Results](virustotal-link) - 0/70 detections
```

---

## 📋 Bước 7: Chuẩn bị GitHub Release

### Files cần upload:

```
📦 Tsufutube-v1.0.0-Portable.zip          (85MB)
📦 Tsufutube-Downloader-Setup-v1.0.0.exe  (90MB)
📄 SHA256SUMS.txt                          (1KB)
```

### Release Notes Template:

```markdown
## 📥 Download

**Portable Version (Recommended for most users)**
- [Tsufutube-v1.0.0-Portable.zip](link) (85 MB)
- Extract and run, no installation needed
- SHA256: `xxx...`

**Installer Version**
- [Tsufutube-Downloader-Setup-v1.0.0.exe](link) (90 MB)
- Installs to Program Files
- Creates Desktop shortcut
- SHA256: `xxx...`

### Checksums
See [SHA256SUMS.txt](link) for file verification

### System Requirements
- Windows 10/11 (64-bit)
- 2GB RAM minimum
- 500MB free disk space
```

---

## 🔧 Troubleshooting

### Issue 1: PyInstaller không tìm thấy module
```bash
# Thêm vào command
--hidden-import=<module_name>
```

### Issue 2: Antivirus block file
```bash
# Thử exclude modules không cần thiết
--exclude-module=matplotlib
--exclude-module=numpy
```

### Issue 3: File quá lớn
```bash
# UPX compression (risky)
pip install pyinstaller[encryption]
# Thêm vào command
--upx-dir="C:\upx"
```

### Issue 4: Inno Setup không compile
- Kiểm tra path trong `installer.iss`
- Đảm bảo `dist\Tsufutube-Downloader\` exists
- Check console log trong Inno Setup

---

## ✅ Checklist Cuối

Trước khi upload lên GitHub:

- [ ] Build thành công với PyInstaller
- [ ] Test portable version chạy OK
- [ ] ZIP portable version
- [ ] Compile installer với Inno Setup
- [ ] Test installer (install → run → uninstall)
- [ ] Tạo SHA256 checksums
- [ ] Scan virus (VirusTotal)
- [ ] Kiểm tra file size hợp lý (<100MB)
- [ ] Test trên máy sạch (không có Python)
- [ ] Chuẩn bị release notes

---

## 🎯 Final Structure

```
Your Release Folder/
├── Tsufutube-v1.0.0-Portable.zip         ← Upload GitHub
├── Tsufutube-Downloader-Setup-v1.0.0.exe ← Upload GitHub
└── SHA256SUMS.txt                         ← Upload GitHub
```

**Total upload size:** ~175MB (GitHub allows up to 2GB per release)

---

**Good luck with your build! 🚀**

Need help? Check:
- PyInstaller docs: https://pyinstaller.org/
- Inno Setup docs: https://jrsoftware.org/ishelp/
