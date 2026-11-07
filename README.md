<<<<<<< HEAD
# claude-faceless-shorts-creator

**A faceless YouTube-Shorts factory you drive with [Claude Code](https://claude.com/claude-code).**
Three production tracks in one repo — you just describe the video, and the right pipeline runs:

| You say… | Track | The pixels |
|---|---|---|
| *"make a short about the ×11 trick"* | **TSX** (`/make-short`) | 100% code — a [Remotion](https://remotion.dev) composition, no footage, no stock |
| *"make an AI video short with blue-man"* | **Generative** (`/make-ai-short`) | a fal video model animating a **locked recurring character** |
| *"make a vox-style short about coffee"* | **Collage** (`/make-vox`) | Vox-documentary paper collage — AI-image layers, die-cuts, a traveling camera |

Every track shares the same backbone: ElevenLabs voice with **word-exact synced captions**,
frame-by-frame QA at phone scale, a reusable self-growing SFX/music library, seamless
frame-0==last-frame loops, and no dated engagement-CTA outros.

## 📖 Read the guide

I wrote up the whole system on my site, including the six-beat grammar that decides whether a
40-second short is worth finishing:
**[Make Faceless YouTube Shorts With Claude Code](https://learnwithhasan.com/guide/how-to-make-faceless-youtube-shorts-with-claude-code/?utm_source=github&utm_medium=readme&utm_campaign=claude-faceless-shorts-creator&utm_content=body)**

Free to read, no login. More build guides at
**[learnwithhasan.com/guides](https://learnwithhasan.com/guides/?utm_source=github&utm_medium=readme&utm_campaign=claude-faceless-shorts-creator&utm_content=body)**.

## The example videos (more coming)

**TSX shorts** (`shorts/`) — 12 complete productions; each folder has the script, beats
contract, and SFX cue sheet, and the committed composition renders the exact video:

| # | Niche | Title / hook |
|---|---|---|
| 1 | Chess | The 4-Move Checkmate — Punished |
| 2 | Math | The ×11 Trick |
| 3 | Algorithms | Bubble vs Quick: The Race |
| 4 | Dev tips | `git reflog` undoes any mistake |
| 5 | Probability | Monty Hall, Finally Intuitive |
| 6 | Excel | Excel Reads Your Mind (Flash Fill / Ctrl+E) |
| 7 | Kids story | Little Pip (AI-image storybook, ages 4–6) |
| 8 | Cybersecurity | The URL That Isn't PayPal |
| 9 | Music theory | The 4 Chords In Every Hit |
| 10 | Money math | The 1% Fee That Eats 24% Of Your Retirement |
| 11 | Geography | The Map Lied To You |
| 12 | Physics | Astronauts Aren't Weightless. They're Falling. |

**Generative** (`ai-shorts/blue-man/`) — *The Door*: a clay-render character walking through
doors across worlds, thesis "arrival is a myth". Includes the **locked character sheet**
(`character.json` + reference PNG), the model bake-off records (Seedance vs Kling vs Veo, with
derived per-second costs), and the six generated clips — committed, because video-model pixels
are not reproducible.

**Collage** (`vox-shorts/vox-1-coffee/`) — a Vox-style documentary short on coffee's journey:
generated map/archival/cutout layers (committed), a camera choreographed across scenes, and
`DESIGN.md` — the full visual-language spec of the collage engine.

Rendered videos aren't committed (they're reproducible from the repo); links to published
versions will be added here as they go live.

## How a short gets made

```
topic ──▶ script.md + beats.json      the beat grammar: HOOK (frame 0 = the thumbnail)
                │                      → SETUP → QUIZ → REVEAL → TWIST → seamless LOOP
                ▼
        the visuals                    TSX composition / video-model clips / collage layers
                │                      (per track — but always ONE Remotion timeline)
                ▼
        frame-by-frame QA              Claude renders PNGs at phone scale and READS them
                │
                ▼
        gen_voice.py                   ElevenLabs TTS per line → REAL per-word timestamps
                │                      → captions highlight on the exact spoken word
                ▼
        sfx-plan.json + mix_sfx.py     library-first sound design, audition mix, your ear
                │                      is the final gate (optional music bed: mix_music.py)
                ▼
        <track>/<project>/output/*-sfx.mp4
```

Five Claude Code **skills** encode the craft:

- **`/make-short`** — the TSX pipeline: hook grammar, no-CTA outros, caption safe areas,
  Sequence-local frame math, loop-into-intro endings.
- **`/make-ai-short`** — the generative pipeline and its three iron rules: never regenerate a
  locked character from text, state the cost before spending it, loop by end-frame constraint.
- **`/make-vox`** — scene dissection into layers, cheapest-source layer production
  (gen_image + rembg cutouts, HTML→PNG, SVG-in-TSX), CollageBoard camera choreography.
- **`/vidtsx-2d-generator`** — the TSX authoring rules that keep Remotion renders from crashing.
- **`/suggest-sfx`** — taste-encoded sound design: function-first cues, layered hero moments,
  measured audibility (RMS-diff, not hope), a library that compounds across videos.

`brand.md` is the style contract (palette, type, motion, SFX taste) — swap it for your own
brand and every future short follows it.

## Quickstart

Requirements: [Claude Code](https://claude.com/claude-code) · Node 18+ · Python 3.10+ ·
`ffmpeg` on PATH · an [ElevenLabs](https://elevenlabs.io) key (voice/SFX/music). For the
generative track add a [fal.ai](https://fal.ai) key; for collage layer production:
`pip install pillow rembg playwright && playwright install chromium` (the only pip installs
in the repo — everything else is stdlib).

```bash
git clone https://github.com/hassancs91/claude-faceless-shorts-creator
cd claude-faceless-shorts-creator
cp .env.example .env          # add your keys
cd remotion && npm install && npm run gen && cd ..

claude                        # open the repo in Claude Code, then:
```

> **make a short about &lt;your topic&gt;** · **make an AI video short about &lt;idea&gt;** ·
> **make a vox-style short about &lt;story&gt;**

…or rebuild an example: *"re-render short-5 and regenerate its voice"*.

To just explore the compositions visually: `cd remotion && npm run studio`.

## Repo layout

```
.claude/skills/   the five skills (this is where the "editor" lives)
tools/            Python: gen_voice, gen_sfx, gen_music, mix_sfx, mix_music, gen_image,
                  gen_clip, bakeoff_clip, cutout, capture_web, gen_chords
remotion/         the Remotion project — shared kits in src/lib/ (incl. collage.tsx),
                  one folder per video in src/shots/
media/library/    reusable assets: SFX clips + music beds (catalogued, loudness-normalized)
media/projects/   media for one specific video — incl. committed AI clips & collage layers
shorts/           the 12 TSX example productions
ai-shorts/        the generative track: blue-man/ (locked character) + IDEAS.md (cost tables)
vox-shorts/       the collage track: vox-1-coffee/ + DESIGN.md (the visual language)
brand.md          the style contract — make it yours
IDEAS.md          the TSX-shorts niche/idea bank
```

## License

MIT — see [LICENSE](LICENSE). Bundled SFX/music clips and example AI media were generated by
the repo author (ElevenLabs / fal / Gemini) and are redistributed here; per-clip provenance is
recorded in `media/library/*/catalog.json` and the per-shot `.json` sidecars.

<!-- lwh-footer -->

---

## 📘 The free book

This repo is one thing I built with AI. The book is the system underneath it.

**[Vibe Engineering Blocks](https://learnwithhasan.com/blocks/?utm_source=github&utm_medium=readme&utm_campaign=claude-faceless-shorts-creator&utm_content=footer)** is my free 74-page book.
47 building blocks for shipping real apps with AI. One block per page, each with the exact
prompt to hand your AI.

Built by **[Hasan Aboul Hasan](https://learnwithhasan.com/?utm_source=github&utm_medium=readme&utm_campaign=claude-faceless-shorts-creator&utm_content=footer)**. I build real products with AI and
write down exactly how.
[Guides](https://learnwithhasan.com/guides/?utm_source=github&utm_medium=readme&utm_campaign=claude-faceless-shorts-creator&utm_content=footer) &nbsp;·&nbsp;
[YouTube](https://www.youtube.com/@HasanAboulHasan) &nbsp;·&nbsp;
[Community](https://learnwithhasan.com/community/?utm_source=github&utm_medium=readme&utm_campaign=claude-faceless-shorts-creator&utm_content=footer)
=======
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
>>>>>>> 6b3cb2ad90e85fb2e7158260c56ca0d54475ffc0
