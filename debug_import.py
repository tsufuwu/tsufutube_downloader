import sys
import traceback
import os

# Add current directory to path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

print(f"Running from: {current_dir}")

try:
    print("Attempting to import ui.app...")
    from ui.app import YoutubeDownloaderApp
    print("Import successful.")
    
    print("Attempting to initialize YoutubeDownloaderApp...")
    # Mocking arguments if needed, or just running init
    app = YoutubeDownloaderApp(start_silently=True)
    print("Init successful.")
except Exception:
    print("Caught exception:")
    traceback.print_exc()
