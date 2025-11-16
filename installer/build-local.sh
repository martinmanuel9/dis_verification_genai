#!/bin/bash
###############################################################################
# Local Installer Build Script
# Builds installers for testing before pushing to GitHub
###############################################################################

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
print_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
print_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
print_error() { echo -e "${RED}[ERROR]${NC} $1"; }

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
VERSION=$(cat "$PROJECT_ROOT/VERSION")

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "         DIS Verification GenAI - Local Build Script"
echo "         Version: $VERSION"
echo "═══════════════════════════════════════════════════════════════"
echo ""

# Parse arguments
BUILD_TARGET="${1:-all}"

build_linux_deb() {
    print_info "Building Linux DEB package..."

    local PKG_DIR="dis-verification-genai_${VERSION}_amd64"
    local BUILD_DIR="$PROJECT_ROOT/build/deb"

    # Clean previous build
    rm -rf "$BUILD_DIR"
    mkdir -p "$BUILD_DIR"

    # Create package structure
    mkdir -p "$BUILD_DIR/$PKG_DIR/opt/dis-verification-genai"
    mkdir -p "$BUILD_DIR/$PKG_DIR/DEBIAN"

    # Copy application files
    print_info "Copying application files..."
    cp -r "$PROJECT_ROOT/src" "$BUILD_DIR/$PKG_DIR/opt/dis-verification-genai/"
    cp -r "$PROJECT_ROOT/scripts" "$BUILD_DIR/$PKG_DIR/opt/dis-verification-genai/"
    cp "$PROJECT_ROOT/docker-compose.yml" "$BUILD_DIR/$PKG_DIR/opt/dis-verification-genai/"
    cp "$PROJECT_ROOT/.env.template" "$BUILD_DIR/$PKG_DIR/opt/dis-verification-genai/.env"
    cp "$PROJECT_ROOT/VERSION" "$BUILD_DIR/$PKG_DIR/opt/dis-verification-genai/"
    cp "$PROJECT_ROOT/CHANGELOG.md" "$BUILD_DIR/$PKG_DIR/opt/dis-verification-genai/"
    cp "$PROJECT_ROOT/README.md" "$BUILD_DIR/$PKG_DIR/opt/dis-verification-genai/"
    cp "$PROJECT_ROOT/INSTALL.md" "$BUILD_DIR/$PKG_DIR/opt/dis-verification-genai/"

    # Copy DEBIAN control files
    cp "$SCRIPT_DIR/linux/DEBIAN/"* "$BUILD_DIR/$PKG_DIR/DEBIAN/"

    # Update version in control file
    sed -i "s/VERSION_PLACEHOLDER/$VERSION/g" "$BUILD_DIR/$PKG_DIR/DEBIAN/control"

    # Set permissions
    chmod 755 "$BUILD_DIR/$PKG_DIR/DEBIAN/postinst"
    chmod 755 "$BUILD_DIR/$PKG_DIR/DEBIAN/prerm"
    chmod 755 "$BUILD_DIR/$PKG_DIR/DEBIAN/postrm"
    chmod +x "$BUILD_DIR/$PKG_DIR/opt/dis-verification-genai/scripts/"*.sh

    # Build DEB package
    print_info "Building DEB package..."
    cd "$BUILD_DIR"
    dpkg-deb --build "$PKG_DIR"

    # Move to output directory
    mkdir -p "$PROJECT_ROOT/dist"
    mv "$BUILD_DIR/${PKG_DIR}.deb" "$PROJECT_ROOT/dist/"

    print_success "DEB package built: dist/${PKG_DIR}.deb"
}

build_linux_rpm() {
    print_info "Building Linux RPM package..."

    if ! command -v rpmbuild &> /dev/null; then
        print_error "rpmbuild not found. Install with: sudo apt-get install rpm"
        return 1
    fi

    local SPEC_FILE="$SCRIPT_DIR/linux/dis-verification-genai.spec"

    # Create RPM build directories
    mkdir -p ~/rpmbuild/{BUILD,RPMS,SOURCES,SPECS,SRPMS}

    # Create spec file
    cat > "$SPEC_FILE" <<EOF
Name:           dis-verification-genai
Version:        $VERSION
Release:        1%{?dist}
Summary:        AI-powered verification and test plan generation system
License:        Proprietary
URL:            https://github.com/martinmanuel9/dis_verification_genai
Requires:       docker >= 24.0.0

%description
DIS Verification GenAI provides comprehensive test plan generation.

%install
mkdir -p %{buildroot}/opt/dis-verification-genai
cp -r src %{buildroot}/opt/dis-verification-genai/
cp -r scripts %{buildroot}/opt/dis-verification-genai/
cp docker-compose.yml %{buildroot}/opt/dis-verification-genai/
cp .env.template %{buildroot}/opt/dis-verification-genai/.env
cp VERSION %{buildroot}/opt/dis-verification-genai/
cp CHANGELOG.md %{buildroot}/opt/dis-verification-genai/
cp README.md %{buildroot}/opt/dis-verification-genai/

%files
/opt/dis-verification-genai

%changelog
* $(date +'%a %b %d %Y') Developer <dev@example.com> - $VERSION-1
- Release $VERSION
EOF

    # Create source tarball
    print_info "Creating source tarball..."
    cd "$PROJECT_ROOT"
    tar czf ~/rpmbuild/SOURCES/dis-verification-genai-$VERSION.tar.gz \
        --exclude='.git' \
        --exclude='build' \
        --exclude='dist' \
        --exclude='*.pyc' \
        src scripts docker-compose.yml .env.template VERSION CHANGELOG.md README.md

    # Build RPM
    print_info "Building RPM package..."
    rpmbuild -ba "$SPEC_FILE"

    # Copy to dist
    mkdir -p "$PROJECT_ROOT/dist"
    cp ~/rpmbuild/RPMS/x86_64/dis-verification-genai-$VERSION-1.*.x86_64.rpm "$PROJECT_ROOT/dist/"

    print_success "RPM package built: dist/dis-verification-genai-$VERSION-1.*.x86_64.rpm"
}

