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

# Carefully timed segments for the Dancing Plague short (67.5s total)
SEGMENTS = [
    {
        "id": 1,
        "name": "Hook",
        "t_start": 0.10,
        "rate": "+18%",
        "text": "In 1518, a woman walked into the street and started dancing, and within a month 400 people couldn't stop."
    },
    {
        "id": 2,
        "name": "Town",
        "t_start": 6.75,
        "rate": "+15%",
        "text": "It was a scorching July in Strasbourg, and Frau Troffea wouldn't stop."
    },
    {
        "id": 3,
        "name": "March",
        "t_start": 11.40,
        "rate": "+15%",
        "text": "Her shoes soaked with blood, yet she kept twirling day and night."
    },
    {
        "id": 4,
        "name": "Bounce",
        "t_start": 15.65,
        "rate": "+16%",
        "text": "Within days, dozens joined in, leaping wildly across the cobblestones."
    },
    {
        "id": 5,
        "name": "Mock",
        "t_start": 20.70,
        "rate": "+15%",
        "text": "Local doctors diagnosed the craze as hot blood."
    },
    {
        "id": 6,
        "name": "Whistle",
        "t_start": 24.35,
        "rate": "+15%",
        "text": "So the city council hired a live band to dance it out."
    },
    {
        "id": 7,
        "name": "Groan",
        "t_start": 28.25,
        "rate": "+15%",
        "text": "They built a wooden stage, and people danced until their hearts gave out."
    },
    {
        "id": 8,
        "name": "Snap",
        "t_start": 32.90,
        "rate": "+15%",
        "text": "Dozens collapsed from exhaustion, but the manic music kept playing."
    },
    {
        "id": 9,
        "name": "Luckily",
        "t_start": 37.30,
        "rate": "+15%",
        "text": "Luckily, the church intervened."
    },
    {
        "id": 10,
        "name": "Unluckily",
        "t_start": 40.20,
        "rate": "+15%",
        "text": "Unluckily, they forced them to dance up to a mountain shrine."
    },
    {
        "id": 11,
        "name": "Pivot",
        "t_start": 44.25,
        "rate": "+15%",
        "text": "You see, Strasbourg was suffering through a devastating famine."
    },
    {
        "id": 12,
        "name": "Swing",
        "t_start": 48.55,
        "rate": "+16%",
        "text": "Starving locals ate rye bread contaminated with ergot fungus, a toxic mold closely related to LSD."
    },
    {
        "id": 13,
        "name": "Pushing",
        "t_start": 55.35,
        "rate": "+15%",
        "text": "Combined with panic, it triggered mass psychogenic hysteria."
    },
    {
        "id": 14,
        "name": "Rule",
        "t_start": 59.55,
        "rate": "+15%",
        "text": "Eventually the fever broke, and the survivors walked home."
    },
    {
        "id": 15,
        "name": "Twist",
        "t_start": 63.35,
        "rate": "+20%",
        "text": "Leaving history with the only epidemic cured with a live brass band."
    }
]

os.makedirs("/tmp/edge_tts_dp", exist_ok=True)

async def generate():
    master_voice = np.zeros(TOTAL_SAMPLES, dtype=np.float32)
    all_words = []
    
    for i, seg in enumerate(SEGMENTS):
        text = seg["text"]
        rate = seg.get("rate", "+15%")
        mp3_path = f"/tmp/edge_tts_dp/seg_{i}.mp3"
        wav_path = f"/tmp/edge_tts_dp/seg_{i}.wav"
        
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
        
        # Check if segment overflows past 67.5s
        if t_start + dur > TOTAL_DUR:
            print(f"WARNING: Segment {seg['name']} exceeds {TOTAL_DUR}s! Truncating or adjusting.")
            
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

        wpm = len(words) / dur * 60
        print(f"[{seg['name']:10s}] t={t_start:5.2f}s - {t_start+dur:5.2f}s ({dur:4.2f}s | {wpm:3.0f} WPM) | {text}")

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
