# Changelog

All notable changes to Tsufutube Downloader will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.0.0] - 2026-01-16

### 🎉 Initial Release

#### ✨ Added
- Multi-platform video download support (YouTube, Facebook, TikTok, Instagram, Bilibili, etc.)
- Quality selection (4K, 2K, 1080p, 720p, 480p, 360p, 144p)
- Audio extraction (OPUS, AAC, MP3, FLAC)
- Video trimming/cutting feature
- Subtitle download (multi-language)
- Download queue system
- Playlist/Album batch download
- Browser cookies support (Chrome, Edge, Firefox, Opera, Brave)
- Smart Cookie Helper with auto-detection
- SponsorBlock integration (YouTube ad-skipping)
- Geo-bypass and proxy support
- Archive mode (avoid duplicate downloads)
- Auto-paste from clipboard
- Download history tracking
- **Built-in Media Tools:**
  - Format converter (Remux)
  - Audio extractor
  - Fast Cut (stream copy)
  - Video compression
  - Subtitle embed/burn
  - Cover art embed
  - Normalize audio
  - Remove audio
  - Fix rotation
  - Video ↔ GIF converter
  - Subtitle format converter
- **Multi-language UI:**
  - Vietnamese (Tiếng Việt)
  - English
  - Chinese Simplified (简体中文)
  - Spanish (Español)
  - Russian (Русский)
  - Japanese (日本語)
  - Korean (한국어)
  - French (Français)
  - Portuguese (Português)
  - German (Deutsch)
- Modern CustomTkinter UI with dark/light themes
- Cookie status indicator on Home tab
- 3-tab User Guide (Guide, Features, FAQ)
- Custom delete dialog for history items
- Settings persistence with auto-save
- FFmpeg integration for media processing
- Thumbnail preview
- Progress tracking with speed/ETA

#### 🛠️ Technical Features
- Async info fetching (non-blocking UI)
- Thread management for downloads
- Error handling with smart retry
- yt-dlp integration with custom extractors
- Bilibili 403 error fix
- Motchill JW Player extractor
- Download resume support
- Configurable output paths
- Format priority system
- Metadata embedding

#### 🎨 UI/UX
- Clean, modern interface
- Responsive design
- Real-time progress updates
- Cookie Helper popup for restricted content
- Jump-to-Settings functionality
- Bilingual restart confirmation
- Smooth tab switching
- Status indicators
- Context menu in history
- Batch operations (open files/folders, delete)

#### 🐛 Fixed
- Restart loop when saving settings
- Cookie indicator not updating
- Duplicate code cleanup
- Missing helper functions
- UI freeze during playlist downloads
- Info fetch race conditions

---

## [Future Plans]

### v1.1.0 (Planned)
- [ ] Linux support
- [ ] macOS support
- [ ] Auto-update mechanism
- [ ] Custom download templates
- [ ] Advanced filtering options
- [ ] Batch URL import from file
- [ ] Download scheduler
- [ ] Speed limiter

### v1.2.0 (Planned)
- [ ] Plugin/Extension system
- [ ] Custom extractor support
- [ ] Advanced queue management
- [ ] Download categories/folders
- [ ] Cloud storage integration
- [ ] Mobile companion app
- [ ] Web interface (optional)

### v2.0.0 (Long-term)
- [ ] Complete UI redesign
- [ ] AI-powered quality selection
- [ ] Built-in video player
- [ ] Social features (share, comment)
- [ ] Statistics and analytics
- [ ] Premium features

---

## Version History

- **v1.0.0** - 2026-01-16 - Initial Release

---

**Note:** This changelog follows [Semantic Versioning](https://semver.org/):
- **MAJOR** version for incompatible API changes
- **MINOR** version for new functionality (backwards compatible)
- **PATCH** version for bug fixes (backwards compatible)
