# unpack textures and screen recordings after cloning (pip install opencv-python-headless numpy; needs ffmpeg)
import cv2,glob,os,subprocess
for f in glob.glob('sh/*.webp')+glob.glob('bk/*.webp'): cv2.imwrite(f[:-4]+'png',cv2.imread(f,-1))
for d in('phone','laptop'):
    os.makedirs('cap24/'+d,exist_ok=True);subprocess.run(['ffmpeg','-v','error','-y','-i',d+'.mp4','-q:v','1','-qmin','1','-start_number','0','cap24/'+d+'/%04d.jpg'],check=True)
os.makedirs('pk',exist_ok=True)
