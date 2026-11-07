# LibertyRecomp Remote — PC Stream + Phone Touch Controller

Play GTA IV (LibertyRecomp) on your iPhone with video stream from PC + touch controller overlay.
Game runs on PC, phone acts as controller + viewer.

## Setup (Windows PC)

### Prerequisites

1. **LibertyRecomp.exe** — download from https://github.com/OZORDI/LibertyRecomp/releases (v1.0.1)
2. **Game files GTA IV Xbox 360** (default.xex, common.rpf, xbox360.rpf, audio.rpf) — extract from your own disc
3. **Bun runtime** — https://bun.sh
4. **ffmpeg** — https://ffmpeg.org/download.html (add to PATH)
5. **nircmd.exe** — https://www.nirsoft.net/utils/nircmd.html (place in `mini-services/input-server/`)

### Steps

```powershell
# 1. Clone repo
git clone https://github.com/kj564/libertyrecomp-ios.git
cd libertyrecomp-ios

# 2. Install dependencies
bun install
cd mini-services/input-server && bun install && cd ../..

# 3. Configure
copy .env.example .env
# Edit .env: LIBERTY_EXE_PATH=C:\Users\You\AppData\Local\LibertyRecomp\LibertyRecomp.exe

# 4. Start Next.js dev server (terminal 1)
bun run dev

# 5. Start input-server (terminal 2)
cd mini-services/input-server
bun run dev

# 6. Find PC IP
ipconfig

# 7. Open on iPhone browser (landscape)
# http://PC_IP:3000
```

Tap **Launch** → game streams to iPhone, touch controller active.

## Controls (GTA IV default)

| Touch | Keyboard |
|---|---|
| Left joystick | W/A/S/D (move) |
| Right joystick | Mouse move (camera) |
| Jump button | Space |
| Enter button | F (vehicle enter/exit) |
| Aim button | Right Mouse Button |
| Fire button | Left Mouse Button |
| Sprint button | Shift |
| Map button | Tab |
| Reload button | R |
| Weapon 1-6 | 1-6 keys |

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│ Windows PC                                              │
│                                                         │
│  Next.js app (port 3000)                                │
│    /api/launch   → spawn LibertyRecomp.exe              │
│    /api/status   → check process                        │
│    /api/stop     → kill process                         │
│    /api/stream   → ffmpeg screen capture → MJPEG        │
│                                                         │
│  Input-server (port 3003)                               │
│    WebSocket → receives {type:"key"/"mouse"}             │
│    nircmd.exe → simulates keyboard/mouse                │
│                                                         │
│  LibertyRecomp.exe (game process)                       │
└─────────────────────────────────────────────────────────┘
                       ↑↓ HTTP + WebSocket
┌─────────────────────────────────────────────────────────┐
│ iPhone (browser, landscape)                             │
│                                                         │
│  <img src="/api/stream">    (MJPEG video)               │
│  Virtual joysticks + buttons (touch → WebSocket)         │
└─────────────────────────────────────────────────────────┘
```

## Latency (honest)

| Solution | Latency | Quality |
|---|---|---|
| **This (MJPEG + WebSocket)** | 200-500ms | Basic |
| Sunshine + Moonlight | 10-30ms | Excellent |
| Steam Link | 30-80ms | Good |

For best latency, install **Sunshine** (PC) + **Moonlight** (iPhone App Store). This project is for quick setup without extra software.

## Troubleshooting

**"PC Offline" on iPhone**
- Ensure PC + iPhone on same Wi-Fi
- Check IP: `ipconfig` → use IPv4 Address
- Allow port 3000 + 3003 in Windows Firewall

**Buttons not responsive**
- Verify `nircmd.exe` in `mini-services/input-server/`
- Check input-server terminal — should show "[ws] client connected"

**Black video stream**
- Verify ffmpeg in PATH: `ffmpeg -version`
- Verify LibertyRecomp window in foreground

## File locations

```
src/app/page.tsx              — Frontend UI (touch controller + video)
src/app/api/
  ├── launch/route.ts         — POST: start LibertyRecomp.exe
  ├── status/route.ts         — GET: process status
  ├── stop/route.ts           — POST: kill process
  └── stream/route.ts         — GET: MJPEG stream
mini-services/input-server/
  ├── index.ts                — WebSocket server (touch → keyboard)
  ├── package.json
  └── run.sh                  — auto-restart wrapper
.env                          — LIBERTY_EXE_PATH config
```

## Source

- LibertyRecomp (Windows): https://github.com/OZORDI/LibertyRecomp
- This repo: https://github.com/kj564/libertyrecomp-ios

## License

Code in this repo: MIT-style, free to use.
LibertyRecomp itself: see https://github.com/OZORDI/LibertyRecomp for license.
