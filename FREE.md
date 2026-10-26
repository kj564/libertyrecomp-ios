# FREE — running the shorts factory with ZERO paid API keys

The original `claude-faceless-shorts-creator` needs three paid services: **ElevenLabs**
(voice/SFX/music), **Google Gemini** (images), **fal.ai** (AI video clips). This doc maps
each paid touchpoint to a **100% free replacement** that works in this environment via the
`z-ai-web-dev-sdk` (the platform's free AI) and `edge-tts` (Microsoft's free neural TTS).

**No API key is required for the free path.** Leave `ELEVENLABS_API_KEY`, `GEMINI_API_KEY`
and `FAL_KEY` empty in `.env`.

## The mapping

| Paid tool | Needs | Free replacement | Status |
|---|---|---|---|
| `tools/gen_voice.py` | ElevenLabs key | **`tools/gen_voice_free.py`** — `z-ai` TTS (default) or `edge-tts` | ✅ works |
| `tools/gen_image.py` | Gemini key | **`tools/gen_image_free.py`** — `z-ai image` CLI | ✅ works |
| `tools/gen_clip.py` | fal.ai key | **no free SDK** — generate stills with `gen_image_free.py`, animate via Remotion Ken Burns (see `shorts/short-7-kids/`) | ⚠️ workaround |
| `tools/gen_sfx.py` | ElevenLabs key | **the committed library** — 33 SFX clips in `media/library/sfx/clips/` reused, never regenerated | ✅ free |
| `tools/gen_music.py` | ElevenLabs key | **`tools/gen_chords.py`** — deterministic chord synthesis (no API), + 6 committed music beds in `media/library/music/clips/` | ✅ free |

## Voice — `gen_voice_free.py`

A drop-in replacement for `gen_voice.py` with the **same output contract** (per-line mp3 +
`.words.json`, assembled `voice.wav`, beats.json written back with real timings, optional
`vo.gen.ts`). `/make-short`, `mix_sfx.py` and the TSX captions work unchanged.

```bash
# Generate the full voice track for a short (default engine = z-ai, batch mode = ~1 API call)
python tools/gen_voice_free.py --beats shorts/short-1-chess/beats.json \
    --emit-ts remotion/src/shots/short-1/vo.gen.ts

# Plan only (no API calls)
python tools/gen_voice_free.py --beats shorts/short-1-chess/beats.json --dry-run

# Mux the voice onto a rendered (silent) mp4 for a voiced preview
python tools/gen_voice_free.py --beats ... --mux remotion/out/Short1Chess.mp4

# English voice, Microsoft edge-tts (local machine only — sandboxed egress kills its websocket)
python tools/gen_voice_free.py --beats ... --engine edge --voice en-US-GuyNeural

# One call per line (no batching) — only if a voice renders joined text poorly
python tools/gen_voice_free.py --beats ... --no-batch
```

**Batch mode (default):** consecutive lines are joined into chunks ≤ 900 chars and
synthesized as ONE TTS call, then split back into per-line clips at proportional time
boundaries. A 17-line / ~700-char short becomes ~1 API call — comfortably inside the free
z-ai quota (which is ~13 calls/window).

**Word timing:** proportional (char-weighted), the same fallback `gen_voice.py` uses when
ElevenLabs timestamps are unavailable. Captions highlight ~on beat, not word-exact. For
word-EXACT captions, add a forced aligner (`aeneas` / `whisper`) — out of scope here.

**z-ai voices:** `tongtong`, `chuichui`, `xiaochen`, **`jam` (English gentleman)**, `kazi`,
`douji`, `luodo`. Default `jam` is the English pick.

**edge-tts voices:** any Microsoft neural voice, e.g. `en-US-GuyNeural`, `en-US-AriaNeural`,
`en-GB-RyanNeural`. Needs free outbound network (not available inside this sandbox).

## Images — `gen_image_free.py`

A drop-in for `gen_image.py` (same PNG + sidecar `.json` contract). Powered by the free
`z-ai image` CLI. No API key.

```bash
# Vertical 9:16 storybook frame (mapped to the valid z-ai size 768x1344)
python tools/gen_image_free.py --prompt "warm storybook illustration of a small bird..." \
    --aspect 9:16 --out shorts/short-7-kids/images/b1-hook.png

# Landscape / square
python tools/gen_image_free.py --prompt "..." --aspect 16:9 --out wide.png
python tools/gen_image_free.py --prompt "..." --aspect 1:1 --out square.png
```

**Aspect → size** (z-ai requires multiples of 32, 512–2880 px, ≤ 2²² pixels):
`9:16→768x1344`, `16:9→1344x768`, `1:1→1024x1024`, `4:3→1152x864`, `3:2→1344x864`.

**Limitations vs paid Gemini:** `--ref` (reference-image conditioning) is not supported by
the free z-ai image endpoint — ignored with a warning. `--seed` is accepted for CLI
compatibility but has no effect.

## SFX — already free

The library at `media/library/sfx/clips/` (33 clips) is **committed and reusable** — check
`catalog.json` first, reuse before generating. `mix_sfx.py` places these cues and needs no
API key. New SFX generation (`gen_sfx.py`, ElevenLabs) is optional — the library covers the
factory's needs.

## Music — already free

`tools/gen_chords.py` synthesizes chords **deterministically** (equal temperament, A4=440,
additive harmonics) — no API, no key, identical every run. The 4 piano clips
(`piano-c-maj/g-maj/a-min/f-maj`) live in the SFX library and are placed by `mix_sfx.py`.
6 ambient music beds are committed in `media/library/music/clips/`.

```bash
# Regenerate the chord clips (free)
python tools/gen_chords.py --force
```

## Video — the one gap

There is no free video-generation SDK in this environment. For the generative track
(`/make-ai-short`), the free workaround is the **`short-7-kids` pattern**: generate 9:16
stills with `gen_image_free.py`, then Ken-Burns animate them in Remotion (the TSX track).
This produces a fully-synthetic short with no paid video model. True AI video clips
(`gen_clip.py` / fal.ai) still require a key.

## Full free workflow (example: short-1)

```bash
# 1. (scripts/beats already committed in shorts/short-1-chess/)
# 2. Generate the free voice track — ONE z-ai TTS call for all 17 lines
python tools/gen_voice_free.py --beats shorts/short-1-chess/beats.json \
    --emit-ts remotion/src/shots/short-1/vo.gen.ts

# 3. Mix the SFX library onto the voiced track (free — reads committed library)
python tools/mix_sfx.py --beats shorts/short-1-chess/beats.json \
    --voice shorts/short-1-chess/voice/voice.wav \
    --out shorts/short-1-chess/output/short-1-sfx.mp4 \
    --video remotion/out/Short1Chess.mp4

# Result: a fully-voiced, sound-designed short — $0 API spend.
```

## When to still use the paid path

| Want | Use |
|---|---|
| Word-EXACT captions (not proportional) | `gen_voice.py` (ElevenLabs char-level alignment) |
| Reference-image conditioning | `gen_image.py` (Gemini) |
| Real AI video motion (not Ken Burns) | `gen_clip.py` (fal.ai) |

The free and paid tools coexist — pick per project. The `.env` keys are all optional.
