#!/usr/bin/env python3
"""
gen_voice_free.py — 100% FREE voice track for a TSX short, driven by its beats.json.

A free drop-in replacement for gen_voice.py (which needs the paid ElevenLabs API).
Same output contract so /make-short, mix_sfx.py and the TSX captions work unchanged:

  shorts/<short>/voice/line-NN-<hash>.mp3 + .words.json   (per-line clips + word maps)
  shorts/<short>/voice/voice.wav                          (assembled, loudness-normalized)
  beats.json written back with REAL line timings + per-word start/end (global timeline)
  optional --emit-ts  -> remotion/src/shots/short-N/vo.gen.ts (imported by the composition)

Two free engines, auto-fallback:
  --engine zai  (default)  z-ai-web-dev-sdk TTS via the `z-ai` CLI (FREE in this environment).
                            Voices: tongtong, chuichui, xiaochen, jam (English), kazi, douji, luodo.
                            BATCH MODE (default): joins consecutive lines into chunks ≤ 900 chars,
                            so a full 17-line / ~700-char short collapses to ~1 TTS call — well
                            inside the free-tier quota. Word timing: proportional (char-weighted).
  --engine edge            edge-tts (Microsoft neural voices, FREE, no API key). Best English voices.
                            NOTE: edge-tts keeps a websocket open for the whole synthesis; in
                            sandboxed environments with tight egress rules, the process can be
                            SIGKILL'd mid-call. Use this on a local machine with free outbound
                            network. Word timing: proportional.

USAGE
  python tools/gen_voice_free.py --beats shorts/short-1-chess/beats.json
  python tools/gen_voice_free.py --beats ... --emit-ts remotion/src/shots/short-1/vo.gen.ts
  python tools/gen_voice_free.py --beats ... --mux remotion/out/Short1Chess.mp4   # voiced preview
  python tools/gen_voice_free.py --beats ... --engine zai --voice jam
  python tools/gen_voice_free.py --beats ... --dry-run                           # plan only

No API key required. ffmpeg/ffprobe must be on PATH. Default edge voice: en-US-GuyNeural.
Library-first caching: unchanged lines (text+voice+engine hash) are never re-generated.
"""
import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DEFAULT_ENGINE = "zai"  # edge-tts's websocket gets SIGKILL'd in sandboxed environments;
                         # z-ai TTS is the robust free path here (batch mode = 1 call/short).
DEFAULT_VOICE_EDGE = "en-US-GuyNeural"
DEFAULT_VOICE_ZAI = "jam"
MAX_ATEMPO = 1.3  # never speed a line up more than 30%

# Delivery tags like [excited], [pause] — steer some engines, never captioned.
TAG_RE = re.compile(r"\[[^\]]+\]")


def load_env():
    env = {}
    p = os.path.join(ROOT, ".env")
    if os.path.exists(p):
        for line in open(p, encoding="utf-8"):
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            env[k.strip()] = v.strip().strip('"').strip("'")
    return {**env, **os.environ}


def run(cmd):
    r = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    if r.returncode != 0:
        sys.exit(f"command failed: {' '.join(cmd)}\n{r.stdout}")
    return r.stdout


def probe_duration(path):
    out = run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
               "-of", "default=noprint_wrappers=1:nokey=1", path])
    return float(out.strip())


def strip_tags(text):
    """Remove [excited]/[pause] delivery tags for captioning + some TTS engines."""
    return TAG_RE.sub("", text).strip()


