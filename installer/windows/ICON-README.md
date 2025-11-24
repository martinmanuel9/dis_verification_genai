# Adding a Windows Icon to the Installer

## Quick Steps

1. **Create or obtain an icon file** in `.ico` format
   - Recommended sizes: 16x16, 32x32, 48x48, 64x64, 128x128, 256x256
   - You can use online tools like [ICOConverter](https://icoconverter.com/) or [ConvertICO](https://convertio.co/png-ico/)

2. **Save the icon** as `installer/windows/app-icon.ico`

3. **Uncomment the icon configuration** in `installer/windows/Product.wxs`:
   ```xml
   <!-- Currently commented at lines 35-36 -->
   <Property Id="ARPPRODUCTICON" Value="AppIcon" />
   <Icon Id="AppIcon" SourceFile="app-icon.ico" />
   ```

4. **Uncomment shortcut icon references** in `Product.wxs`:
   ```xml
   <!-- In ApplicationStartMenuShortcut (line 121) -->
   <!-- In ApplicationDesktopShortcut (line 162) -->
   Icon="AppIcon" IconIndex="0"
   ```

5. **Update the build script** to copy the icon file:
   Add to `installer/windows/build-msi.ps1` around line 96:
   ```powershell
   # Copy icon file
   $iconFile = "$PSScriptRoot\app-icon.ico"
   if (Test-Path $iconFile) {
       Copy-Item $iconFile $buildDir
       Write-Info "Icon file copied to build directory"
   }
   ```

6. **Update GitHub Actions workflow** to copy the icon:
   Add to `.github/workflows/build-installers.yml` around line 194:
   ```yaml
   # Copy icon file if it exists
   if (Test-Path installer/windows/app-icon.ico) {
       Copy-Item installer/windows/app-icon.ico installer/windows/ -ErrorAction SilentlyContinue
   }
   ```

## Creating an Icon from Scratch

If you want to create a custom icon:

### Option 1: Use an Online Tool
1. Design your logo/icon in any graphics program (PNG recommended)
2. Upload to [ICOConverter.com](https://icoconverter.com/)
3. Download the `.ico` file

### Option 2: Use GIMP (Free)
1. Design your icon (256x256 or 512x512 recommended)
2. File → Export As
3. Save as `.ico` format
4. Select multiple sizes in the export dialog

### Option 3: Use ImageMagick (Command Line)
```bash
# Install ImageMagick
sudo apt-get install imagemagick  # Linux
brew install imagemagick          # macOS
choco install imagemagick         # Windows

# Convert PNG to ICO with multiple sizes
convert icon.png -define icon:auto-resize=256,128,64,48,32,16 app-icon.ico
```

## Design Recommendations

- **Simple and recognizable**: Icons look better when they're simple
- **Test at small sizes**: Make sure it's visible at 16x16
- **Use transparency**: ICO files support transparency
- **Professional look**: Consider hiring a designer on Fiverr ($5-20)

## Example Icon Ideas for DIS Verification GenAI

- Brain with circuit patterns (AI theme)
- Document with checkmark (verification theme)
- Shield with AI chip (security + AI)
- Magnifying glass over code (analysis theme)
- Robot holding a clipboard (automated testing)

## Current Status

✅ WiX configuration prepared (commented out, ready to enable)
✅ Shortcut icon support prepared
⏳ Icon file not yet created (`app-icon.ico`)

Once you add the `app-icon.ico` file, simply uncomment the relevant lines in `Product.wxs` and rebuild!
