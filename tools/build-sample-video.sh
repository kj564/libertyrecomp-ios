#!/bin/bash
# build-sample-video.sh — build a 15s vertical sample short with ffmpeg (no Chrome needed).
# Uses AI-generated chess images + free voice track + committed music library.
# Output: public/sample/sample-short.mp4 (1080x1920, 30fps, ~15s)
set -e

ROOT="/home/z/my-project"
SAMPLE_DIR="$ROOT/public/sample"
VOICE="$ROOT/shorts/short-1-chess/voice/voice.wav"
MUSIC="$ROOT/media/library/music/clips/cinematic-min.mp3"
OUT="$SAMPLE_DIR/sample-short.mp4"
TMP="/tmp/sample-build"
mkdir -p "$TMP"

# Fonts
FONT_BOLD="/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONT_REG="/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
FONT_MONO="/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"

# Brand colors
INDIGO="0x6366F1"
WHITE="0xFFFFFF"
INK="0x1A1A2E"
MUTED="0x8B949E"
PAPER="0xFFFEF7"

# Images
IMG1="$SAMPLE_DIR/chess-board.png"
IMG2="$SAMPLE_DIR/queen-closeup.png"
IMG3="$SAMPLE_DIR/checkmate.png"

echo "=== building scene 1: title + chess board (0-4.5s) ==="
ffmpeg -y -v error -loop 1 -t 4.5 -i "$IMG1" \
  -filter_complex "
    [0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,
    zoompan=z='min(1+0.25*on/135,1.25)':d=135:s=1080x1920:fps=30[zoomed];
    [zoomed]drawbox=x=0:y=0:w=1080:h=420:color=black@0.55:t=fill[bg];
    [bg]drawtext=fontfile=$FONT_BOLD:text='THE 4-MOVE':fontsize=82:fontcolor=$WHITE:x=(w-text_w)/2:y=180:line_spacing=8,
    drawtext=fontfile=$FONT_BOLD:text='CHECKMATE':fontsize=92:fontcolor=$INDIGO:x=(w-text_w)/2:y=280,
    drawtext=fontfile=$FONT_REG:text='wins millions of games':fontsize=42:fontcolor=$MUTED:x=(w-text_w)/2:y=420,
    fade=in:0:15,fade=out:st=4.0:d=0.5
  " -t 4.5 -r 30 -pix_fmt yuv420p "$TMP/scene1.mp4"
echo "  scene1.mp4 done"

echo "=== building scene 2: queen + moves (4.5-10s) ==="
ffmpeg -y -v error -loop 1 -t 5.5 -i "$IMG2" \
  -filter_complex "
    [0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,
    zoompan=z='min(1+0.2*on/165,1.2)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=165:s=1080x1920:fps=30[zoomed];
    [zoomed]drawbox=x=0:y=1480:w=1080:h=440:color=$INK@0.75:t=fill[bg];
    [bg]drawtext=fontfile=$FONT_MONO:text='1. e4':fontsize=56:fontcolor=$WHITE:x=120:y=1540:enable='gte(t,0)',
    drawtext=fontfile=$FONT_MONO:text='2. Bc4':fontsize=56:fontcolor=$WHITE:x=120:y=1630:enable='gte(t,1.5)',
    drawtext=fontfile=$FONT_MONO:text='3. Qh5':fontsize=56:fontcolor=$INDIGO:x=120:y=1720:enable='gte(t,3.0)',
    drawtext=fontfile=$FONT_BOLD:text='aiming at f7':fontsize=40:fontcolor=$MUTED:x=480:y=1720:enable='gte(t,3.5)',
    fade=in:st=0:d=0.3,fade=out:st=5.0:d=0.5
  " -t 5.5 -r 30 -pix_fmt yuv420p "$TMP/scene2.mp4"
echo "  scene2.mp4 done"

echo "=== building scene 3: checkmate reveal (10-15s) ==="
ffmpeg -y -v error -loop 1 -t 5.0 -i "$IMG3" \
  -filter_complex "
    [0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,
    zoompan=z='min(1+0.3*on/150,1.3)':d=150:s=1080x1920:fps=30[zoomed];
    [zoomed]drawbox=x=0:y=0:w=1080:h=1920:color=$INK@0.45:t=fill[bg];
    [bg]drawtext=fontfile=$FONT_BOLD:text='CHECKMATE':fontsize=120:fontcolor=$WHITE:x=(w-text_w)/2:y=720:enable='gte(t,0.3)',
    drawtext=fontfile=$FONT_BOLD:text='in just 4 moves':fontsize=52:fontcolor=$INDIGO:x=(w-text_w)/2:y=880:enable='gte(t,1.2)',
    drawtext=fontfile=$FONT_REG:text='Game over.':fontsize=36:fontcolor=$MUTED:x=(w-text_w)/2:y=1000:enable='gte(t,2.5)',
    fade=in:st=0:d=0.3,fade=out:st=4.5:d=0.5
  " -t 5.0 -r 30 -pix_fmt yuv420p "$TMP/scene3.mp4"
echo "  scene3.mp4 done"

echo "=== concatenating scenes ==="
printf "file '$TMP/scene1.mp4'\nfile '$TMP/scene2.mp4'\nfile '$TMP/scene3.mp4'\n" > "$TMP/concat.txt"
ffmpeg -y -v error -f concat -safe 0 -i "$TMP/concat.txt" -c copy "$TMP/video-silent.mp4"
echo "  concatenated -> $(du -h $TMP/video-silent.mp4 | cut -f1)"

echo "=== mixing voice (15s) + background music ==="
ffmpeg -y -v error \
  -i "$TMP/video-silent.mp4" \
  -ss 0 -t 15 -i "$VOICE" \
  -ss 0 -t 15 -i "$MUSIC" \
  -filter_complex "
    [1:a]volume=1.5[voice];
    [2:a]volume=0.15,afade=in:0:30,afade=out:st=14:d=1[bgm];
    [voice][bgm]amix=inputs=2:duration=shortest:dropout_transition=0[aout]
  " \
  -map 0:v -map "[aout]" -c:v copy -c:a aac -b:a 192k -shortest "$OUT"

echo "=== done ==="
ffprobe -v error -show_entries format=duration,size -show_entries stream=width,height,codec_name -of default=noprint_wrappers=1 "$OUT"
echo "output: $OUT ($(du -h "$OUT" | cut -f1))"