def tts_edge(text, voice, out_path):
    """edge-tts: synthesize ONE line in an isolated subprocess so the websocket/aiohttp
    buffers never accumulate across a long script (which OOM-kills in-process loops).
    Returns out_path on success; raises on failure."""
    helper = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_edge_tts_one.py")
    r = subprocess.run([sys.executable, helper, text, voice, out_path],
                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    if r.returncode != 0 or not os.path.exists(out_path) or os.path.getsize(out_path) == 0:
        raise RuntimeError(f"edge-tts failed: {r.stdout.strip()[:200] or 'no audio'}")
    return out_path


def tts_zai(text, voice, out_path):
    """z-ai-web-dev-sdk TTS via the `z-ai` CLI. Streams audio to out_path (memory-safe).
    Retries on HTTP 429 (free-tier rate limit) with exponential backoff."""
    tmp_wav = out_path + ".zai.wav"
    cmd = ["z-ai", "tts", "-i", text, "-o", tmp_wav, "--voice", voice, "--format", "wav"]
    last_err = ""
    for attempt in range(5):  # up to ~30s of backoff total
        r = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        if r.returncode == 0 and os.path.exists(tmp_wav) and os.path.getsize(tmp_wav) > 0:
            break
        last_err = r.stdout
        # 429 = free-tier rate limit — back off and retry
        if "429" in r.stdout or "Too many requests" in r.stdout:
            wait = 2 ** attempt  # 1, 2, 4, 8, 16s
            print(f"    (rate-limited; retry {attempt + 1}/5 in {wait}s)")
            time.sleep(wait)
            continue
        sys.exit(f"z-ai TTS failed for: {text!r}\n{r.stdout}")
    else:
        sys.exit(f"z-ai TTS kept rate-limiting for: {text!r}\n{last_err}")
    run(["ffmpeg", "-y", "-v", "error", "-i", tmp_wav, "-codec:a", "libmp3lame",
         "-b:a", "128k", out_path])
    os.remove(tmp_wav)
    return out_path


def proportional_words(text, clip_dur):
    """Distribute words across clip_dur seconds, weighted by char count (+1 for spacing).
    This is the factory's documented fallback when real alignment is unavailable."""
    words = [w for w in strip_tags(text).split() if w]
    if not words:
        return []
    weights = [len(w) + 1 for w in words]
    total = sum(weights)
    out, t = [], 0.0
    for w, wt in zip(words, weights):
        dur = clip_dur * wt / total
        out.append({"w": w, "start": round(t, 3), "end": round(t + dur, 3)})
        t += dur
    # snap last end to clip_dur to avoid float drift
    if out:
        out[-1]["end"] = round(clip_dur, 3)
    return out


def tts_line(engine, voice, text, out_path):
    """TTS one line -> writes the mp3 AND <out_path>.words.json (per-word start/end in the RAW clip)."""
    if engine == "zai":
        tts_zai(text, voice, out_path)
    else:
        tts_edge(text, voice, out_path)
    dur = probe_duration(out_path)
    words = proportional_words(text, dur)
    with open(out_path + ".words.json", "w", encoding="utf-8") as f:
        json.dump(words, f, ensure_ascii=False)
    return dur


def tts_batch(engine, voice, lines):
    """Batch TTS: join `lines` (list of (text, out_path)) into ONE call (≤ 1024 chars),
    synthesize the joined audio, then split it into per-line clips at proportional
    (char-weighted) time boundaries. Collapses N line calls into 1 call per chunk —
    keeps a full short inside the free tier's quota AND stays under the sandbox's
    external-connection kill threshold.

    Writes each raw mp3 + .words.json (proportional within each split clip)."""
    joined = ". ".join(strip_tags(t) for t, _ in lines)
    if len(joined) > 1024:
        raise RuntimeError(f"batch text {len(joined)} chars > 1024 limit")
    chunk_path = lines[0][1] + ".batch.mp3"  # temp joined clip
    # one TTS call for the whole chunk — engine picks edge-tts or z-ai
    if engine == "zai":
        tts_zai(joined, voice, chunk_path)
    else:
        tts_edge(joined, voice, chunk_path)
    chunk_dur = probe_duration(chunk_path)
    # proportional split: each line's duration ∝ its stripped char count (+1 separator)
    weights = [len(strip_tags(t)) + 1 for t, _ in lines]
    total_w = sum(weights)
    t = 0.0
    for (text, out_path), wt in zip(lines, weights):
        seg_dur = chunk_dur * wt / total_w
        run(["ffmpeg", "-y", "-v", "error", "-ss", f"{t:.3f}", "-t", f"{seg_dur:.3f}",
             "-i", chunk_path, "-codec:a", "libmp3lame", "-b:a", "128k", out_path])
        words = proportional_words(text, seg_dur)
        with open(out_path + ".words.json", "w", encoding="utf-8") as f:
            json.dump(words, f, ensure_ascii=False)
        t += seg_dur
    os.remove(chunk_path)


def chunk_lines(items, max_chars=900):
    """Group (text, out_path) items into chunks whose joined text stays under max_chars
    (leaving headroom under the 1024 z-ai limit for the '. ' separators)."""
    chunks, cur, cur_len = [], [], 0
    for it in items:
        n = len(strip_tags(it[0])) + 2  # +2 for '. ' separator
        if cur and cur_len + n > max_chars:
            chunks.append(cur)
            cur, cur_len = [], 0
        cur.append(it)
        cur_len += n
    if cur:
        chunks.append(cur)
    return chunks


def emit_ts(vo, path, engine):
    """Write the generated VO (with word times) as a TS module the shot imports."""
    lines = ["// AUTO-GENERATED by tools/gen_voice_free.py — do not edit.",
             f"// Free TTS engine: {engine}. Word times are proportional estimates; "
             "captions highlight ~on beat.",
             "import type { VoLine } from '../../lib/shorts';", "",
             "export const VO: VoLine[] = ["]
    for line in vo:
        esc = line["text"].replace("\\", "\\\\").replace("'", "\\'")
        ws = ", ".join(
            "{ w: '%s', start: %s, end: %s }" % (
                w["w"].replace("\\", "\\\\").replace("'", "\\'"), w["start"], w["end"])
            for w in line.get("words", []))
        lines.append(f"  {{ text: '{esc}', start: {line['start']}, end: {line['end']}, words: [{ws}] }},")
    lines += ["];", ""]
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--beats", required=True, help="path to the short's beats.json")
    ap.add_argument("--engine", default=DEFAULT_ENGINE, choices=["edge", "zai"],
                    help=f"TTS engine (default: {DEFAULT_ENGINE})")
    ap.add_argument("--voice", help=f"voice id (edge default: {DEFAULT_VOICE_EDGE}; zai default: {DEFAULT_VOICE_ZAI})")
    ap.add_argument("--zai-delay", type=float, default=1.5,
                    help="seconds to pause between BATCHES on the z-ai engine (default: 1.5)")
    ap.add_argument("--no-batch", action="store_true",
                    help="disable batch mode (one z-ai TTS call per line) — hits the free quota fast")
    ap.add_argument("--emit-ts", help="write VO with word times as a TS module, e.g. remotion/src/shots/short-1/vo.gen.ts")
    ap.add_argument("--mux", help="optional rendered mp4 to mux the voice onto (-voiced.mp4)")
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    voice = args.voice or (DEFAULT_VOICE_ZAI if args.engine == "zai" else DEFAULT_VOICE_EDGE)

    beats_path = os.path.abspath(args.beats)
    beats = json.load(open(beats_path, encoding="utf-8"))
    vo = beats["vo"]
    total = float(beats["format"]["durationSec"])
    vdir = os.path.join(os.path.dirname(beats_path), "voice")
    os.makedirs(vdir, exist_ok=True)

    if args.dry_run:
        print(f"engine={args.engine}  voice={voice}")
        print(f"{'line':4s} {'start':>6s} {'window':>6s}  text")
        for i, line in enumerate(vo):
            start = float(line["start"])
            next_start = float(vo[i + 1]["start"]) if i + 1 < len(vo) else total - 0.3
            window = next_start - start - 0.05
            print(f"{i:4d} {start:6.2f} {window:6.2f}  {line.get('tts', line['text'])}")
        return

    fitted = []  # (path, start_sec, fitted_dur)
    # Pre-compute per-line raw clip paths. Caching is by (engine|voice|tts_text) hash so
    # unchanged lines are never re-billed — same contract as gen_voice.py.
    plan = []  # (i, tts_text, raw_path, fit_path, hash)
    for i, line in enumerate(vo):
        tts_text = line.get("tts", line["text"])
        h = hashlib.sha1(f"{args.engine}|{voice}|{tts_text}".encode()).hexdigest()[:8]
        raw = os.path.join(vdir, f"line-{i:02d}-{h}.mp3")
        fit = os.path.join(vdir, f"line-{i:02d}-{h}-fit.wav")
        plan.append((i, tts_text, raw, fit, h))

    # ---- GENERATE missing clips ----------------------------------------------
    # BATCH by default for BOTH engines: join consecutive lines into chunks ≤ 900 chars
    # (one TTS call each), then split the chunk audio into per-line clips at proportional
    # time boundaries. A full 17-line / ~700-char short collapses to ~1 TTS call — well
    # inside the free z-ai quota AND under the sandbox's external-connection kill threshold
    # (one connection per chunk, not one per line).
    # --no-batch forces the original one-call-per-line path (needed only if a voice renders
    # the joined text poorly, e.g. sentence-internal emphasis is lost).
    use_batch = not args.no_batch
    missing = [(t, r) for (_, t, r, _, _) in plan
               if args.force or not os.path.exists(r) or not os.path.exists(r + ".words.json")]
    if missing:
        if use_batch:
            chunks = chunk_lines(missing)
            print(f"engine={args.engine}  voice={voice}  batch: {len(missing)} line(s) in {len(chunks)} call(s)")
            for ci, chunk in enumerate(chunks):
                if ci > 0:
                    time.sleep(args.zai_delay if args.engine == "zai" else 0.5)
                try:
                    tts_batch(args.engine, voice, chunk)
                except Exception as e:
                    # edge-tts external connection killed / blocked -> fall back to z-ai batch
                    if args.engine == "edge":
                        print(f"    (edge-tts failed: {e}; falling back to z-ai batch)")
                        args.engine = "zai"
                        voice = args.voice or DEFAULT_VOICE_ZAI
                        # re-plan with new engine hash and re-run the batch path
                        plan = []
                        for j, line in enumerate(vo):
                            tt = line.get("tts", line["text"])
                            hh = hashlib.sha1(f"{args.engine}|{voice}|{tt}".encode()).hexdigest()[:8]
                            plan.append((j, tt, os.path.join(vdir, f"line-{j:02d}-{hh}.mp3"),
                                         os.path.join(vdir, f"line-{j:02d}-{hh}-fit.wav"), hh))
                        missing = [(t, r) for (_, t, r, _, _) in plan
                                   if args.force or not os.path.exists(r) or not os.path.exists(r + ".words.json")]
                        for chunk in chunk_lines(missing):
                            tts_batch(args.engine, voice, chunk)
                    else:
                        raise
                print(f"  batch {ci + 1}/{len(chunks)}: {len(chunk)} line(s) -> ok")
        else:
            print(f"engine={args.engine}  voice={voice}  (per-line, no batch)")
            for i, tts_text, raw, fit, _h in plan:
                if args.force or not os.path.exists(raw) or not os.path.exists(raw + ".words.json"):
                    tts_line(args.engine, voice, tts_text, raw)
                    if args.engine == "zai" and i < len(vo) - 1:
                        time.sleep(args.zai_delay)

    # ---- FIT each line to its window + assemble ------------------------------
    print(f"{'line':4s} {'start':>6s} {'window':>6s} {'clip':>6s} {'tempo':>5s}  text")
    for (i, tts_text, raw, fit, _h), line in zip(plan, vo):
        start = float(line["start"])
        next_start = float(vo[i + 1]["start"]) if i + 1 < len(vo) else total - 0.3
        window = next_start - start - 0.05

        dur = probe_duration(raw)
        tempo = 1.0
        if dur > window:
            tempo = min(MAX_ATEMPO, dur / window)
        if args.force or not os.path.exists(fit):
            run(["ffmpeg", "-y", "-v", "error", "-i", raw,
                 "-filter:a", f"atempo={tempo:.4f}", "-ar", "44100", "-ac", "2", fit])
        fdur = probe_duration(fit)
        overflow = " OVERFLOW" if fdur > window + 0.05 else ""
        print(f"{i:4d} {start:6.2f} {window:6.2f} {fdur:6.2f} {tempo:5.2f}  {line['text']}{overflow}")
        line["end"] = round(start + fdur, 2)
        raw_words = json.load(open(raw + ".words.json", encoding="utf-8"))
        line["words"] = [{"w": w["w"],
                          "start": round(start + w["start"] / tempo, 3),
                          "end": round(start + w["end"] / tempo, 3)} for w in raw_words]
        fitted.append((fit, start, fdur))

    # assemble: delay each line to its start, sum (lines never overlap), pad to length
    voice_wav = os.path.join(vdir, "voice.wav")
    inputs, parts = [], []
    for j, (path, start, _d) in enumerate(fitted):
        inputs += ["-i", path]
        ms = int(round(start * 1000))
        parts.append(f"[{j}:a]adelay={ms}|{ms}[a{j}]")
    chain = "".join(f"[a{j}]" for j in range(len(fitted)))
    fc = ";".join(parts) + f";{chain}amix=inputs={len(fitted)}:normalize=0,apad,atrim=0:{total}," \
         f"loudnorm=I=-16:TP=-1.5:LRA=11[out]"
    run(["ffmpeg", "-y", "-v", "error", *inputs, "-filter_complex", fc,
         "-map", "[out]", "-ar", "44100", "-ac", "2", voice_wav])
    print(f"voice track -> {os.path.relpath(voice_wav, ROOT)}")

    beats["voiceStatus"] = f"free:{args.engine}:{voice}"
    json.dump(beats, open(beats_path, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
    print(f"actual line timings + word maps written back -> {os.path.relpath(beats_path, ROOT)}")

    if args.emit_ts:
        emit_ts(vo, rp := os.path.abspath(args.emit_ts), args.engine)
        print(f"VO TS module -> {os.path.relpath(rp, ROOT)}")

    if args.mux:
        out = os.path.splitext(args.mux)[0] + "-voiced.mp4"
        run(["ffmpeg", "-y", "-v", "error", "-i", args.mux, "-i", voice_wav,
             "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
             "-t", str(total), out])
        print(f"voiced preview -> {os.path.relpath(out, ROOT)}")


if __name__ == "__main__":
    main()
