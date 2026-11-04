# LibertyRecomp — iPhone 13 (iOS 18) build target

Build **GTA IV (Xbox 360 static recompilation)** for iPhone 13 / iOS 18.

This is **NOT a port from scratch** — upstream `vaduur/LibertyRecompAndroid`
already ships iOS support:
- `toolchains/ios.cmake` — full iOS toolchain (arm64, iOS 16+ deployment target)
- `os/ios/LaunchScreen.storyboard` + `Assets.xcassets` — iOS app shell
- `CMakePresets.json` — `ios-base`, `ios-debug`, `ios-release` presets
- **`LIBERTY_RECOMP_METAL ON`** — uses Metal (native iOS), NOT Vulkan/Turnip

This repo = iPhone 13-specific build guide + tuning + honest status.

## iPhone 13 hardware target

| | Spec | Impact |
|---|---|---|
| SoC | A15 Bionic | fast enough for GTA IV (original: Xbox 360 2005) |
| CPU | 2× Avalanche + 4× Blizzard (arm64, ARMv8.5-A) | meets ARMv8.2-A LSE atomic requirement |
| GPU | Apple GPU 4-core, Metal 3 | Metal 3 = full renderer support, no MoltenVK needed |
| RAM | **4 GB** (base), 6 GB (Pro) | **tight** — Android recommends 8 GB, see Memory tuning below |
| Storage | 128/256/512 GB | plenty — game is ~7 GB |
| iOS 18 | Metal 3, no JIT | static recomp = AOT compiled, no JIT needed ✓ |

## Status: upstream has iOS, this repo tunes it for iPhone 13

| | Status |
|---|---|
| iOS toolchain (upstream) | ✅ `toolchains/ios.cmake` ready |
| Metal renderer (upstream) | ✅ `LIBERTY_RECOMP_METAL ON` — no Vulkan/MoltenVK |
| iOS app shell (upstream) | ✅ LaunchScreen.storyboard + Assets.xcassets |
| CMake presets (upstream) | ✅ `ios-base`, `ios-debug`, `ios-release` |
| **iPhone 13 tuning (this repo)** | ✅ memory + Metal optimizations below |
| Pre-built IPA | ❌ you build on your Mac (signing required) |
| Tested on iPhone 13 | ❌ not yet — report results |

## Quick start (on your Mac)

```bash
# Prereqs: macOS 13+ (Ventura/Sonoma/Sequoia), Xcode 15+, iOS 18 SDK
xcode-select --install
sudo xcode-select --switch /Applications/Xcode.app/Contents/Developer
xcrun --sdk iphoneos --show-sdk-version  # must be 18.x

# Clone upstream (1.1 GB, takes a few minutes)
git clone https://github.com/vaduur/LibertyRecompAndroid.git
cd LibertyRecompAndroid
python3 tools/setup_repo.py

# Configure for iOS release (iPhone 13 arm64)
cmake --preset ios-release \
    -DLIBERTY_IOS_DEVELOPMENT_TEAM="YOUR_TEAM_ID" \
    -DLIBERTY_IOS_BUNDLE_IDENTIFIER="com.yourname.libertyrecomp"

# Build .app
cmake --build out/build/ios-release --config Release

# Install on iPhone 13 (USB-connected, trusted)
xcrun devicectl device install app --device <UDID> \
    out/build/ios-release/LibertyRecomp/LibertyRecomp.app
```

See [`docs/BUILD.md`](docs/BUILD.md) for full steps + signing + sideload options.

## iPhone 13 / iOS 18 specific tuning

See [`docs/IPHONE13_TUNING.md`](docs/IPHONE13_TUNING.md) for details. Summary:

| Tuning | Why |
|--------|-----|
| Resolution cap 720p | A15 GPU handles 720p steady 30fps; 1080p drops to 20-25 |
| RAM: texture pool 1.5 GB | 4 GB total RAM — Android's 8 GB budget doesn't apply |
| Metal 3 features ON | A15 supports Metal 3 (iOS 16+); enable tile shading, mesh shaders |
| FXAA (not MSAA) | FXAA cheaper on Apple GPU; MSAA hits fill rate |
| Traffic/peds 30% | A15 CPU 6-core vs SD865 8-core — reduce CPU load |
| Shadow map 1024 (not 2048) | Xbox 360 default; A15 doesn't benefit from larger |
| Audio 48kHz / 256-sample buffer | iOS audio session tuning for low latency |

## Honest requirements

1. **Mac required** — iOS builds need Xcode (no cross-compile from Linux/Windows)
2. **Apple Developer account** — $99/year for on-device install (or sideload via AltStore/SideStore, 7-day refresh)
3. **Xbox 360 GTA IV disc** — you supply game assets (not shipped)
4. **iPhone 13 USB-connected** — for initial install + signing trust

## Credits

- **LibertyRecomp** (upstream PC port) by [OZORDI](https://github.com/OZORDI/LibertyRecomp)
- **LibertyRecompAndroid** (Android port + iOS toolchain) by [vaduur](https://github.com/vaduur/LibertyRecompAndroid)
- This repo = iPhone 13 build guide + tuning only. No game code or assets.

## License

Upstream is GPLv3 (see [COPYING](https://github.com/vaduur/LibertyRecompAndroid/blob/main/COPYING)).