build_macos_dmg() {
    print_info "Building macOS DMG..."

    if [[ "$(uname -s)" != "Darwin" ]]; then
        print_warning "macOS builds must be done on macOS"
        return 1
    fi

    local APP_NAME="DIS Verification GenAI"
    local DMG_NAME="dis-verification-genai-$VERSION.dmg"
    local BUILD_DIR="$PROJECT_ROOT/build/macos"

    # Clean previous build
    rm -rf "$BUILD_DIR"
    mkdir -p "$BUILD_DIR"

    # Create app bundle
    print_info "Creating app bundle..."
    mkdir -p "$BUILD_DIR/$APP_NAME.app/Contents/MacOS"
    mkdir -p "$BUILD_DIR/$APP_NAME.app/Contents/Resources"

    # Copy application files
    cp -r "$PROJECT_ROOT/src" "$BUILD_DIR/$APP_NAME.app/Contents/Resources/"
    cp -r "$PROJECT_ROOT/scripts" "$BUILD_DIR/$APP_NAME.app/Contents/Resources/"
    cp "$PROJECT_ROOT/docker-compose.yml" "$BUILD_DIR/$APP_NAME.app/Contents/Resources/"
    cp "$PROJECT_ROOT/.env.template" "$BUILD_DIR/$APP_NAME.app/Contents/Resources/.env"
    cp "$PROJECT_ROOT/VERSION" "$BUILD_DIR/$APP_NAME.app/Contents/Resources/"
    cp "$PROJECT_ROOT/CHANGELOG.md" "$BUILD_DIR/$APP_NAME.app/Contents/Resources/"
    cp "$PROJECT_ROOT/README.md" "$BUILD_DIR/$APP_NAME.app/Contents/Resources/"

    # Create Info.plist
    cat > "$BUILD_DIR/$APP_NAME.app/Contents/Info.plist" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleName</key>
    <string>DIS Verification GenAI</string>
    <key>CFBundleVersion</key>
    <string>$VERSION</string>
    <key>CFBundleShortVersionString</key>
    <string>$VERSION</string>
    <key>CFBundleExecutable</key>
    <string>launcher</string>
</dict>
</plist>
EOF

    # Create launcher script
    cat > "$BUILD_DIR/$APP_NAME.app/Contents/MacOS/launcher" <<'EOF'
#!/bin/bash
cd "$(dirname "$0")/../Resources"
docker compose up -d
open http://localhost:8501
EOF
    chmod +x "$BUILD_DIR/$APP_NAME.app/Contents/MacOS/launcher"

    # Create DMG
    print_info "Creating DMG..."
    mkdir -p "$PROJECT_ROOT/dist"
    hdiutil create -volname "$APP_NAME" -srcfolder "$BUILD_DIR" -ov -format UDZO "$PROJECT_ROOT/dist/$DMG_NAME"

    print_success "DMG created: dist/$DMG_NAME"
}

# Main build logic
case "$BUILD_TARGET" in
    deb)
        build_linux_deb
        ;;
    rpm)
        build_linux_rpm
        ;;
    dmg)
        build_macos_dmg
        ;;
    linux)
        build_linux_deb
        build_linux_rpm
        ;;
    all)
        print_info "Building all packages..."
        build_linux_deb || true
        build_linux_rpm || true
        if [[ "$(uname -s)" == "Darwin" ]]; then
            build_macos_dmg || true
        fi
        ;;
    *)
        print_error "Invalid build target: $BUILD_TARGET"
        echo ""
        echo "Usage: $0 [deb|rpm|dmg|linux|all]"
        echo ""
        echo "  deb    - Build Debian/Ubuntu package"
        echo "  rpm    - Build RHEL/CentOS/Fedora package"
        echo "  dmg    - Build macOS package (macOS only)"
        echo "  linux  - Build both DEB and RPM"
        echo "  all    - Build all available packages [default]"
        exit 1
        ;;
esac

echo ""
print_success "Build completed!"
echo ""
if [ -d "$PROJECT_ROOT/dist" ]; then
    print_info "Built packages:"
    ls -lh "$PROJECT_ROOT/dist/"
fi
echo ""
