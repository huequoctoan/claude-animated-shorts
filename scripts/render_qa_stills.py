import os
import subprocess
import json

FRAMES = [60, 350, 700, 1050, 1250, 1500, 1900]
os.makedirs("out/qa_stills", exist_ok=True)

chrome = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

for f in FRAMES:
    clip_path = f"out/qa_stills/clip_{f}.mp4"
    out_jpg = f"out/qa_stills/frame_{f:04d}.jpg"
    print(f"Rendering frame {f}...")
    cmd = [
        "npx", "remotion", "render", "src/index.ts", "BridgeShort", clip_path,
        f"--frames={f}-{f+2}",
        f"--browser-executable={chrome}",
        "--scale=0.5",
        "--quiet"
    ]
    subprocess.run(cmd, check=True)
    # Extract the exact frame
    subprocess.run([
        "ffmpeg", "-y", "-i", clip_path, "-vf", "select=eq(n\\,0)", "-vframes", "1", out_jpg
    ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    os.remove(clip_path)
    print(f"Saved: {out_jpg}")

print("All QA frames generated successfully!")

