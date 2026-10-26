#!/usr/bin/env python3
"""_edge_tts_one.py — synthesize ONE text line to an mp3 via edge-tts.

Isolated-subprocess helper for tools/gen_voice_free.py::tts_edge(). Running each
line in its own process guarantees edge-tts's websocket/aiohttp buffers are fully
released between lines — no accumulation, no OOM kills on long scripts.

Usage (called by gen_voice_free.py, not meant to be run directly):
  python tools/_edge_tts_one.py <text> <voice> <out_path>

Exits 0 on success (file written), non-zero on failure.
"""
import asyncio
import os
import sys


def main():
    if len(sys.argv) != 4:
        sys.exit("usage: _edge_tts_one.py <text> <voice> <out_path>")
    text, voice, out_path = sys.argv[1], sys.argv[2], sys.argv[3]

    async def go():
        import edge_tts
        comm = edge_tts.Communicate(text, voice=voice)
        await comm.save(out_path)

    asyncio.run(go())
    if not os.path.exists(out_path) or os.path.getsize(out_path) == 0:
        sys.exit("edge-tts wrote no audio (network blocked?)")
    sys.exit(0)


if __name__ == "__main__":
    main()
