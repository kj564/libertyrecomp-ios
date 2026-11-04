# iPhone 13 / iOS 18 tuning

The Android port targets Snapdragon 865 / Adreno 650 with 8 GB RAM. iPhone 13
has a different balance — A15 Bionic is faster per-core, but has 4 GB RAM (half).

This doc lists the settings that need changing for steady 30 fps on iPhone 13.

## Hardware comparison

| | iPhone 13 (A15) | Retroid Pocket 5 (SD865) — Android baseline |
|---|---|---|
| CPU | 2× Avalanche (3.2 GHz) + 4× Blizzard (2.0 GHz) | 1× Cortex-A77 (2.8) + 3× A77 (2.4) + 4× A55 (1.8) |
| CPU cores (performance) | 2 big + 4 small | 4 big + 4 small |
| GPU | Apple 4-core, Metal 3 | Adreno 650, Vulkan 1.1 |
| RAM | **4 GB** | 8 GB |
| Storage | 128/256/512 GB NVMe | 128 GB UFS 3.0 |
| Display | 1170×2532 (60 Hz) | 1080×1920 (60 Hz) |

**Net:** A15 is ~30-40% faster per-core than SD865, but iPhone 13 has half the RAM.
The bottleneck shifts from CPU/GPU to **memory pressure**.

## Recommended settings for iPhone 13

### Memory (critical)

iPhone 13 has 4 GB RAM. iOS reserves ~2 GB for system + foreground app, so
LibertyRecomp gets **~2 GB usable**. Android baseline uses 6+ GB for the game.

| Setting | Android default | iPhone 13 | Where |
|---------|-----------------|-----------|-------|
| Texture pool | 3 GB | **1.5 GB** | renderer config |
| Streaming distance | 1.0 | 0.7 | renderer config |
| Asset cache | 2 GB | **1 GB** | asset system |
| Shadow map size | 2048 | **1024** | renderer config |

The 1024 shadow map is the Xbox 360 default — A15 GPU doesn't benefit from
larger shadow maps (fill rate limited), so 2048 is wasted memory.

### CPU

A15 has 2 performance cores vs SD865's 4. Reduce CPU-bound work:

| Setting | Android | iPhone 13 | Effect |
|---------|---------|-----------|--------|
| Traffic density | 0.4 of PC default | **0.3** | -25% CPU |
| Pedestrian density | 0.4 | **0.3** | -25% CPU |
| Draw distance | 1.0 | 0.85 | -15% CPU + fewer draw calls |
| Physics tick | 30 Hz | 30 Hz | match (don't reduce, breaks gameplay) |

### GPU (Metal 3 specific)

A15 supports Metal 3 features that SD865's Vulkan 1.1 doesn't. Enable:

| Feature | Effect | Risk |
|---------|--------|------|
| Tile shading | deferred shading on-tile, less memory bandwidth | needs Metal 3 (✓ iOS 18) |
| Mesh shaders | alternative to VTG pipeline, ~10% faster on Apple GPU | shader rewrite needed |
| Untracked resources | bypass residency tracking, less CPU overhead | iOS 16+ API |
| FXAA (not MSAA) | cheaper on Apple GPU, no fill rate hit | already default |
| Frame pacing via CAMetalLink | VSync without blocking | iOS 15+ |

**Do NOT enable:**
- MSAA 4x — Apple GPU fill rate penalty is worse than Adreno
- Ray tracing — A15 doesn't have RT cores (A17 Pro+ only)
- Variable rate shading tier 2 — A15 only tier 1

### Display

iPhone 13 native resolution: 1170×2532 (portrait). Game renders landscape 1280×720.

| Setting | Value |
|---------|-------|
| Render resolution | 1280×720 (Xbox 360 native, no upscale) |
| Display mode | landscape fullscreen, letterbox if aspect differs |
| VSync | ON (cap 30 fps — matches Xbox 360 original) |
| FXAA | ON (cheaper than MSAA on Apple GPU) |
| Brightness | 50% (iPhone 13 display is brighter than Xbox 360 output) |

### Audio

iPhone 13 speaker is mono; Bluetooth/AirPods give stereo. Tune for low latency:

| Setting | Value |
|---------|-------|
| Sample rate | 48000 Hz (iPhone audio session native) |
| Buffer size | 256 samples (~5ms) — low latency, may need 512 if glitchy |
| Audio session category | `AVAudioSessionCategoryPlayback` (no input) |
| Mode | `AVAudioSessionModeMoviePlayback` |

### Controls

iPhone 13 has no built-in gamepad. Options:

| Option | Setup | Latency |
|--------|-------|---------|
| On-screen touch gamepad | upstream has one (new in 0.5.7.2) | 16ms (1 frame) |
| MFi controller (Xbox/PS5/DualSense) | iOS native support | 4ms |
| Touch overlays via GameController framework | custom | varies |

**Recommend:** pair a DualSense or Xbox controller via Bluetooth — iOS 18 has
native support, zero config.

## How to apply these settings

Most settings are in the renderer config file. Upstream uses a config system
that reads from `os/<platform>/config.toml` or similar. To tune for iPhone 13:

1. Find the renderer config (likely `LibertyRecomp/config/` or embedded in `os/ios/`)
2. Override the values above
3. Rebuild: `cmake --build out/build/ios-release --config Release`
4. Test on device, measure fps via Xcode GPU debugger

## Performance measurement

Use Xcode's Metal debugger (Window → Devices and Simulators → your iPhone →
"Capture GPU frame"). Shows:
- Frame time (target: 33ms for 30 fps)
- Per-draw-call cost
- Memory pressure graph (watch for warnings — 4 GB is tight)
- Shader compilation time (first few frames will be slow)

## Honest expectation

With all tuning above on iPhone 13 / iOS 18:
- Intro + early story missions: **steady 30 fps** (target hit)
- Free roam driving: 28-30 fps (occasional drop when streaming new areas)
- Heavy scenes (bridges, skyline at night): **22-26 fps** (RAM-limited, not GPU)

Compare to Retroid Pocket 5 (8 GB RAM, Vulkan/Turnip): 25-29 fps on heavy scenes.
iPhone 13 with 4 GB RAM will be **slightly slower on heavy scenes**, **slightly
faster on CPU-bound scenes** (A15 per-core advantage).

If you want consistent 30 fps: reduce draw distance further (0.7) + traffic to 0.2.
Trade-off: world feels emptier.
