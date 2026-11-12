#!/bin/bash
set -e

export REMOTION_TMP="/Volumes/D/APP_AI/Short_auto/remotion-tmp"
export TEMP="/Volumes/D/APP_AI/Short_auto/remotion-tmp"
export TMP="/Volumes/D/APP_AI/Short_auto/remotion-tmp"

CHROME="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
RAW_MP4="out/molasses_raw.mp4"
FINAL_MP4="out/molasses_flood_2k.mp4"
AUDIO_WAV="templates/audio/mix.wav"

echo "=== STEP 1: Rendering 2K video via Remotion (1440x2560, 2025 frames) ==="
npx remotion render src/index.ts MolassesFlood "$RAW_MP4" \
  --codec h264 \
  --crf 16 \
  --width 1440 \
  --height 2560 \
  --browser-executable="$CHROME" \
  --concurrency 1 \
  --log=verbose

echo "=== STEP 2: Muxing 2K video with master audio mix ==="
ffmpeg -y -i "$RAW_MP4" -i "$AUDIO_WAV" \
  -c:v copy \
  -c:a aac -b:a 320k \
  -map 0:v:0 -map 1:a:0 \
  -shortest \
  "$FINAL_MP4"

echo "=== STEP 3: Verification & Media Info ==="
ffprobe -show_entries stream=width,height,codec_name,r_frame_rate,sample_rate,channels:format=duration,size -of default=noprint_wrappers=1 "$FINAL_MP4"

echo "SUCCESS: Final Molasses Flood 2K animated short exported to $FINAL_MP4"

