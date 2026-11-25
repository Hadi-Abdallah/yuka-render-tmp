import subprocess,numpy as np,cv2,sys,glob,os
def exr(p):
    pr=subprocess.run(['ffprobe','-v','error','-show_entries','stream=width,height','-of','csv=p=0',p],capture_output=True,text=True).stdout.strip().split(',')
    w,h=int(pr[0]),int(pr[1]);r=subprocess.run(['ffmpeg','-v','error','-i',p,'-f','rawvideo','-pix_fmt','gbrpf32le','-'],capture_output=True).stdout
    g=np.frombuffer(r,'f4').reshape(3,h,w);return np.stack([g[2],g[0],g[1]],-1).clip(0,None)
def tone(im):
    im=np.where(im>.7,.7+.3*np.tanh((im-.7)/.3),im);return np.where(im<.0031308,im*12.92,1.055*np.power(np.clip(im,1e-8,None),1/2.4)-.055)
if __name__=='__main__':
    fs=sorted(glob.glob(sys.argv[1]+'/*.exr'));cv2.imwrite(sys.argv[2],np.hstack([(np.clip(tone(exr(f)),0,1)*255).astype(np.uint8)[...,::-1] for f in fs]))
