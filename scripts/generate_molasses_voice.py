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

SEGMENTS = [
    {
        "id": 1,
        "name": "Hook",
        "t_start": 0.10,
        "rate": "+18%",
        "text": "In 1919, a twenty-five-foot wave of molasses blasted through Boston at thirty-five miles per hour."
    },
    {
        "id": 2,
        "name": "Setting",
        "t_start": 6.65,
        "rate": "+15%",
        "text": "It was stored in a fifty-foot steel tank in Boston's North End."
    },
    {
        "id": 3,
        "name": "Leak",
        "t_start": 10.95,
        "rate": "+15%",
        "text": "The tank leaked for months, so locals collected free syrup in buckets."
    },
    {
        "id": 4,
        "name": "Paint",
        "t_start": 15.50,
        "rate": "+15%",
        "text": "Instead of fixing it, the company painted the tank brown to hide cracks."
    },
    {
        "id": 5,
        "name": "Heat",
        "t_start": 20.20,
        "rate": "+15%",
        "text": "Then a winter heatwave jumped forty degrees in one day."
    },
    {
        "id": 6,
        "name": "Rivets",
        "t_start": 24.00,
        "rate": "+15%",
        "text": "Fermenting syrup built pressure, and rivets popped like gunfire."
    },
    {
        "id": 7,
        "name": "Burst",
        "t_start": 28.30,
        "rate": "+15%",
        "text": "The steel hull burst open, unleashing two million gallons of sludge."
    },
    {
        "id": 8,
        "name": "Crush",
        "t_start": 33.00,
        "rate": "+15%",
        "text": "The wave flattened buildings, crushed wagons, and derailed a train."
    },
    {
        "id": 9,
        "name": "Luckily",
        "t_start": 37.65,
        "rate": "+15%",
        "text": "Luckily, it was only syrup."
    },
    {
        "id": 10,
        "name": "Unluckily",
        "t_start": 40.35,
        "rate": "+15%",
        "text": "Unluckily, freezing winter air turned it into suffocating quicksand."
    },
    {
        "id": 11,
        "name": "Pivot",
        "t_start": 44.95,
        "rate": "+15%",
        "text": "You see, molasses is a non-Newtonian fluid that thickens under stress."
    },
    {
        "id": 12,
        "name": "Mechanism",
        "t_start": 49.80,
        "rate": "+15%",
        "text": "Struggling to escape only makes the sticky syrup grip tighter."
    },
    {
        "id": 13,
        "name": "Consequence",
        "t_start": 53.70,
        "rate": "+15%",
        "text": "The disaster forced America to create mandatory engineering safety laws."
    },
    {
        "id": 14,
        "name": "Cleanup",
        "t_start": 58.60,
        "rate": "+15%",
        "text": "Saltwater crews took six months to scrub the cobblestones clean."
    },
    {
        "id": 15,
        "name": "Twist",
        "t_start": 62.90,
        "rate": "+18%",
        "text": "Even today, hot summer days in Boston still smell like pancakes."
    }
]

os.makedirs("/tmp/edge_tts_molasses", exist_ok=True)

async def generate():
    master_voice = np.zeros(TOTAL_SAMPLES, dtype=np.float32)
    all_words = []
    
    for i, seg in enumerate(SEGMENTS):
        text = seg["text"]
        rate = seg.get("rate", "+15%")
        mp3_path = f"/tmp/edge_tts_molasses/seg_{i}.mp3"
        wav_path = f"/tmp/edge_tts_molasses/seg_{i}.wav"
        
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
        
        if t_start + dur > TOTAL_DUR:
            print(f"WARNING: Segment {seg['name']} exceeds {TOTAL_DUR}s! ({t_start + dur:.2f}s)")
            
        start_idx = int(t_start * SR)
        end_idx = min(TOTAL_SAMPLES, start_idx + len(samples))
        master_voice[start_idx:end_idx] = samples[:end_idx - start_idx]
        
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

        wpm = len(words) / dur * 60
        print(f"[{seg['name']:12s}] t={t_start:5.2f}s - {t_start+dur:5.2f}s ({dur:4.2f}s | {wpm:3.0f} WPM) | {text}")

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

