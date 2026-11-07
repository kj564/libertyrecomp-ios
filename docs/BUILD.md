# Building LibertyRecomp for iPhone 13 (iOS 18)

Complete honest pipeline. You need a Mac — there is no way around this for iOS.

## Prerequisites

### Mac setup (one-time)

| Requirement | Version | Notes |
|--------------|---------|-------|
| macOS | 13.5+ (Ventura/Sonoma/Sequoia) | Xcode 15+ requires it |
| Xcode | 15.0+ (recommended 16+) | includes iOS 18 SDK |
| Command Line Tools | match Xcode | `xcode-select --install` |
| CMake | 3.28+ | `brew install cmake` |
| Ninja | 1.11+ | `brew install ninja` (faster than make) |
| Python | 3.10+ | for `tools/setup_repo.py` |

Verify:
```bash
xcode-select -p                         # /Applications/Xcode.app/...
xcrun --sdk iphoneos --show-sdk-version # 18.x
cmake --version                          # 3.28+
python3 --version                        # 3.10+
```

### Apple Developer account (for on-device install)

- **Option A — Paid Developer Program ($99/year):** install persists for 1 year, up to 100 devices
- **Option B — Free Apple ID:** install persists 7 days, max 3 apps, refresh via AltStore/SideStore
- **Option C — Jailbreak:** no signing needed (not recommended; risks device)

For Option A, get your Team ID at https://developer.apple.com/account (Membership → Team ID).

## Steps

### 1. Clone + setup (first time, ~15 min)

```bash
git clone https://github.com/vaduur/LibertyRecompAndroid.git
cd LibertyRecompAndroid
python3 tools/setup_repo.py   # pulls submodules: SDL2, Mesa, FidelityFX, etc.
```

Repo size after setup: ~2.5 GB (git + submodules + vcpkg).

### 2. Configure for iPhone 13

```bash
cmake --preset ios-release \
    -DLIBERTY_IOS_DEVELOPMENT_TEAM="ABCDE12345" \
    -DLIBERTY_IOS_BUNDLE_IDENTIFIER="com.yourname.libertyrecomp"
```

Replace `ABCDE12345` with your Apple Team ID. The `ios-release` preset:
- Uses `toolchains/ios.cmake` (arm64, iOS 16+ deploy target)
- Sets `LIBERTY_RECOMP_METAL ON` (Metal renderer, no Vulkan)
- Sets `LIBERTY_RECOMP_EMBEDDED_ASSETS ON` (assets packaged at build time)

### 3. Build the .app

```bash
cmake --build out/build/ios-release --config Release -j$(sysctl -n hw.ncpu)
```

Build time: ~30-60 min on M1/M2/M3 Mac, longer on Intel. Output:
`out/build/ios-release/LibertyRecomp/LibertyRecomp.app`

### 4. Game asset packaging

The iOS build uses `LIBERTY_RECOMP_EMBEDDED_ASSETS=ON` — assets are packaged into
the .app bundle at build time (no installer UI on iOS). Place your Xbox 360 GTA IV
files at the path configured by `LIBERTY_RECOMP_EMBEDDED_GAME_PATH` (default:
`tools/local_game_payload/`):

```
tools/local_game_payload/
├── default.xex
├── default.xexp
├── aes_key.bin
├── common.rpf
├── xbox360.rpf
├── audio.rpf
├── common/
├── xbox360/
├── audio/
└── update/
```

You extract these from your own Xbox 360 GTA IV disc using `tools/extract-xiso`
(bundled submodule) or `tools/XexToolGUI`.

### 5. Install on iPhone 13

**USB-connect iPhone 13, trust the Mac, then:**

```bash
# List connected devices, get UDID
xcrun devicectl list devices

# Install
xcrun devicectl device install app --device <UDID> \
    out/build/ios-release/LibertyRecomp/LibertyRecomp.app
```

**First launch:** Settings → General → VPN & Device Management → trust your Developer cert.

## Troubleshooting (honest)

### "No signing certificate" / code signing failed

You need a valid Apple Developer cert installed in Keychain. Verify:
```bash
security find-identity -v -p codesigning
```
If empty: open Xcode → Settings → Accounts → your Apple ID → Download Manual Profile.

### "Metal feature not available"

iPhone 13 A15 supports Metal 3 (iOS 16+). If you see this error, your iOS deployment
target is too low. Verify in `toolchains/ios.cmake`:
```cmake
set(CMAKE_OSX_DEPLOYMENT_TARGET "16.0" ...)
```
iPhone 13 on iOS 18 → change to `"18.0"` if you want to require iOS 18 features.

### Out of memory (app crashes on launch)

iPhone 13 has 4 GB RAM. Android recommends 8 GB. Apply the tuning in
[`IPHONE13_TUNING.md`](IPHONE13_TUNING.md): cap texture pool, reduce traffic,
lower shadow map.

### "This app cannot be installed" / 7-day limit

Free Apple ID signing expires in 7 days. Refresh via AltStore or SideStore,
or get a paid Developer Program membership ($99/year) for 1-year installs.

### Game code signing restrictions

iOS sandbox blocks memory mapping executable (`PROT_EXEC`) for non-Apple-signed
binaries. Static recompilation = AOT compiled C++ → native Mach-O binary, so
**no JIT is needed**. This is why iOS is feasible where a JIT-based emulator is not.

## What does NOT work on iOS (honest)

| Feature | Status | Why |
|---------|--------|-----|
| Online multiplayer | ❌ | requires Sony/NP infrastructure; upstream removed |
| Episodes (TLAD, TBOGT) | ⚠️ untested | upstream says "not tested on Android" |
| Discord RPC | ❌ | vcpkg marks it `!ps4 & !ps5` but iOS also can't use it |
| Bink video | ✅ should work | native decoder, no external dep |
| Savegame | ✅ | iOS sandbox paths in `os/ios/` |

## Build on cloud Mac (if you don't have one)

If you don't own a Mac:
- **MacStadium / MacInCloud** — rent Mac mini by hour (~$1/hr)
- **GitHub Actions macOS runner** — free for public repos, 6 hr/mo
- **Xcode Cloud** — Apple's CI, integrates with App Store (but this app won't pass App Store review)

The iOS build is pure CMake + Xcode — any of these work.

## References

- Upstream Android port: https://github.com/vaduur/LibertyRecompAndroid
- Upstream PC port: https://github.com/OZORDI/LibertyRecomp
- iOS toolchain source: `toolchains/ios.cmake` in upstream repo
- CMake presets: `CMakePresets.json` → `ios-base`, `ios-debug`, `ios-release`
