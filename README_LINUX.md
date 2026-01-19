# Running Tsufutube Downloader on Linux

## Prerequisites
- **Python**: 3.10 or higher
- **FFmpeg**: Must be installed (`sudo apt install ffmpeg`)
- **Tkinter**: Python GUI support (`sudo apt install python3-tk`)

## Installation
1. Clone the repository:
   ```bash
   git clone https://github.com/tsufuwu/tsufutube_downloader.git
   cd tsufutube_downloader
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run the application:
   ```bash
   python "Tsufutube downloader.py"
   ```

## Running with Docker
### 1. Build the Image
```bash
docker build -t tsufutube .
```

### 2. Run the Container
Running GUI apps in Docker requires X11 forwarding.

#### On Linux (Native X11):
```bash
xhost +local:docker
docker run -it --rm \
    -e DISPLAY=$DISPLAY \
    -v /tmp/.X11-unix:/tmp/.X11-unix \
    -v $(pwd)/downloads:/app/downloads \
    tsufutube
```

#### On Windows (WSL2):
Requires an X Server like [VcXsrv](https://sourceforge.net/projects/vcxsrv/).
1. Start VcXsrv with "Disable access control" checked.
2. Run:
   ```bash
   docker run -it --rm \
       -e DISPLAY=host.docker.internal:0 \
       -v $(pwd)/downloads:/app/downloads \
       tsufutube
   ```
