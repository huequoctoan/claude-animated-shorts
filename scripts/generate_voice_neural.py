import asyncio
import os
import json
import subprocess
import wave
import numpy as np
import edge_tts

SR = 48000
TOTAL_DUR = 67.500
TOTAL_SAMPLES = int(TOTAL_DUR * SR)

VOICE = "en-US-ChristopherNeural"

# Carefully timed segments aligned with shots in story.ts
SEGMENTS = [
    {
        "id": 1,
        "name": "Hook",
        "t_start": 0.10,
        "t_limit": 4.15,
        "rate": "+15%",
        "text": "Seventy-four soldiers knocked down an iron bridge just by walking across it."
    },
    {
        "id": 2,
        "name": "Town",
        "t_start": 4.45,
        "t_limit": 9.20,
        "rate": "+10%",
        "text": "In 1831, the brand new bridge was the pride of the whole town."
    },
    {
        "id": 3,
        "name": "March",
        "t_start": 9.55,
        "t_limit": 14.60,
        "rate": "+10%",
        "text": "The men marched home four across, boots hitting the planks at the exact same moment."
    },
    {
        "id": 4,
        "name": "Bounce",
        "t_start": 14.90,
        "t_limit": 17.65,
        "rate": "+10%",
        "text": "Halfway over, the bridge started bouncing under their feet."
    },
    {
        "id": 5,
        "name": "Mock",
        "t_start": 17.80,
        "t_limit": 21.25,
        "rate": "+10%",
        "text": "A normal person would slow down, but these guys found it hilarious."
    },
    {
        "id": 6,
        "name": "Whistle",
        "t_start": 21.55,
        "t_limit": 27.20,
        "rate": "+10%",
        "text": "Someone whistled a marching tune, and the column stomped along, harder with every step."
    },
    {
        "id": 7,
        "name": "Groan",
        "t_start": 27.55,
        "t_limit": 32.70,
        "rate": "+10%",
        "text": "The bounce grew bigger, chains started groaning, and nobody wanted to break step."
    },
    {
        "id": 8,
        "name": "Snap",
        "t_start": 33.00,
        "t_limit": 37.60,
        "rate": "+10%",
        "text": "Then a single bolt snapped, and the entire bridge dropped into the river."
    },
    {
        "id": 9,
        "name": "Luckily",
        "t_start": 38.00,
        "t_limit": 40.25,
        "rate": "+10%",
        "text": "Luckily, the river was only two feet deep."
    },
    {
        "id": 10,
        "name": "Unluckily",
        "t_start": 40.50,
        "t_limit": 43.20,
        "rate": "+10%",
        "text": "Unluckily, the river was only two feet deep."
    },
    {
        "id": 11,
        "name": "Pivot",
        "t_start": 43.50,
        "t_limit": 46.90,
        "rate": "+10%",
        "text": "You see, every bridge has a rhythm it naturally likes to sway at."
    },
    {
        "id": 12,
        "name": "Swing",
        "t_start": 47.15,
        "t_limit": 53.80,
        "rate": "+12%",
        "text": "Ever pushed a kid on a swing? Tiny pushes, timed just right, make the swing go higher and higher."
    },
    {
        "id": 13,
        "name": "Pushing",
        "t_start": 54.10,
        "t_limit": 57.65,
        "rate": "+10%",
        "text": "Seventy-four men stepping together were pushing that bridge like a swing."
    },
    {
        "id": 14,
        "name": "Rule",
        "t_start": 57.95,
        "t_limit": 61.90,
        "rate": "+10%",
        "text": "Nobody died, but the army made a rule: never cross a bridge in step."
    },
    {
        "id": 15,
        "name": "Twist",
        "t_start": 62.20,
        "t_limit": 67.10,
        "rate": "+10%",
        "text": "Now, the best drilled soldiers in the world cross every bridge like a crowd of tourists."
    }
]

os.makedirs("/tmp/edge_tts_short", exist_ok=True)

async def generate():
    master_voice = np.zeros(TOTAL_SAMPLES, dtype=np.float32)
    all_words = []
    
    for i, seg in enumerate(SEGMENTS):
        text = seg["text"]
        rate = seg.get("rate", "+10%")
        mp3_path = f"/tmp/edge_tts_short/seg_{i}.mp3"
        wav_path = f"/tmp/edge_tts_short/seg_{i}.wav"
        
        comm = edge_tts.Communicate(text, VOICE, rate=rate)
        await comm.save(mp3_path)
        
        # Convert to 48kHz mono 16-bit WAV
        subprocess.run([
            "ffmpeg", "-y", "-i", mp3_path, "-ar", str(SR), "-ac", "1", wav_path
        ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        with wave.open(wav_path, "rb") as wf:
            n_frames = wf.getnframes()
            samples = np.frombuffer(wf.readframes(n_frames), dtype=np.int16).astype(np.float32) / 32768.0
            
        dur = len(samples) / SR
        t_start = seg["t_start"]
        t_limit = seg["t_limit"]
        
        # Ensure it fits within limit with gentle scaling if needed
        max_dur = t_limit - t_start
        if dur > max_dur:
            speed = dur / max_dur
            sped_wav = f"/tmp/edge_tts_short/seg_{i}_sped.wav"
            subprocess.run([
                "ffmpeg", "-y", "-i", wav_path, "-filter:a", f"atempo={speed:.4f}", "-ar", str(SR), sped_wav
            ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            with wave.open(sped_wav, "rb") as wf:
                samples = np.frombuffer(wf.readframes(wf.getnframes()), dtype=np.int16).astype(np.float32) / 32768.0
            dur = len(samples) / SR

        start_idx = int(t_start * SR)
        end_idx = min(TOTAL_SAMPLES, start_idx + len(samples))
        master_voice[start_idx:end_idx] = samples[:end_idx - start_idx]
        
        # Map word timings
        words = text.split()
        char_lens = [len(w) for w in words]
        total_chars = sum(char_lens)
        cur_t = t_start
        for w, clen in zip(words, char_lens):
            wdur = (clen / total_chars) * dur
            all_words.append({
                "w": w.strip(".,;:?!\"'"),
                "s": round(cur_t, 3),
                "e": round(cur_t + wdur * 0.9, 3)
            })
            cur_t += wdur

        print(f"[{seg['name']:10s}] t={t_start:5.2f}s - {t_start+dur:5.2f}s ({dur:4.2f}s) | {text}")

    # Export voice.wav (stereo 16-bit PCM)
    voice_int16 = (master_voice * 32767).clip(-32768, 32767).astype(np.int16)
    stereo = np.column_stack([voice_int16, voice_int16])

    for out_dir in ["voice", "templates/voice"]:
        os.makedirs(out_dir, exist_ok=True)
        wav_out = os.path.join(out_dir, "voice.wav")
        json_out = os.path.join(out_dir, "words.json")
        
        with wave.open(wav_out, "wb") as wf:
            wf.setnchannels(2)
            wf.setsampwidth(2)
            wf.setframerate(SR)
            wf.writeframes(stereo.tobytes())
            
        with open(json_out, "w", encoding="utf-8") as jf:
            json.dump(all_words, jf, indent=2)

    print(f"\nSUCCESS: Generated {TOTAL_DUR}s voice with {len(all_words)} words using {VOICE}")

if __name__ == "__main__":
    asyncio.run(generate())

