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
1. Used-mug option: owner chose 4 (most worn). Build with MUGV=4.
2. Palm and finger marks: checked, good.
3. Webcam strip: checked, made fully dark.
4. pk/room.blend built (LEFT=none MUGV=4 SAVE=1), test frames 10 and 324 from it via render.py look right (~100 s/frame on 4 cores). Next: owner says yes, then start the render and deliver.
Note: cropped EXRs (BORDER) read as black through ffmpeg; load them in Blender instead. Full frames are fine.
Approved, do not change: books, no plant, trackpad position, mug size, coffee traces, warm shelf light, camera move.
Send progress images often; keep usage economical.
