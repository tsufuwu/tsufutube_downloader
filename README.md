<div align="center">

# 🎬 Tsufutube Downloader

### Powerful Multi-Platform Video Downloader
*Download videos from 1000+ websites with advanced features*

[![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)](https://github.com/yourusername/tsufutube-downloader/releases)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/platform-Windows-lightgrey.svg)](https://github.com/yourusername/tsufutube-downloader)
[![Downloads](https://img.shields.io/github/downloads/yourusername/tsufutube-downloader/total.svg)](https://github.com/yourusername/tsufutube-downloader/releases)

[🌐 English](#english) | [🇻🇳 Tiếng Việt](#tiếng-việt)

![Screenshot](assets/screenshots/home.png)

[📥 Download](https://github.com/yourusername/tsufutube-downloader/releases/latest) | [📖 User Guide](docs/USER_GUIDE.md) | [❓ FAQ](docs/FAQ.md) | [🐛 Report Bug](https://github.com/yourusername/tsufutube-downloader/issues)

</div>

---

## English

### ✨ Features

#### 🌐 **Multi-Platform Support**
Download from **1000+ websites** including:
- YouTube (Videos, Playlists, Music)
- Facebook (Watch, Posts, Stories)
- Instagram (Reels, Posts, Stories)
- TikTok (Videos, Music)
- Twitter/X (Videos, GIFs)
- Bilibili (Videos, Bangumi with 403 fix)
- Vimeo, Dailymotion, and many more!

#### 🎬 **Quality Options**
- **Video**: 4K, 2K, 1080p, 720p, 480p, 360p, 144p
- **Audio**: OPUS, AAC, MP3, FLAC
- Smart quality selection based on availability

#### ⚡ **Advanced Features**
- ✂️ **Video Trimming**: Download only the part you need
- 📝 **Subtitle Download**: Multi-language subtitle support
- 📋 **Download Queue**: Batch download multiple videos
- 🎵 **Audio-Only Mode**: Extract audio from videos
- 🔄 **Resume Support**: Continue interrupted downloads
- 📦 **Playlist Download**: Download entire playlists/albums
- 🍪 **Smart Cookie Helper**: Auto-detect when cookies needed
- 🚫 **SponsorBlock**: Skip ads/intros automatically (YouTube)
- 🌍 **Multi-Language UI**: 10 languages supported

#### 🔧 **Built-in Media Tools**
- **Remux**: Convert video formats (MP4, MKV, AVI, WEBM...)
- **Extract Audio**: MP3, AAC, FLAC, WAV
- **Fast Cut**: Trim videos using stream copy (instant!)
- **Compress**: Reduce file size with CRF
- **Subtitle Embed/Burn**: Add subtitles to videos
- **Cover Art**: Embed thumbnails
- **Video ↔ GIF**: Convert between formats
- **Normalize Audio**, **Remove Audio**, **Fix Rotation**

### 📸 Screenshots

<details>
<summary>Click to view screenshots</summary>

| Home Tab | History Tab |
|----------|-------------|
| ![Home](assets/screenshots/home.png) | ![History](assets/screenshots/history.png) |

| Tools Tab | Settings Tab |
|-----------|--------------|
| ![Tools](assets/screenshots/tools.png) | ![Settings](assets/screenshots/settings.png) |

</details>

### 🚀 Quick Start

1. **Download** the latest release from [Releases](https://github.com/yourusername/tsufutube-downloader/releases)
2. **Run** `Tsufutube-Downloader.exe` (No installation needed!)
3. **Paste** any video link
4. **Click** "Check" to fetch info
5. **Select** quality and options
6. **Download**!

### 📋 Requirements

- **OS**: Windows 10/11 (64-bit)
- **RAM**: 2GB minimum
- **Disk**: 500MB free space
- **Internet**: Active connection
- **Optional**: FFmpeg (included in executable)
- **Linux / Docker Users**: See [README_LINUX.md](README_LINUX.md) for instructions.

### 💻 For Developers

#### Installation from Source

```bash
# Clone repository
git clone https://github.com/yourusername/tsufutube-downloader.git
cd tsufutube-downloader

# Create virtual environment
python -m venv venv
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run
python "tsufutube_downloader.py"
```

#### Build Executable

```bash
pyinstaller --onefile --windowed --icon=icon.ico \
  --name="Tsufutube-Downloader" \
  --add-data="assets;assets" \
  "tsufutube_downloader.py"
```

### 📖 Documentation

- [User Guide](docs/USER_GUIDE.md)
- [FAQ](docs/FAQ.md)
- [Contributing](docs/CONTRIBUTING.md)
- [Changelog](CHANGELOG.md)

### 🤝 Contributing

Contributions are welcome! Please read [CONTRIBUTING.md](docs/CONTRIBUTING.md) first.

1. Fork the project
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

### 🐛 Bug Reports & Feature Requests

- [Report a bug](https://github.com/yourusername/tsufutube-downloader/issues/new?template=bug_report.md)
- [Request a feature](https://github.com/yourusername/tsufutube-downloader/issues/new?template=feature_request.md)

### 📜 License

This project is licensed under the MIT License - see [LICENSE](LICENSE) file for details.

### 🙏 Acknowledgments

- [yt-dlp](https://github.com/yt-dlp/yt-dlp) - Core download engine
- [FFmpeg](https://ffmpeg.org/) - Media processing
- [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter) - Modern UI framework

### ☕ Support

If you find this project helpful, consider:
- ⭐ Starring the repository
- 🐛 Reporting bugs
- 💬 Sharing with friends
- ☕ [Buy me a coffee](your-donation-link)

---

## Tiếng Việt

### ✨ Tính năng

#### 🌐 **Hỗ trợ đa nền tảng**
Tải video từ **hơn 1000 website** bao gồm:
- YouTube (Video, Playlist, Nhạc)
- Facebook (Watch, Bài viết, Story)
- Instagram (Reels, Bài viết, Story)
- TikTok (Video, Nhạc)
- Twitter/X (Video, GIF)
- Bilibili (Video, Bangumi với fix lỗi 403)
- Vimeo, Dailymotion và nhiều nền tảng khác!

#### 🎬 **Tùy chọn chất lượng**
- **Video**: 4K, 2K, 1080p, 720p, 480p, 360p, 144p
- **Audio**: OPUS, AAC, MP3, FLAC
- Tự động chọn chất lượng tốt nhất có sẵn

#### ⚡ **Tính năng nâng cao**
- ✂️ **Cắt video**: Chỉ tải phần cần thiết
- 📝 **Tải phụ đề**: Hỗ trợ đa ngôn ngữ
- 📋 **Hàng đợi**: Tải hàng loạt nhiều video
- 🎵 **Chỉ tải nhạc**: Trích xuất audio từ video
- 🔄 **Tiếp tục tải**: Tự động resume khi bị gián đoạn
- 📦 **Tải Playlist**: Tải cả playlist/album
- 🍪 **Hỗ trợ Cookie thông minh**: Tự phát hiện khi cần cookies
- 🚫 **SponsorBlock**: Tự động bỏ qua quảng cáo (YouTube)
- 🌍 **Đa ngôn ngữ**: 10 ngôn ngữ

#### 🔧 **Công cụ xử lý media tích hợp**
- **Chuyển đổi định dạng**: MP4, MKV, AVI, WEBM...
- **Trích xuất âm thanh**: MP3, AAC, FLAC, WAV
- **Cắt nhanh**: Cắt video bằng stream copy (tức thì!)
- **Nén video**: Giảm dung lượng với CRF
- **Thêm phụ đề**: Mềm hoặc cứng
- **Thêm ảnh bìa**: Embed thumbnail
- **Video ↔ GIF**: Chuyển đổi qua lại
- **Chuẩn hóa âm thanh**, **Xóa âm thanh**, **Sửa xoay video**

### 🚀 Bắt đầu nhanh

1. **Tải xuống** phiên bản mới nhất từ [Releases](https://github.com/yourusername/tsufutube-downloader/releases)
2. **Chạy** file `Tsufutube-Downloader.exe` (Không cần cài đặt!)
3. **Dán** link video bất kỳ
4. **Nhấn** "Kiểm tra" để lấy thông tin
5. **Chọn** chất lượng và tùy chọn
6. **Tải về**!

### 📋 Yêu cầu hệ thống

- **HĐH**: Windows 10/11 (64-bit)
- **RAM**: Tối thiểu 2GB
- **Ổ đĩa**: 500MB trống
- **Internet**: Kết nối ổn định
- **Tùy chọn**: FFmpeg (đã tích hợp)

### 🤝 Đóng góp

Mọi đóng góp đều được hoan nghênh! Vui lòng đọc [CONTRIBUTING.md](docs/CONTRIBUTING.md) trước.

### 📜 Giấy phép

Dự án này được cấp phép theo giấy phép MIT - xem file [LICENSE](LICENSE) để biết chi tiết.

### ☕ Ủng hộ

Nếu bạn thấy dự án hữu ích:
- ⭐ Star repository
- 🐛 Báo lỗi
- 💬 Chia sẻ với bạn bè
- ☕ [Mua tôi cà phê](your-donation-link)

---

<div align="center">

Made with ❤️ by [Tsufu]

[⬆ Back to top](#-tsufutube-downloader)

</div>
