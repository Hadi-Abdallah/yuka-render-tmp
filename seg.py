import sys, subprocess, cv2
from post2 import finish
cv2.setNumThreads(1); a, b, out = int(sys.argv[1]), int(sys.argv[2]), sys.argv[3]
p = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', '1080x1920', '-r', '24', '-i', '-', '-vf', 'scale=out_color_matrix=bt709:out_range=tv,format=yuv420p', '-c:v', 'libx264', '-preset', 'medium', '-crf', '11', '-colorspace', 'bt709', '-color_primaries', 'bt709', '-color_trc', 'bt709', out], stdin=subprocess.PIPE)
for i in range(a, b): p.stdin.write(finish('rend/%04d.exr' % i, i).tobytes())
p.stdin.close(); p.wait()
