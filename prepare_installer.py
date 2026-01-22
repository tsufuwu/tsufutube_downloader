from PIL import Image
import os

def convert():
    files = ["step 1.png", "step 2.png"]
    src_dir = os.path.join("assets", "install_manual")
    dest_dir = os.path.join("installer", "assets")

    if not os.path.exists(dest_dir):
        os.makedirs(dest_dir)

    for f in files:
        src = os.path.join(src_dir, f)
        if os.path.exists(src):
            try:
                img = Image.open(src)
                # Ensure RGB for BMP
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                dest_name = f.replace(".png", ".bmp")
                dest = os.path.join(dest_dir, dest_name)
                img.save(dest)
                print(f"Converted {f} -> {dest}")
            except Exception as e:
                print(f"Failed to convert {f}: {e}")
        else:
            print(f"Missing source: {src}")

if __name__ == "__main__":
    convert()
