# GTA IV di iPhone 13 via Husk + LibertyRecomp

## Cara kerja

```
iPhone 13 (A15 Bionic, iOS 18, 4GB RAM)
  Husk.app (sideload via SideStore/AltStore)
    Translation Layer (native arm64, no QEMU)
      LibertyRecomp APK (v0.5.9.3)
        GTA IV Xbox 360 (statically recompiled)
          Runs DIRECTLY on A15 CPU (no emulation!)
```

LibertyRecomp = static recompilation (AOT). Husk translation-layer loads .so,
translates SDL3 ke UIKit/Metal, Vulkan ke MoltenVK. Tidak ada QEMU, tidak
ada Android boot, tidak ada JIT.

## Step 1: Install Husk

### SideStore (gratis, 7 hari refresh)
1. Install SideStore: https://sidestore.io
2. Add source di SideStore: `https://itslevii.dev/repo.json`
3. Install Husk dari source list

### AltStore (alternatif)
1. Download Husk.ipa (135 MB):
   https://github.com/Leviidev/Husk/releases/download/3.4/Husk.ipa
2. Sideload via AltStore

## Step 2: Download LibertyRecomp APK

Download APK (45 MB):
https://github.com/vaduur/LibertyRecompAndroid/releases/download/v0.5.9.3/LibertyRecompAndroid-v0.5.9.3.apk

## Step 3: Import APK ke Husk

1. Buka Husk di iPhone 13
2. Tab Library > tap tombol +
3. Pilih file LibertyRecompAndroid-v0.5.9.3.apk
4. Husk scan APK, detect:
   - lib/arm64-v8a/libLibertyRecomp.so
   - SDL3 activity
   - Game assets

## Step 4: Setup Game Assets

LibertyRecomp butuh Xbox 360 GTA IV game files. Extract dari disc Anda:
default.xex, default.xexp, aes_key.bin, common.rpf, xbox360.rpf, audio.rpf,
folder common/ xbox360/ audio/ update/

1. Zip semua file tersebut
2. Transfer ke iPhone 13 (via Files app, AirDrop, atau Husk file manager)
3. Di Husk > game settings > Data Files > import zip

## Step 5: Tuning iPhone 13

### Husk Settings (per-app)
Buka LibertyRecomp di Husk > tap gear icon:

- Resolution: Low (1x) - 4GB RAM, render 720p native
- Orientation: Landscape
- JIT Method: AOT (JIT-less) - LibertyRecomp is AOT, no JIT needed
- On-screen Pad: Auto (show if no MFi controller)
- Window Mode: Full Screen

### Husk Translation Layer Settings
- Vulkan backend: MoltenVK (Husk bundles untuk iOS)
- EGL backend: ANGLE (Husk builds ANGLE for Metal)
- Audio: CoreAudio (native iOS)
- Memory limit: 2.5 GB (4GB total, reserve 1.5GB untuk iOS + Husk)

### LibertyRecomp config.toml
Letakkan di game data directory:

[Video]
WindowWidth = 1280
WindowHeight = 720
Fullscreen = true
VSync = true
FPS = 30
ResolutionScale = 0.85
AntiAliasing = "FXAA"
AnisotropicFiltering = 8
ShadowResolution = "x1024"
ShadowFilter = "PCF3x3"
ReflectionResolution = "Half"
MotionBlur = "Off"
DepthOfField = "Off"
SSAO = "Off"
EnableBloom = false
EnableSunShafts = false
Upscaler = "MetalFX"
UpscaleQuality = "Quality"
UpscaleSharpness = 0.6
DynamicResolution = "On"
MinResolutionScale = 0.5
TargetFrameTime = 33.33

[Graphics]
RenderDistanceMultiplier = 0.8
LODDistanceMultiplier = 0.8
StreamingDistanceMultiplier = 0.7
FarClipMultiplier = 0.9
EntityFadeDistance = 400.0
MaxRenderDistance = 800.0
PedestrianLODDistance = 150.0
VehicleLODDistance = 220.0
BuildingLODDistance = 80.0

[Audio]
ChannelConfiguration = "Stereo"
MuteOnFocusLost = true
MusicAttenuation = true

[System]
Autosave = true

## Step 6: Setup JIT-less

LibertyRecomp = static recompilation = AOT code, no JIT needed.

1. Husk Settings > JIT & Sideload > Method: Built-in StikJIT atau None
2. Saat launch pertama, Husk akan:
   - Convert libLibertyRecomp.so menjadi Mach-O dylib (AOT)
   - Sign dengan developer certificate Anda
   - Run dylib langsung (native arm64)
3. Proses AOT: 2-5 menit (sekali saja)

## Step 7: Play

1. Buka Husk
2. Library > tap LibertyRecomp
3. Game launches:
   - Husk loads libLibertyRecomp.so (as Mach-O dylib)
   - SDL3 menjadi UIKit (window, touch input)
   - Vulkan menjadi MoltenVK menjadi Metal (rendering)
   - Audio menjadi CoreAudio
4. GTA IV boots: NOW LOADING > CRIWARE > AM2 > main menu

## Controller

Pair DualSense atau Xbox controller via Bluetooth.
iOS 18 punya native MFi support, Husk auto-detect dan map ke Android gamepad API.

## Expected Performance

- Boot logos: 30 fps
- Main menu: 30 fps steady
- Free roam: 25-30 fps
- Heavy scenes (bridges, skyline): 20-25 fps (RAM-limited)

Compare: Retroid Pocket 5 (SD865, 8GB): 25-29 fps
iPhone 13 (A15, 4GB, via Husk): 25-30 fps (A15 per-core faster)

## Troubleshooting

App crashes on launch:
- Check JIT method = AOT/JIT-less
- Check APK version v0.5.9.3
- Check game assets properly extracted

Black screen:
- Check Vulkan backend = MoltenVK
- Check Resolution = Low (1x)
- Check config.toml location correct

Low FPS (under 20):
- Lower ResolutionScale to 0.7
- Set FPS to 30
- Reduce traffic density

Audio crackling:
- Set audio buffer to 512 samples
- Check CoreAudio selected

## Links

Husk releases: https://github.com/Leviidev/Husk/releases
LibertyRecomp APK: https://github.com/vaduur/LibertyRecompAndroid/releases
SideStore: https://sidestore.io
Husk website: https://itslevii.dev/husk
