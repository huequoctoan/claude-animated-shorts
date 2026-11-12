import os
import json
import subprocess
import wave
import numpy as np

SR = 48000
TOTAL_DUR = 67.500
TOTAL_SAMPLES = int(TOTAL_DUR * SR)

# 15 segments with target start and end times in seconds
SCRIPT_SEGMENTS = [
    {
        "t_start": 0.15,
        "t_max": 4.10,
        "text": "Seventy-four soldiers knocked down an iron bridge just by walking across it.",
    },
    {
        "t_start": 4.45,
        "t_max": 9.20,
        "text": "It's 1831, and the brand new bridge over the river is the pride of the whole town.",
    },
    {
        "t_start": 9.55,
        "t_max": 14.60,
        "text": "The men are marching home four across, every boot hitting the planks at the exact same moment.",
    },
    {
        "t_start": 14.90,
        "t_max": 17.50,
        "text": "Halfway over, the bridge starts bouncing under their feet.",
    },
    {
        "t_start": 17.90,
        "t_max": 21.10,
        "text": "A normal person would slow down, but these guys think it's hilarious.",
    },
    {
        "t_start": 21.55,
        "t_max": 27.10,
        "text": "Somebody starts whistling a marching tune, and the whole column stomps along to it, a little harder every step.",
    },
    {
        "t_start": 27.55,
        "t_max": 32.60,
        "text": "The bounce gets bigger, the chains start groaning, and nobody wants to be the one who breaks step.",
    },
    {
        "t_start": 33.00,
        "t_max": 37.50,
        "text": "Then a single bolt snaps, and the whole end of the bridge drops into the river.",
    },
    {
        "t_start": 37.95,
        "t_max": 40.20,
        "text": "Luckily, the river was only two feet deep.",
    },
    {
        "t_start": 40.50,
        "t_max": 43.10,
        "text": "Unluckily, the river was only two feet deep.",
    },
    {
        "t_start": 43.55,
        "t_max": 46.80,
        "text": "You see, every bridge has a rhythm it naturally likes to sway at.",
    },
    {
        "t_start": 47.15,
        "t_max": 53.70,
        "text": "Ever pushed a kid on a swing? Each push is tiny, but if they all land at just the right moment, the swing goes higher and higher.",
    },
    {
        "t_start": 54.15,
        "t_max": 57.60,
        "text": "Seventy-four men stepping together were pushing that bridge like a swing.",
    },
    {
        "t_start": 57.95,
        "t_max": 61.90,
        "text": "Nobody died, but the army made a rule: never cross a bridge in step.",
    },
    {
        "t_start": 62.25,
        "t_max": 67.10,
        "text": "So now, the best drilled soldiers in the world cross every bridge like a crowd of tourists.",
    },
]

os.makedirs("/tmp/tts_short", exist_ok=True)
all_words = []
master_voice = np.zeros(TOTAL_SAMPLES, dtype=np.float32)

for i, seg in enumerate(SCRIPT_SEGMENTS):
    text = seg["text"]
    t0 = seg["t_start"]
    t_target = seg["t_max"] - t0
    
    words = text.split()
    # Estimate speech rate: words per second
    wps = len(words) / max(0.5, t_target * 0.9)
    # rate in say: ~170-200 wpm
    rate_wpm = int(max(150, min(230, wps * 60)))
    
    aiff_path = f"/tmp/tts_short/seg_{i}.aiff"
    wav_path = f"/tmp/tts_short/seg_{i}.wav"
    
    subprocess.run(["say", "-v", "Daniel", "-r", str(rate_wpm), text, "-o", aiff_path], check=True)
    subprocess.run(["ffmpeg", "-y", "-i", aiff_path, "-ar", str(SR), "-ac", "1", wav_path], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    # Read samples
    with wave.open(wav_path, "rb") as wf:
        n_samples = wf.getnframes()
        data = wf.readframes(n_samples)
        samples = np.frombuffer(data, dtype=np.int16).astype(np.float32) / 32768.0
        
    actual_dur = len(samples) / SR
    # If longer than target, speed up slightly with ffmpeg atempo
    if actual_dur > t_target:
        speed = actual_dur / (t_target - 0.05)
        sped_wav = f"/tmp/tts_short/seg_{i}_sped.wav"
        subprocess.run(["ffmpeg", "-y", "-i", wav_path, "-filter:a", f"atempo={speed:.3f}", "-ar", str(SR), sped_wav], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        with wave.open(sped_wav, "rb") as wf:
            n_samples = wf.getnframes()
            samples = np.frombuffer(wf.readframes(n_samples), dtype=np.int16).astype(np.float32) / 32768.0
        actual_dur = len(samples) / SR

    start_idx = int(t0 * SR)
    end_idx = min(TOTAL_SAMPLES, start_idx + len(samples))
    master_voice[start_idx:end_idx] = samples[:end_idx - start_idx]
    
    # Generate word timings proportional to word character lengths
    char_lens = [len(w) for w in words]
    total_chars = sum(char_lens)
    cur_t = t0
    for w, clen in zip(words, char_lens):
        wdur = (clen / total_chars) * actual_dur
        all_words.append({
            "w": w.strip(".,;:?!\"'"),
            "s": round(cur_t, 3),
            "e": round(cur_t + wdur * 0.9, 3)
        })
        cur_t += wdur

# Write output master_voice
os.makedirs("voice", exist_ok=True)
os.makedirs("templates/voice", exist_ok=True)

# Convert to 16-bit PCM WAV (stereo)
voice_int16 = (master_voice * 32767).clip(-32768, 32767).astype(np.int16)
stereo = np.column_stack([voice_int16, voice_int16])

for out_dir in ["voice", "templates/voice"]:
    wav_out = os.path.join(out_dir, "voice.wav")
    json_out = os.path.join(out_dir, "words.json")
    
    with wave.open(wav_out, "wb") as wf:
        wf.setnchannels(2)
        wf.setsampwidth(2)
        wf.setframerate(SR)
        wf.writeframes(stereo.tobytes())
        
    with open(json_out, "w", encoding="utf-8") as jf:
        json.dump(all_words, jf, indent=2)

print(f"Generated voice: {TOTAL_DUR} s ({TOTAL_SAMPLES} samples), {len(all_words)} words.")

