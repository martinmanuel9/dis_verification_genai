#!/usr/bin/env python3
"""
Convert PNG to ICO for Windows installer
"""
import sys
from pathlib import Path

try:
    from PIL import Image
except ImportError:
    print("ERROR: PIL/Pillow not installed")
    print("Install with: pip install Pillow")
    sys.exit(1)

script_dir = Path(__file__).parent
png_file = script_dir / "app-icon.png"
ico_file = script_dir / "app-icon.ico"

if not png_file.exists():
    print(f"ERROR: {png_file} not found")
    sys.exit(1)

print(f"Converting {png_file} to {ico_file}...")

try:
    img = Image.open(png_file)

    # ICO files need specific sizes (16, 32, 48, 256)
    # Resize to 256x256 if needed
    if img.size != (256, 256):
        img = img.resize((256, 256), Image.Resampling.LANCZOS)

    # Save as ICO with multiple sizes
    img.save(ico_file, format='ICO', sizes=[(16, 16), (32, 32), (48, 48), (256, 256)])

    print(f"SUCCESS: Created {ico_file}")
    print(f"Icon sizes: 16x16, 32x32, 48x48, 256x256")

except Exception as e:
    print(f"ERROR: {e}")
    sys.exit(1)
