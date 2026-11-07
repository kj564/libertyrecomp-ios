#!/bin/bash
# One-command build script for iPhone 13 (run on Mac)
# Usage: ./build_iphone13.sh <TEAM_ID> [BUNDLE_ID]
set -e

TEAM_ID="${1:?usage: $0 <APPLE_TEAM_ID> [BUNDLE_ID]}"
BUNDLE_ID="${2:-com.libertyrecomp.iphone13}"
REPO_URL="https://github.com/vaduur/LibertyRecompAndroid.git"
BUILD_DIR="out/build/ios-release"

echo "=== 1. Verify Mac environment ==="
xcode-select -p
xcrun --sdk iphoneos --show-sdk-version || { echo "ERROR: iOS SDK not found. Install Xcode 15+"; exit 1; }
cmake --version | head -1
python3 --version

echo ""
echo "=== 2. Clone upstream (1.1 GB, ~5 min) ==="
if [ ! -d "LibertyRecompAndroid" ]; then
    git clone --depth=1 "$REPO_URL"
fi
cd LibertyRecompAndroid
python3 tools/setup_repo.py

echo ""
echo "=== 3. Configure for iPhone 13 (iOS 18, arm64, Metal) ==="
cmake --preset ios-release \
    -DLIBERTY_IOS_DEVELOPMENT_TEAM="$TEAM_ID" \
    -DLIBERTY_IOS_BUNDLE_IDENTIFIER="$BUNDLE_ID"

echo ""
echo "=== 4. Build .app (~30-60 min on Apple Silicon, longer on Intel) ==="
cmake --build "$BUILD_DIR" --config Release -j$(sysctl -n hw.ncpu)

echo ""
echo "=== 5. Verify build output ==="
APP="$BUILD_DIR/LibertyRecomp/LibertyRecomp.app"
if [ -d "$APP" ]; then
    echo "OK: $APP built"
    du -sh "$APP"
    echo ""
    echo "Bundle ID: $BUNDLE_ID"
    echo "Team ID:   $TEAM_ID"
    echo ""
    echo "Next: install on iPhone 13"
    echo "  xcrun devicectl list devices"
    echo "  xcrun devicectl device install app --device <UDID> $APP"
else
    echo "ERROR: build failed — $APP not found"
    exit 1
fi
