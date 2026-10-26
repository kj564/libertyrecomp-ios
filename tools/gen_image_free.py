#!/usr/bin/env python3
"""
gen_image_free.py — 100% FREE in-video AI images via the z-ai-web-dev-sdk (CLI).

A free drop-in replacement for gen_image.py (which needs the paid Google Gemini API).
Same output contract: PNG + sidecar .json (prompt, model, refs, size) so any render can
be reproduced or re-rolled. Powered by the `z-ai image` CLI, which is free in this
environment and needs NO API KEY.

Size mapping: z-ai requires width/height in [512..2880], multiples of 32, and ≤ 2^22 pixels.
We map the factory's --aspect presets to the closest supported size:

  9:16  -> 768x1344   (vertical shorts, default)
  16:9  -> 1344x768   (landscape)
  1:1   -> 1024x1024  (square)
  4:3   -> 1152x864
  3:2   -> 1344x864   (closest mult-of-32)

A raw z-ai model id can also be passed via --model (ignored — z-ai has one model; kept for
CLI compatibility with gen_image.py).

Reference images (--ref) are NOT supported by the free z-ai image endpoint; they are ignored
with a warning. --seed is accepted for CLI compat but has no effect.

Usage:
  python tools/gen_image_free.py --prompt "..." --out shorts/short-7-kids/images/b1.png
  python tools/gen_image_free.py --prompt-file p.txt --aspect 9:16 --out x.png
  python tools/gen_image_free.py --prompt "..." --aspect 16:9 --out wide.png --dry-run

No API key needed. The z-ai CLI must be on PATH.
"""
import json
import os
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

ASPECT_TO_SIZE = {
    "9:16": "768x1344",
    "16:9": "1344x768",
    "1:1": "1024x1024",
    "4:3": "1152x864",
    "3:2": "1344x864",
    "3:4": "864x1152",
    "2:3": "864x1152",
}
DEFAULT_ASPECT = "9:16"
MODEL_NAME = "z-ai-free (z-ai-web-dev-sdk images.generations)"


def get_arg(args, name, default=None):
    return args[args.index(name) + 1] if name in args else default


def get_args_multi(args, name):
    return [args[i + 1] for i, a in enumerate(args) if a == name]


def rel(p):
    try:
        return os.path.relpath(p, ROOT)
    except ValueError:
        return p


def normalize_image(out_path):
    """z-ai sometimes returns JPEG bytes even when .png is requested. Honor the extension
    by re-encoding with PIL so downstream consumers (Remotion staticFile, gen_thumbnail) see a
    real PNG/JPEG matching its name."""
    try:
        from PIL import Image
    except ImportError:
        return  # PIL not available — leave bytes as-is; most tools detect format from content
    ext = os.path.splitext(out_path)[1].lower()
    try:
        im = Image.open(out_path)
        target = "PNG" if ext == ".png" else "JPEG"
        if im.format != target:
            im.save(out_path, target)
            print(f"  (re-encoded {im.format} -> {target} to match {ext})")
    except Exception as e:
        print(f"  (image normalize skipped: {e})")


def main():
    args = sys.argv[1:]
    dry = "--dry-run" in args

    prompt = get_arg(args, "--prompt")
    pf = get_arg(args, "--prompt-file")
    if pf:
        prompt = open(pf, encoding="utf-8").read()
    out = get_arg(args, "--out")
    if not prompt or not out:
        sys.exit("need --prompt/--prompt-file and --out (see file header)")

    model = get_arg(args, "--model", MODEL_NAME)  # accepted for CLI compat, ignored
    aspect = get_arg(args, "--aspect", DEFAULT_ASPECT)
    size = ASPECT_TO_SIZE.get(aspect)
    if size is None:
        # allow a raw WxH that satisfies z-ai constraints
        if "x" in aspect and all(p.isdigit() for p in aspect.split("x")):
            size = aspect
        else:
            sys.exit(f"unknown --aspect {aspect!r}; use one of {sorted(ASPECT_TO_SIZE)} or WxH")
    seed = get_arg(args, "--seed")
    refs = [r for r in get_args_multi(args, "--ref") if os.path.exists(r)]

    print(f"engine=z-ai-free  aspect={aspect}  size={size}  seed={seed}")
    if refs:
        print(f"  note: --ref ignored by the free z-ai image endpoint ({len(refs)} ref(s))")
    print(f"out -> {rel(out)}")
    if dry:
        print("[dry-run] validated; no API call.")
        return

    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    cmd = ["z-ai", "image", "-p", prompt, "-o", out, "-s", size]
    env = {**os.environ}
    r = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, env=env)
    if r.returncode != 0 or not os.path.exists(out):
        sys.exit(f"z-ai image failed:\n{r.stdout}")
    print(r.stdout.strip().splitlines()[-1] if r.stdout.strip() else "  ok")

    normalize_image(out)
    kb = os.path.getsize(out) // 1024
    print(f"  png  -> {rel(out)}  ({kb}KB)")

    sidecar = os.path.splitext(out)[0] + ".json"
    with open(sidecar, "w", encoding="utf-8") as f:
        json.dump({"prompt": prompt, "model": MODEL_NAME, "engine": "z-ai-free",
                   "aspect_ratio": aspect, "size": size, "seed": seed,
                   "refs": [rel(r) for r in refs], "ref_supported": False,
                   "created": time.strftime("%Y-%m-%dT%H:%M:%S")}, f, indent=2, ensure_ascii=False)
        f.write("\n")
    print(f"  meta -> {rel(sidecar)}")


if __name__ == "__main__":
    main()
