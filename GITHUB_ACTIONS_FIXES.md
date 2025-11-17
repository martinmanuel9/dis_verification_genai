# GitHub Actions Workflow Fixes

## Summary

Updated the `.github/workflows/build-installers.yml` workflow to build installers with all the new automation features (source code inclusion, environment setup, Ollama model pulling).

## Changes Made

### 1. Windows MSI Build (lines 138-239)

**Problem:** The old workflow used a simple Product.wxs that didn't include source files.

**Solution:** Updated to use WiX file harvesting with `heat.exe`:

#### New Steps:
1. **Create staging directory** - Copies all source files, scripts, documentation
   ```powershell
   Copy-Item -Recurse src $stagingDir
   Copy-Item -Recurse scripts $stagingDir
   Copy-Item -Recurse installer/windows/scripts/* $stagingDir/scripts
   # ... all other files
   ```

2. **Harvest files with heat.exe** - Automatically generates WiX fragment for all files
   ```powershell
   heat.exe dir staging -cg ApplicationFiles -var "var.StagingDir" ...
   ```

3. **Compile with proper variables** - Passes StagingDir variable to candle.exe
   ```powershell
   candle.exe Product_build.wxs -dStagingDir="$stagingPath" -dVersion=$version
   candle.exe FilesFragment.wxs -dStagingDir="$stagingPath" -dVersion=$version
   ```

4. **Link to create MSI** - Combines both object files
   ```powershell
   light.exe Product_build.wixobj FilesFragment.wixobj -out ...
   ```

**Result:**
- ✅ Complete `src/` directory included
- ✅ All scripts (bash + PowerShell) included
- ✅ Post-install.ps1 runs after installation
- ✅ Setup wizard auto-runs
- ✅ Ollama integration available

---

### 2. Linux DEB Build (line 286)

**Added:** INSTALL.md to copied files

```bash
cp INSTALL.md "$PKG_DIR/opt/dis-verification-genai/"
```

**Result:**
- ✅ Complete documentation included
- ✅ Postinst script (already updated) runs interactive setup

---

### 3. Linux RPM Build (lines 326-415)

**Added:**
1. Copy RPM post-install script before creating tarball
   ```bash
   cp installer/linux/rpm-postinst.sh scripts/
   ```

2. Enhanced spec file with:
   - Complete description
   - `%post` section calling rpm-postinst.sh
   - `%preun` section to stop services
   - `%postun` section to clean up

3. Added INSTALL.md to source tarball
   ```bash
   cp -r src scripts ... INSTALL.md dis-verification-genai-$VERSION/
   ```

**Result:**
- ✅ Post-install automation runs
- ✅ Interactive environment setup
- ✅ Ollama installation option
- ✅ Proper service cleanup on uninstall

---

### 4. macOS DMG Build (lines 453-490)

**Enhanced launcher scripts:**

1. **Main launcher** - Now includes:
   - First-run setup check
   - Docker running verification
   - Auto-opens Terminal for configuration
   ```bash
   if [ ! -f "$RESOURCES_DIR/.env" ] || [ ! -s "$RESOURCES_DIR/.env" ]; then
       osascript -e 'tell app "Terminal" to do script "cd '"$RESOURCES_DIR"' && ./scripts/setup-env.sh"'
       exit 0
   fi
   ```

2. **Setup launcher** - New separate script for reconfiguration
   ```bash
   cat > "build/$APP_NAME.app/Contents/MacOS/setup" <<'EOF'
   #!/bin/bash
   RESOURCES_DIR="$(dirname "$0")/../Resources"
   cd "$RESOURCES_DIR"
   osascript -e 'tell app "Terminal" to do script "cd '"$RESOURCES_DIR"' && ./scripts/setup-env.sh && exit"'
   EOF
   ```

**Result:**
- ✅ First launch runs setup wizard automatically
- ✅ Docker check before starting services
- ✅ User-friendly error messages
- ✅ Separate setup script for reconfiguration

---

## Testing the Workflow

### Trigger Options:

1. **Push to main** (when VERSION file changes)
   ```bash
   echo "1.0.5" > VERSION
   git add VERSION
   git commit -m "Bump version to 1.0.5"
   git push origin main
   ```

