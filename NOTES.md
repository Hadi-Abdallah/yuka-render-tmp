# Room clip: working files
Goal: 27 s, 648 frames, 24 fps, 1080x1920, must look 100% filmed: laptop + phone in a blue/violet room. No audio.
## Setup on Linux
1. Blender 5.3 (linux x64) from download.blender.org, verify the sha256. ffmpeg. pip install opencv-python-headless numpy.
2. `python setup.py` (unpacks webp textures to png, recordings to cap24/).
3. `python dl.py "" american_walnut_veneer,smoked_walnut_veneer,black_oak_veneer,dark_wood` (Poly Haven CC0, creates assets-polyhaven/tex).
4. Test: `LEFT=none MUGV=2 PCT=45 SPP=16 OUT=t/ blender -b -P room2.py -- 10,440` then `python post2.py t t.png`.
Env: LEFT=none, MUGV=1..4, PCT, SPP, BORDER=x0,x1,y0,y1 (crop render), SAVE=1 (writes pk/room.blend, packed).
render.yml.txt is the 20-job GitHub Actions render (put it at .github/workflows/render.yml on a branch called mix-video together with pk/room.blend, render.py, seg.py, post2.py, tone.py, phone.mp4, laptop.mp4). It has not run yet. Ask the owner before starting it, and remind them to make the repo private when it finishes.
## Open items
1. Used-mug option: owner chooses. 1 light smudges, 2 smudges + fine scratches + worn lip (recommended), 3 adds dried drip + desk ring, 4 most worn.
2. Palm and finger marks: checked, good.
3. Webcam strip: checked, made fully dark.
4. SAVE=1, start the render, deliver.
Approved, do not change: books, no plant, trackpad position, mug size, coffee traces, warm shelf light, camera move.
Send progress images often; keep usage economical.
