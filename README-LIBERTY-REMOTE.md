# LibertyRecomp Remote — PC Stream + Phone Controller

Main GTA IV di iPhone Anda dengan video stream dari PC + touch controller overlay.
Game jalan di PC (LibertyRecomp.exe), HP jadi controller + viewer.

## Yang dibangun

- **Web app** (Next.js, jalan di PC): launcher + MJPEG video stream + WebSocket input server
- **Frontend** (buka di HP browser): touch controller overlay (virtual joystick + action buttons GTA IV style)
- **Mini-service** (`mini-services/input-server`): WebSocket server yang terima touch input dari HP, simulate keyboard/mouse di PC

## Setup di Windows PC Anda

### Prasyarat

1. **LibertyRecomp.exe** — download dari https://github.com/OZORDI/LibertyRecomp/releases (latest v1.0.1)
2. **Game files GTA IV Xbox 360** (default.xex, common.rpf, xbox360.rpf, audio.rpf, dll.) — extract dari disc Anda sendiri
3. **Bun runtime** — install dari https://bun.sh
4. **ffmpeg** — install dari https://ffmpeg.org/download.html (tambahkan ke PATH)
5. **nircmd.exe** — download dari https://www.nirsoft.net/utils/nircmd.html (untuk simulate keyboard/mouse di Windows). Letakkan `nircmd.exe` di folder `mini-services/input-server/`

### Cara jalankan

1. **Clone repo ini di Windows PC Anda:**
   ```powershell
   git clone https://github.com/kj564/libertyrecomp-ios.git
   cd libertyrecomp-ios
   ```

2. **Edit `.env`** — set path ke LibertyRecomp.exe:
   ```
   LIBERTY_EXE_PATH=C:\Users\Anda\AppData\Local\LibertyRecomp\LibertyRecomp.exe
   LIBERTY_WORK_DIR=C:\Users\Anda\AppData\Local\LibertyRecomp\
   ```

3. **Install dependencies:**
   ```powershell
   bun install
   ```

4. **Start Next.js dev server** (di terminal 1):
   ```powershell
   bun run dev
   ```
   → jalan di http://localhost:3000

5. **Start input-server** (di terminal 2):
   ```powershell
   cd mini-services\input-server
   bun install
   bun run dev
   ```
   → WebSocket server di port 3003

6. **Cari IP PC Anda:**
   ```powershell
   ipconfig
   ```
   Catat IPv4 Address, misal `192.168.1.5`

7. **Di iPhone, buka browser:**
   ```
   http://192.168.1.5:3000
   ```
   - Rotasi iPhone ke landscape
   - Tap **Launch** untuk start LibertyRecomp di PC
   - Game tampil di iPhone (MJPEG stream)
   - Touch controller aktif (virtual joystick + tombol)

## Kontrol (GTA IV default)

### Movement (joystick kiri, bawah)
- W/A/S/D — gerak (walk/drive)

### Look (joystick kanan, bawah)
- Mouse move — kamera

### Action buttons
- **Jump** — Space
- **Enter** — F (masuk/keluar kendaraan)
- **Aim** — Right Mouse Button
- **Fire** — Left Mouse Button

### Side buttons (kiri)
- **Sprint** — Shift
- **Map** — Tab
- **Reload** — R

### Weapon select (kanan atas)
- 1-6 — pilih senjata

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│ Windows PC                                                  │
│                                                             │
│  Next.js app (port 3000)                                     │
│    /api/launch   → spawn LibertyRecomp.exe                   │
│    /api/status   → check process                            │
│    /api/stop     → kill process                             │
│    /api/stream   → ffmpeg screen capture → MJPEG           │
│                                                             │
│  Input-server (port 3003)                                   │
│    WebSocket → receives {type:"key"/"mouse"}                │
│    nircmd.exe → simulates keyboard/mouse                    │
│                                                             │
│  LibertyRecomp.exe (game process)                           │
└─────────────────────────────────────────────────────────────┘
                          ↑↓ HTTP + WebSocket
┌─────────────────────────────────────────────────────────────┐
│ iPhone (browser, landscape)                                 │
│                                                             │
│  <img src="/api/stream">    (MJPEG video)                   │
│  Virtual joysticks + buttons (touch → WebSocket)            │
└─────────────────────────────────────────────────────────────┘
```

## Latency

| Solusi | Latency | Quality |
|---|---|---|
| **Yang ini (MJPEG + WebSocket)** | 200-500ms | Basic |
| **Sunshine + Moonlight** (recommended alt) | 10-30ms | Excellent |
| **Steam Link** | 30-80ms | Good |

Kalau MJPEG terasa terlalu laggy, alternatif terbaik:
1. Install **Sunshine** di PC: https://github.com/LizardByte/Sunshine
2. Install **Moonlight** app di iPhone (App Store, gratis)
3. Pair keduanya, play LibertyRecomp dengan stream berkualitas tinggi

## Troubleshooting

**"PC Offline" di iPhone**
- Pastikan PC dan iPhone di WiFi yang sama
- Cek IP PC: `ipconfig` → gunakan IPv4 Address
- Cek Windows Firewall: allow port 3000 dan 3003

**Tombol tidak responsif**
- Pastikan `nircmd.exe` ada di `mini-services/input-server/`
- Cek terminal input-server — harus log "[ws] client connected"
- Cek browser iPhone console (Safari > Develop) untuk error

**Video stream hitam**
- Pastikan ffmpeg di PATH: `ffmpeg -version`
- Pastikan LibertyRecomp window di foreground
- Cek `/api/stream` langsung di browser PC — harus tampil video

**Game tidak launch**
- Cek path di `.env`: `LIBERTY_EXE_PATH`
- Cek file exists: `dir %LIBERTY_EXE_PATH%`
- Cek game files GTA IV sudah di-install (lihat README OZORDI/LibertyRecomp)

## File location

```
/home/z/my-project/
├── src/app/page.tsx              ← Frontend UI (touch controller + video)
├── src/app/api/
│   ├── launch/route.ts           ← POST: start LibertyRecomp.exe
│   ├── status/route.ts           ← GET: process status
│   ├── stop/route.ts             ← POST: kill process
│   └── stream/route.ts           ← GET: MJPEG stream
├── mini-services/input-server/
│   ├── index.ts                  ← WebSocket server (touch input → keyboard)
│   ├── package.json
│   └── run.sh                    ← auto-restart wrapper
└── .env                          ← LIBERTY_EXE_PATH config
```

## Push ke GitHub

Sudah di-push ke https://github.com/kj564/libertyrecomp-ios
Branch: `main`
Folder: root project Next.js

## Bukan solusi sempurna — jujur

Yang saya bangun ini fungsional tapi latency-nya 200-500ms (MJPEG). Untuk GTA IV yang butuh reflex, mungkin terasa laggy. **Sunshine + Moonlight** masih jauh lebih baik (10-30ms, hardware encoding).

Tapi kalau Anda tetap mau pakai yang saya bangun:
- Setup 5 menit (install Bun + ffmpeg + nircmd)
- Buka browser iPhone → langsung jalan
- Touch controller terintegrasi (tidak perlu Bluetooth controller)

Pilihan Anda.