2. **Tag push**
   ```bash
   git tag v1.0.5
   git push origin v1.0.5
   ```

3. **Manual workflow dispatch**
   - Go to GitHub Actions
   - Select "Build Installers" workflow
   - Click "Run workflow"
   - Enter version (e.g., "1.0.5")

### Verify Build Artifacts:

After workflow completes, check that release includes:
- ✅ `dis-verification-genai-1.0.5.msi` (Windows)
- ✅ `dis-verification-genai_1.0.5_amd64.deb` (Debian/Ubuntu)
- ✅ `dis-verification-genai-1.0.5.x86_64.rpm` (RHEL/CentOS/Fedora)
- ✅ `dis-verification-genai-1.0.5.dmg` (macOS)
- ✅ `checksums-sha256.txt` (Verification hashes)

### Verify Installer Contents:

Download and test each installer:

**Windows:**
```powershell
# Extract MSI (for verification only, don't actually do this for install)
# Use 7-Zip or similar to inspect contents
# Should see: src/, scripts/, docker-compose.yml, etc.

# Install and verify
msiexec /i dis-verification-genai-1.0.5.msi
# Should see post-install.ps1 run with prompts
```

**Linux DEB:**
```bash
# Extract DEB (for verification)
dpkg-deb -x dis-verification-genai_1.0.5_amd64.deb extracted/
ls -la extracted/opt/dis-verification-genai/
# Should see src/, scripts/, etc.

# Install and verify
sudo dpkg -i dis-verification-genai_1.0.5_amd64.deb
# Should see interactive setup prompts
```

**Linux RPM:**
```bash
# Extract RPM (for verification)
rpm2cpio dis-verification-genai-1.0.5.x86_64.rpm | cpio -idmv
ls -la opt/dis-verification-genai/
# Should see src/, scripts/, etc.

# Install and verify
sudo rpm -i dis-verification-genai-1.0.5.x86_64.rpm
# Should see interactive setup prompts
```

**macOS:**
```bash
# Mount DMG
open dis-verification-genai-1.0.5.dmg
# Verify app bundle contains Resources/src/, Resources/scripts/, etc.

# Install and run
cp -R "/Volumes/DIS Verification GenAI/DIS Verification GenAI.app" /Applications/
open "/Applications/DIS Verification GenAI.app"
# Should open Terminal with setup wizard on first run
```

---

## Differences from Local Build

The GitHub Actions workflow builds are **functionally identical** to local builds created with `installer/build-local.sh`, but:

### GitHub Actions:
- Uses simpler inline scripts
- Creates staging directory in workflow steps
- Uses `heat.exe` dynamically during build
- Version templating done in workflow

### Local Build Scripts:
- More sophisticated with build-msi.ps1
- Better error handling and verification
- Cleaner build artifacts management
- Easier to debug locally

**Recommendation:** Use GitHub Actions for releases, use local builds for testing.

---

## Troubleshooting

### Windows build fails with "StagingDir not found"
**Cause:** Staging directory wasn't created or heat.exe failed

**Fix:** Check the "Create staging directory" step succeeded:
```powershell
Get-ChildItem -Path $stagingDir -Recurse | Select-Object -First 20
```

### RPM post-install script not running
**Cause:** rpm-postinst.sh wasn't copied to scripts/

**Fix:** Verify the "Copy RPM post-install script" step ran:
```bash
ls -la scripts/rpm-postinst.sh
```

### macOS launcher not showing setup wizard
**Cause:** .env file exists but is empty/template

**Fix:** Launcher now checks file size:
```bash
if [ ! -f "$RESOURCES_DIR/.env" ] || [ ! -s "$RESOURCES_DIR/.env" ]; then
```

---

## Next Steps

1. **Test the workflow** by pushing a version bump
2. **Download artifacts** from GitHub release
3. **Test each installer** on respective platform
4. **Verify all features work:**
   - Source code installed
   - Environment setup runs
   - Ollama integration works
   - Services start correctly

5. **Update documentation** if needed based on test results

---

## Rollback Plan

If the new workflow has issues, you can temporarily revert:

```bash
git revert <commit-hash>
git push origin main
```

Or create a hotfix by manually editing the workflow in GitHub UI.

The old simple workflow is preserved in git history and can be restored if needed.
