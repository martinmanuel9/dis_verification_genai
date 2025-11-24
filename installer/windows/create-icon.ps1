###############################################################################
# Create Icon File with Robot Emoji
# Generates app-icon.ico with a robot emoji
###############################################################################

param(
    [string]$OutputPath = "$PSScriptRoot\app-icon.ico"
)

$ErrorActionPreference = "Stop"

Write-Host "Creating icon with robot emoji..."

# Check if ImageMagick is available
$hasImageMagick = Get-Command magick -ErrorAction SilentlyContinue

if (-not $hasImageMagick) {
    Write-Host ""
    Write-Host "ImageMagick not found. Installing via winget..."
    Write-Host "(This will take a moment)"

    try {
        winget install --id ImageMagick.ImageMagick -e --silent
        Write-Host "ImageMagick installed! Please close and reopen PowerShell, then run this script again."
        exit 0
    } catch {
        Write-Host ""
        Write-Host "Could not install ImageMagick automatically."
        Write-Host ""
        Write-Host "Please install ImageMagick manually:"
        Write-Host "1. Visit: https://imagemagick.org/script/download.php"
        Write-Host "2. Download and install ImageMagick for Windows"
        Write-Host "3. Run this script again"
        Write-Host ""
        Write-Host "Alternative: Use an online tool to create an .ico file:"
        Write-Host "- https://www.icoconverter.com/"
        Write-Host "- https://convertico.com/"
        Write-Host ""
        Write-Host "Just upload a PNG with a robot emoji and download the .ico file!"
        exit 1
    }
}

# Create a temporary PNG with robot emoji
$tempPng = [System.IO.Path]::GetTempFileName() + ".png"

# Use PowerShell to create an image with robot emoji
Add-Type -AssemblyName System.Drawing

# Create bitmap with robot emoji
$sizes = @(256, 128, 64, 48, 32, 16)
$tempFiles = @()

foreach ($size in $sizes) {
    $bitmap = New-Object System.Drawing.Bitmap($size, $size)
    $graphics = [System.Drawing.Graphics]::FromImage($bitmap)

    # Fill background with a nice gradient blue
    $brush = New-Object System.Drawing.Drawing2D.LinearGradientBrush(
        (New-Object System.Drawing.Point(0, 0)),
        (New-Object System.Drawing.Point($size, $size)),
        [System.Drawing.Color]::FromArgb(66, 133, 244),  # Google Blue
        [System.Drawing.Color]::FromArgb(33, 150, 243)   # Material Blue
    )
    $graphics.FillRectangle($brush, 0, 0, $size, $size)

    # Draw robot emoji (using a font that supports emojis)
    $font = New-Object System.Drawing.Font("Segoe UI Emoji", [int]($size * 0.6), [System.Drawing.FontStyle]::Regular)
    $stringFormat = New-Object System.Drawing.StringFormat
    $stringFormat.Alignment = [System.Drawing.StringAlignment]::Center
    $stringFormat.LineAlignment = [System.Drawing.StringAlignment]::Center

    $robotEmoji = "🤖"
    $graphics.DrawString($robotEmoji, $font, [System.Drawing.Brushes]::White, ($size / 2), ($size / 2), $stringFormat)

    # Save temp file
    $tempFile = [System.IO.Path]::GetTempFileName() + "_${size}.png"
    $bitmap.Save($tempFile, [System.Drawing.Imaging.ImageFormat]::Png)
    $tempFiles += $tempFile

    $graphics.Dispose()
    $bitmap.Dispose()
}

Write-Host "Generated PNG files at different sizes"

# Convert PNGs to ICO using ImageMagick
Write-Host "Converting to .ico format..."

try {
    $args = @($tempFiles) + @($OutputPath)
    & magick @args

    if (Test-Path $OutputPath) {
        Write-Host ""
        Write-Host "✓ Icon created successfully: $OutputPath" -ForegroundColor Green
        Write-Host ""
        Write-Host "Next steps:"
        Write-Host "1. Uncomment icon configuration in Product.wxs (lines 35-36)"
        Write-Host "2. Uncomment Icon attributes in shortcuts (lines 121, 162)"
        Write-Host "3. Rebuild the installer"
        Write-Host ""

        # Show file info
        $fileInfo = Get-Item $OutputPath
        Write-Host "File size: $([math]::Round($fileInfo.Length / 1KB, 2)) KB"
    } else {
        throw "Icon file was not created"
    }
} catch {
    Write-Host ""
    Write-Host "Error creating icon: $_" -ForegroundColor Red
    Write-Host ""
    Write-Host "Alternative method:"
    Write-Host "1. Create a PNG with robot emoji using any image editor"
    Write-Host "2. Upload to https://icoconverter.com/"
    Write-Host "3. Download the .ico file"
    Write-Host "4. Save it as installer/windows/app-icon.ico"
} finally {
    # Cleanup temp files
    foreach ($file in $tempFiles) {
        if (Test-Path $file) {
            Remove-Item $file -Force
        }
    }
}
