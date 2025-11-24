#!/usr/bin/env python3
"""
Create Icon File with Robot Emoji
Generates app-icon.ico with a robot emoji
"""

import sys
from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    print("Pillow library not found. Installing...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "Pillow"])
    from PIL import Image, ImageDraw, ImageFont

def create_icon_with_emoji(output_path="app-icon.ico"):
    """Create an icon file with a robot emoji."""

    # Define icon sizes
    sizes = [256, 128, 64, 48, 32, 16]
    images = []

    # Background gradient colors (Google Blue shades)
    bg_color_top = (66, 133, 244)     # Google Blue
    bg_color_bottom = (33, 150, 243)  # Material Blue

    print("Creating icon with robot emoji 🤖")

    for size in sizes:
        # Create new image with gradient background
        img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        # Draw gradient background
        for y in range(size):
            ratio = y / size
            r = int(bg_color_top[0] + (bg_color_bottom[0] - bg_color_top[0]) * ratio)
            g = int(bg_color_top[1] + (bg_color_bottom[1] - bg_color_top[1]) * ratio)
            b = int(bg_color_top[2] + (bg_color_bottom[2] - bg_color_top[2]) * ratio)
            draw.line([(0, y), (size, y)], fill=(r, g, b, 255))

        # Try to draw robot emoji
        try:
            # Calculate font size (roughly 60% of image size)
            font_size = int(size * 0.6)

            # Try different fonts that might support emoji
            font_names = [
                "seguiemj.ttf",  # Windows Segoe UI Emoji
                "Apple Color Emoji.ttc",  # macOS
                "NotoColorEmoji.ttf",  # Linux
                "Symbola.ttf",  # Generic
            ]

            font = None
            for font_name in font_names:
                try:
                    if sys.platform == "win32":
                        # Windows font path
                        font = ImageFont.truetype(f"C:\\Windows\\Fonts\\{font_name}", font_size)
                    else:
                        # Try system font paths
                        font = ImageFont.truetype(font_name, font_size)
                    break
                except:
                    continue

            if font is None:
                # Fallback to default font
                font = ImageFont.load_default()

            # Draw the robot emoji
            emoji = "🤖"

            # Get text bounding box
            bbox = draw.textbbox((0, 0), emoji, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]

            # Center the text
            x = (size - text_width) // 2
            y = (size - text_height) // 2

            # Draw emoji with white color
            draw.text((x, y), emoji, font=font, fill=(255, 255, 255, 255))

        except Exception as e:
            print(f"  Warning: Could not draw emoji for size {size}x{size}: {e}")
            # Draw a simple robot face as fallback
            draw_simple_robot(draw, size)

        images.append(img)
        print(f"  ✓ Generated {size}x{size} icon")

    # Save as ICO
    output_path = Path(output_path)
    images[0].save(
        output_path,
        format='ICO',
        sizes=[(img.width, img.height) for img in images],
        append_images=images[1:]
    )

    print(f"\n✓ Icon created successfully: {output_path}")
    print(f"  File size: {output_path.stat().st_size / 1024:.2f} KB")
    print("\nNext steps:")
    print("1. Uncomment icon configuration in Product.wxs (lines 35-36)")
    print("2. Uncomment Icon attributes in shortcuts (lines 121, 162)")
    print("3. Rebuild the installer")

def draw_simple_robot(draw, size):
    """Draw a simple robot face as a fallback."""
    # Draw robot head (rounded rectangle)
    margin = size // 8
    head_rect = [margin, margin, size - margin, size - margin]
    draw.rounded_rectangle(head_rect, radius=size//10, fill=(255, 255, 255, 255))

    # Draw eyes
    eye_size = size // 8
    eye_y = size // 3
    left_eye = [size // 3 - eye_size // 2, eye_y, size // 3 + eye_size // 2, eye_y + eye_size]
    right_eye = [2 * size // 3 - eye_size // 2, eye_y, 2 * size // 3 + eye_size // 2, eye_y + eye_size]
    draw.ellipse(left_eye, fill=(66, 133, 244, 255))
    draw.ellipse(right_eye, fill=(66, 133, 244, 255))

    # Draw mouth (smile)
    mouth_y = 2 * size // 3
    mouth_width = size // 3
    mouth_rect = [
        size // 2 - mouth_width // 2,
        mouth_y,
        size // 2 + mouth_width // 2,
        mouth_y + mouth_width // 2
    ]
    draw.arc(mouth_rect, 0, 180, fill=(66, 133, 244, 255), width=max(1, size // 20))

    # Draw antenna
    antenna_x = size // 2
    antenna_top = margin // 2
    draw.line([antenna_x, margin, antenna_x, antenna_top], fill=(255, 255, 255, 255), width=max(1, size // 20))
    draw.ellipse([antenna_x - size // 20, antenna_top - size // 20,
                  antenna_x + size // 20, antenna_top + size // 20],
                 fill=(255, 255, 255, 255))

if __name__ == "__main__":
    script_dir = Path(__file__).parent
    output_file = script_dir / "app-icon.ico"

    try:
        create_icon_with_emoji(str(output_file))
    except Exception as e:
        print(f"\n❌ Error: {e}", file=sys.stderr)
        print("\nAlternative: Use an online tool to create the icon:")
        print("1. Go to https://www.icoconverter.com/")
        print("2. Create a PNG with a robot emoji (any graphics editor)")
        print("3. Upload and convert to .ico")
        print("4. Save as installer/windows/app-icon.ico")
        sys.exit(1)
