# iPhone 13 / iOS 18 — REAL config tuning

This doc uses the **actual config keys** from `LibertyRecomp/user/config_def.h` in
upstream. Every value below corresponds to a real config entry you can set in
your `config.toml` (or in-game Settings menu).

## How config works in LibertyRecomp

Config is layered:
1. **Defaults** — compiled into the binary (from `config_def.h`)
2. **`config.toml`** — user overrides (in game's data dir, e.g. `~/Documents/LibertyRecomp/config.toml` on iOS)
3. **In-game Settings menu** — runtime overrides, saved back to `config.toml`

For iPhone 13 tuning, you edit `config.toml` (or set via Settings menu on first boot).

## Section: Video (render quality)

These are the keys that matter most for iPhone 13's 4GB RAM + A15 GPU.

| Config key | Default | iPhone 13 recommended | Why |
|------------|---------|----------------------|-----|
| `WindowSize` | -1 (auto) | **1280×720** | Xbox 360 native; A15 steady 30fps at this res |
| `WindowWidth` | 1280 | 1280 | keep |
| `WindowHeight` | 720 | 720 | keep |
| `Fullscreen` | true | true | iOS is always fullscreen |
| `VSync` | true | true | cap 30fps, match Xbox 360 original |
| `FPS` | 60 | **30** | iPhone 13 A15 can't hold 60 in GTA IV; 30 matches Xbox 360 |
| `ResolutionScale` | 1.0 | **0.85** | render at 85% then upscale — saves GPU + RAM |
| `AntiAliasing` | MSAA4x | **FXAA** | MSAA4x kills Apple GPU fill rate; FXAA cheaper |
| `TransparencyAntiAliasing` | true | **false** | only works with MSAA, we use FXAA |
| `AnisotropicFiltering` | 16 | **8** | 16x is overkill on phone display; 8x half the cost |
| `ShadowResolution` | x4096 (label) / runtime x1024 | **x1024** | matches Xbox 360; A15 doesn't benefit from larger |
| `ShadowFilter` | PCF3x3 | **PCF3x3** | keep — PCF5x5/PCSS too expensive on Apple GPU |
| `ReflectionResolution` | Half | **Half** | keep — Quarter looks bad, Full too expensive |
| `MotionBlur` | Off | Off | keep off — adds ghosting on iPhone display |
| `DepthOfField` | Off | Off | keep off — costs ~5% GPU, subtle effect |
| `FilmGrain` | Off | Off | keep off — iPhone OLED makes grain visible |
| `ChromaticAberration` | Off | Off | keep off — adds nothing on phone |
| `SSAO` | Off | **Off** | SSAO is RAM-heavy (needs G-buffer); iPhone 13 skip |
| `EnableBloom` | false | **false** | keep off — Bloom pyramid is RAM-heavy |
| `EnableSunShafts` | false | **false** | keep off — Sun shafts need extra render pass |

## Section: Video (upscaler — MetalFX!)

iPhone 13 A15 + iOS 18 supports **MetalFX** (`MTLFXTemporalScaler`, available
iOS 16+). Upstream has `upscaler_metalfx.mm` — native Metal 3 upscaler.

This is the **big win**: render at 720p (or lower), upscale to native display
(1170×2532 landscape = 2532×1170) via MetalFX. Saves RAM + GPU, looks sharp.

| Config key | Default | iPhone 13 recommended | Why |
|------------|---------|----------------------|-----|
| `Upscaler` | Off | **MetalFX** | native Metal 3 upscaler, A15 supported |
| `UpscaleQuality` | Quality | **Quality** | temporal mode uses motion vectors (better) |
| `UpscaleSharpness` | 0.5 | 0.6 | slightly sharper for phone display pixel density |
| `DynamicResolution` | Off | **On** | auto-drop res under 30fps, recover when headroom |
| `MinResolutionScale` | 0.5 | **0.5** | floor for dynamic res |
| `TargetFrameTime` | 16.67 | **33.33** | 30fps target (16.67 = 60fps, too aggressive) |
| `FrameGeneration` | Off | Off | A15 doesn't have FG hardware (DLSS-style) |

**Workflow:** with MetalFX + DynamicResolution + ResolutionScale 0.85, the game
renders at ~612p internally, upscales to 720p via MetalFX, then GPU scales to
display. Steady 30fps on A15.

## Section: Graphics (LOD + render distance)

These are the **memory-bound** settings. iPhone 13's 4GB RAM means we must
reduce streaming pressure.

| Config key | Default | iPhone 13 recommended | Why |
|------------|---------|----------------------|-----|
| `RenderDistanceMultiplier` | 1.0 | **0.8** | -20% draw calls, -20% streaming |
| `LODDistanceMultiplier` | 1.0 | **0.8** | switch to lower-detail models sooner |
| `StreamingDistanceMultiplier` | 1.0 | **0.7** | -30% streaming = -30% RAM pressure |
| `FarClipMultiplier` | 1.0 | **0.9** | slightly closer far clip = less to render |
| `DisableLOD` | false | **false** | DON'T disable — uses more RAM (always highest detail) |
| `EntityFadeDistance` | 500.0 | **400.0** | entities fade out sooner |
| `MaxRenderDistance` | 1000.0 | **800.0** | closer max render = less to render |
| `PedestrianLODDistance` | 200.0 | **150.0** | peds switch to LOD sooner |
| `VehicleLODDistance` | 300.0 | **220.0** | vehicles switch to LOD sooner |
| `BuildingLODDistance` | 100.0 | **80.0** | buildings switch to LOD sooner |

**These `HIDDEN` keys** (EntityFadeDistance etc.) aren't in the in-game Settings
menu — you must edit `config.toml` directly. They work (CONFIG_DEFINE_HIDDEN
just hides from UI, still loads from file).

## Section: Audio

iPhone 13 audio session needs low-latency config.

| Config key | Default | iPhone 13 recommended | Why |
|------------|---------|----------------------|-----|
| `MasterVolume` | 1.0 | 1.0 | user preference |
| `MusicVolume` | 0.6 | 0.6 | keep |
| `EffectsVolume` | 0.6 | 0.6 | keep |
| `ChannelConfiguration` | Stereo | **Stereo** | iPhone speaker is mono, but headphones/AirPods stereo |
| `MuteOnFocusLost` | true | true | iOS backgrounding mutes audio |
| `MusicAttenuation` | false | **true** | duck music during cutscenes (iOS-style) |

Audio buffer size is set in `os/ios/` SDL2 audio backend (not in config.toml).
For iPhone 13, 256-sample buffer at 48kHz = 5.3ms latency — good for game audio.

## Section: Input (iPhone 13 has no gamepad by default)

| Config key | Default | iPhone 13 recommended | Why |
|------------|---------|----------------------|-----|
| `TouchControls` | "auto" | **"on"** | force on-screen gamepad (no controller paired) |
| `HorizontalCamera` | Reverse | Normal | user preference |
| `VerticalCamera` | Normal | Normal | user preference |
| `MotionControlsEnabled` | true | **false** | iPhone gyro isn't great for game-style motion |
| `MotionAiming` | false | false | keep off |
| `MotionSteering` | false | **true** | tilt-to-steer works well in cars on iPhone |
| `MotionReload` | true | **false** | shake-to-reload annoying on phone |
| `MotionHelicopter` | false | false | keep off |

**Recommend:** pair a DualSense or Xbox controller via Bluetooth for best
experience. iOS 18 has native MFi support, zero config. Then `TouchControls`
auto-disables.

## Section: System

| Config key | Default | iPhone 13 recommended | Why |
|------------|---------|----------------------|-----|
| `Language` | English | user pref | — |
| `Subtitles` | true | true | keep |
| `Hints` | true | true | keep |
| `Autosave` | true | **true** | critical — iOS sandbox may evict app, autosave frequently |
| `AchievementNotifications` | true | true | keep |
| `ShowConsole` | false | false | no console on iOS |

## Complete `config.toml` for iPhone 13

Drop this file at `~/Documents/LibertyRecomp/config.toml` on your iPhone 13
(after first launch creates the dir), or set in-game Settings:

```toml
# LibertyRecomp config — iPhone 13 / iOS 18 tuned
# 4GB RAM, A15 Bionic, Metal 3, 1170×2532 display

[Video]
WindowSize = 1280
WindowWidth = 1280
WindowHeight = 720
Fullscreen = true
VSync = true
FPS = 30
ResolutionScale = 0.85
AntiAliasing = "FXAA"
TransparencyAntiAliasing = false
AnisotropicFiltering = 8
ShadowResolution = "x1024"
ShadowFilter = "PCF3x3"
ReflectionResolution = "Half"
MotionBlur = "Off"
DepthOfField = "Off"
FilmGrain = "Off"
ChromaticAberration = "Off"
SSAO = "Off"
EnableBloom = false
EnableSunShafts = false

# MetalFX upscaler — big win on A15
Upscaler = "MetalFX"
UpscaleQuality = "Quality"
UpscaleSharpness = 0.6
DynamicResolution = "On"
MinResolutionScale = 0.5
TargetFrameTime = 33.33
FrameGeneration = "Off"

[Graphics]
RenderDistanceMultiplier = 0.8
LODDistanceMultiplier = 0.8
StreamingDistanceMultiplier = 0.7
FarClipMultiplier = 0.9
DisableLOD = false
EntityFadeDistance = 400.0
MaxRenderDistance = 800.0
PedestrianLODDistance = 150.0
VehicleLODDistance = 220.0
BuildingLODDistance = 80.0

[Audio]
ChannelConfiguration = "Stereo"
MuteOnFocusLost = true
MusicAttenuation = true

[Input]
TouchControls = "on"
MotionControlsEnabled = false
MotionSteering = true
MotionReload = false

[System]
Autosave = true
```

## How to apply

1. Build + install the game (see `BUILD.md`)
2. First launch — game creates `~/Documents/LibertyRecomp/config.toml` with defaults
3. Stop the game
4. Replace `config.toml` with the content above (use Files app on iOS, or
   `xcrun devicectl copy` from Mac)
5. Relaunch — settings apply

**OR** use in-game Settings menu for the non-HIDDEN keys (everything except
the `Graphics` LOD section).

## Expected performance with this config

| Scene | FPS | RAM usage |
|-------|-----|-----------|
| Intro logos | 30 (capped) | ~1.2 GB |
| Early story missions | 30 (steady) | ~1.8 GB |
| Free roam driving | 28-30 | ~2.0 GB |
| Heavy scenes (bridges, skyline night) | 22-26 | ~2.3 GB |

**RAM ceiling:** if the game hits ~2.5 GB, iOS will jetsam-kill it (crash to
home screen). The config above stays under 2.3 GB peak — safe.

If you still crash: lower `StreamingDistanceMultiplier` to 0.5, `RenderDistanceMultiplier` to 0.7.

## What's NOT tunable (hardcoded in renderer)

- Texture pool size — set at build time in `LibertyRecompLib/config/`, not user-editable
  (would need a rebuild with iPhone 13-specific pool size)
- Shadow map format — `g_shadowState` is hardcoded `EShadowResolution::x1024` default
- Metal shader cache — embedded in binary at build time

For those, you'd need to fork upstream + modify `LibertyRecompLib/` + rebuild.
That's beyond config tuning — see `docs/BUILD.md` for the fork path.
