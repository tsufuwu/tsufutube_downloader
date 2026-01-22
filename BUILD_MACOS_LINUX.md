# Build Instructions for macOS and Linux

## Prerequisites

### All Platforms
```bash
pip install pyinstaller
pip install -r requirements.txt
```

### macOS Specific
```bash
# Install UPX (optional, for compression)
brew install upx

# Create .icns icon from PNG (required)
# Option 1: Use iconutil
mkdir icon.iconset
sips -z 16 16     assets/icon.png --out icon.iconset/icon_16x16.png
sips -z 32 32     assets/icon.png --out icon.iconset/icon_16x16@2x.png
sips -z 32 32     assets/icon.png --out icon.iconset/icon_32x32.png
sips -z 64 64     assets/icon.png --out icon.iconset/icon_32x32@2x.png
sips -z 128 128   assets/icon.png --out icon.iconset/icon_128x128.png
sips -z 256 256   assets/icon.png --out icon.iconset/icon_128x128@2x.png
sips -z 256 256   assets/icon.png --out icon.iconset/icon_256x256.png
sips -z 512 512   assets/icon.png --out icon.iconset/icon_256x256@2x.png
sips -z 512 512   assets/icon.png --out icon.iconset/icon_512x512.png
sips -z 1024 1024 assets/icon.png --out icon.iconset/icon_512x512@2x.png
iconutil -c icns icon.iconset -o assets/icon.icns
rm -rf icon.iconset

# Option 2: Use png2icns (simpler)
brew install libicns
png2icns assets/icon.icns assets/icon.png
```

### Linux Specific
```bash
# Install UPX for compression
sudo apt install upx

# Install Tk dependencies
sudo apt install python3-tk
```

---

## Building

### macOS (.app bundle)
```bash
# Build the .app
pyinstaller Tsufutube_Mac.spec

# Output: dist/Tsufutube Downloader.app

# Optional: Create DMG for distribution
hdiutil create -volname "Tsufutube Downloader" -srcfolder "dist/Tsufutube Downloader.app" -ov -format UDZO dist/Tsufutube-Downloader.dmg
```

### Linux (single binary)
```bash
# Build single executable
pyinstaller Tsufutube_Linux.spec

# Output: dist/tsufutube-downloader

# Make executable
chmod +x dist/tsufutube-downloader
```

---

## Installation

### macOS
```bash
# Move to Applications
mv "dist/Tsufutube Downloader.app" /Applications/

# Or for current user only
mv "dist/Tsufutube Downloader.app" ~/Applications/
```

### Linux
```bash
# System-wide installation
sudo mkdir -p /opt/tsufutube
sudo cp dist/tsufutube-downloader /opt/tsufutube/
sudo cp -r assets /opt/tsufutube/
sudo cp assets/tsufutube.desktop /usr/share/applications/

# User installation
mkdir -p ~/.local/bin
cp dist/tsufutube-downloader ~/.local/bin/
cp assets/tsufutube.desktop ~/.local/share/applications/

# Update desktop database
update-desktop-database ~/.local/share/applications/
```

---

## Code Signing (macOS only)

For distribution outside the App Store:
```bash
# Sign the app
codesign --deep --force --options=runtime --sign "Developer ID Application: Your Name (TEAM_ID)" --entitlements entitlements.plist "dist/Tsufutube Downloader.app"

# Notarize
xcrun notarytool submit dist/Tsufutube-Downloader.dmg --apple-id "your@email.com" --team-id "TEAM_ID" --password "@keychain:AC_PASSWORD" --wait

# Staple
xcrun stapler staple "dist/Tsufutube Downloader.app"
```

---

## Troubleshooting

### macOS: "App is damaged"
```bash
xattr -cr "/Applications/Tsufutube Downloader.app"
```

### Linux: Missing libraries
```bash
# Install common dependencies
sudo apt install libxcb-xinerama0 libxkbcommon-x11-0
```

### Playwright not working
```bash
# Install Playwright browsers
playwright install chromium
```
