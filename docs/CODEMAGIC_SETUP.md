# Setup Codemagic CI for LibertyRecomp iOS build

GitHub Actions macOS minutes habis setelah 41 runs. Codemagic CI
alternatif gratis untuk public repo (500 min/month macOS).

## One-time setup (5 menit)

### 1. Daftar Codemagic

1. Buka https://codemagic.io
2. Klik "Sign Up" → pilih "Sign up with GitHub"
3. Authorize Codemagic untuk akses GitHub kamu

### 2. Tambah repo

1. Di Codemagic dashboard, klik **"Add application"**
2. Pilih **GitHub** sebagai source
3. Pilih repo **kj564/libertyrecomp-ios**
4. Pilih platform **macOS**
5. Pilih workflow type **Codemagic CLI**

### 3. Enable codemagic.yaml

1. Di app settings, scroll ke **"Build configuration"**
2. Set "Configuration file" ke `codemagic.yaml`
3. Pastikan branch = `main`
4. Save

### 4. Trigger build pertama

- Push commit apapun ke `main` repo → Codemagic auto-detect codemagic.yaml
- Atau klik **"Start new build"** di dashboard Codemagic

## Apa yang dilakukan build

Workflow yang sama seperti GitHub Actions (41 runs debug):
1. Install vcpkg + LLVM 18 + MoltenVK
2. Clone upstream LibertyRecompAndroid
3. Patch iOS-specific (skip MoltenVK, GNS, NFD, FFmpeg, discord-rpc)
4. Configure dengan vcpkg arm64-ios triplet
5. Build .app
6. Package unsigned .ipa

## Output

- Artifact: `LibertyRecomp-unsigned.ipa` (downloadable dari Codemagic dashboard)
- Build logs (kalau gagal): CMakeCache.txt, CMakeOutput.log, CMakeError.log
- Retensi: 30 hari

## Limit

- **500 macOS minutes/month** (gratis untuk public repo)
- Max build duration: 180 min (3 jam)
- Instance: Mac mini M2

## Status patches (41 runs progress)

| Patch | Status | Run yang fix |
|-------|--------|--------------|
| MoltenVK AppKit | ✅ | #1-7 |
| LLVM 18 | ✅ | #8 |
| ReXGlue Vulkan | ✅ | #14 |
| fmt::fmt | ✅ | #16 |
| SDL3::SDL3-static | ✅ | #18 |
| nfd::nfd | ✅ | #34 |
| GameNetworkingSockets | ✅ | #39 |
| FFmpeg libavcodec | ✅ | #40 (belum tested - quota habis) |
| msdf-atlas-gen, XenonUtils | ❓ | next run |

## Setelah build sukses

1. Download `LibertyRecomp-unsigned.ipa` dari Codemagic dashboard
2. Buka Sideloadly di PC
3. Masukin Apple ID kamu
4. Drag .ipa ke Sideloadly
5. Install di iPhone 13 (7 hari refresh)

## Troubleshooting

### "No matching signing certificate"

Codemagic butuh Apple Developer cert untuk signing. Tapi karena kita
build **unsigned** .ipa (-DLIBERTY_IOS_DEVELOPMENT_TEAM=""), cert nggak
dibutuhkan. Sideloadly akan re-sign dengan Apple ID kamu sendiri.

### "vcpkg build timeout"

vcpkg build SDL3 + 8 deps dari source butuh 30-60 menit. Pastikan
`max_build_duration: 180` di codemagic.yaml (sudah set).

### "Configure failed: target X not found"

Cek patch step log — mungkin target baru yang belum di-skip.
Lihat GitHub Actions run history untuk pattern fix yang sudah ada.
