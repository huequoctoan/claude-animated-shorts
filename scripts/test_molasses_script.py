import asyncio
import edge_tts
import subprocess

SCRIPT = [
    ('Hook', "In 1919, a twenty-five-foot wave of molasses blasted through Boston at thirty-five miles per hour.", '+18%'),
    ('Setting', "It was stored in a fifty-foot steel tank in Boston's North End.", '+15%'),
    ('Leak', "The tank leaked for months, so locals collected free syrup in buckets.", '+15%'),
    ('Paint', "Instead of fixing it, the company painted the tank brown to hide cracks.", '+15%'),
    ('Heat', "Then a winter heatwave jumped forty degrees in one day.", '+15%'),
    ('Rivets', "Fermenting syrup built pressure, and rivets popped like gunfire.", '+15%'),
    ('Burst', "The steel hull burst open, unleashing two million gallons of sludge.", '+15%'),
    ('Crush', "The wave flattened buildings, crushed wagons, and derailed a train.", '+15%'),
    ('Luckily', "Luckily, it was only syrup.", '+15%'),
    ('Unluckily', "Unluckily, freezing winter air turned it into suffocating quicksand.", '+15%'),
    ('Pivot', "You see, molasses is a non-Newtonian fluid that thickens under stress.", '+15%'),
    ('Mechanism', "Struggling to escape only makes the sticky syrup grip tighter.", '+15%'),
    ('Consequence', "The disaster forced America to create mandatory engineering safety laws.", '+15%'),
    ('Cleanup', "Saltwater crews took six months to scrub the cobblestones clean.", '+15%'),
    ('Twist', "Yet locals swear that on hot summer days, Boston still smells like pancakes.", '+18%')
]

async def check():
    tot = 0
    for name, text, rate in SCRIPT:
        c = edge_tts.Communicate(text, 'en-US-ChristopherNeural', rate=rate)
        p = f'/tmp/mola2_{name}.mp3'
        await c.save(p)
        dur = float(subprocess.check_output(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1', p]))
        words = len(text.split())
        wpm = words / dur * 60
        print(f'{name:12s}: {dur:4.2f}s ({words:2d} words, {wpm:3.0f} wpm, {rate})')
        tot += dur
    print(f'Total speech time: {tot:.2f}s (leaves {67.50 - tot:.2f}s for pauses across 67.5s)')

asyncio.run(check())
