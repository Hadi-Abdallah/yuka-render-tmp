# scene-linear -> looks like it came out of a camera
import numpy as np,cv2,sys,glob,os
from tone import exr
rng=np.random.default_rng(3);GR=None
def post(im,i=0):
    global GR
    H,W=im.shape[:2];k=W/1080
    if GR is None or GR[0].shape[:2]!=(H,W):
        GR=[np.stack([cv2.GaussianBlur(rng.normal(0,1,(H,W)).astype('f4'),(0,0),.8*k) for _ in range(3)],-1) for _ in range(4)]
    im=im.astype('f4')*1.10
    q=cv2.resize(np.minimum(im,6),(W//4,H//4),interpolation=cv2.INTER_AREA);hi=np.clip(q-.55,0,None)
    bl=cv2.GaussianBlur(hi,(0,0),4*k)*.5+cv2.GaussianBlur(hi,(0,0),16*k)*.35+cv2.GaussianBlur(hi,(0,0),48*k)*.15;bl=cv2.resize(bl,(W,H),interpolation=cv2.INTER_CUBIC)
    im=im+bl*np.array([.10,.085,.11],'f4')
    veil=cv2.resize(cv2.GaussianBlur(q,(0,0),90*k),(W,H));im=im+veil*.012
    yy,xx=np.mgrid[0:H,0:W].astype('f4');u=(xx/W-.5);v=(yy/H-.5)*H/W;r2=u*u+v*v;im=im*(1-.22*np.clip(r2,0,1.2))[...,None]
    # tiny barrel distortion + lateral colour
    out=[]
    for c,s in enumerate((1.0007,1.0,.9993)):
        f=(1+.012*r2)*s/1.006;out.append(cv2.remap(im[...,c],((u*f+.5)*W).astype('f4'),((v*f*W/H+.5)*H).astype('f4'),cv2.INTER_CUBIC,borderMode=cv2.BORDER_REPLICATE))
    im=np.stack(out,-1).clip(0)
    L=im@np.array([.2126,.7152,.0722],'f4');im=L[...,None]+(im-L[...,None])*1.07
    x=im;sh=np.where(x>.55,.55+.45*(1-np.exp(-(x-.55)/.45*.92)),x)
    o=np.where(sh<.0031308,sh*12.92,1.055*np.power(np.clip(sh,1e-8,None),1/2.4)-.055)
    o=.007+o*.985
    g=GR[i%4];g=g[::-1] if i%8>3 else g;g=g[:,::-1] if i%16>7 else g;lum=o.mean(-1,keepdims=True);mono=g.mean(-1,keepdims=True)*1.5
    o=o+(mono*.0105+g*.0055)*(1.15-.85*np.clip(lum,0,1))
    return (np.clip(o,0,1)*255+.5).astype('u1')
def finish(p,i=0):
    im=exr(p)
    H,W=im.shape[:2]
    if W>1080:
        # supersampled frame: resolve in log so lit text stays crisp
        l=np.log1p(im*6);l=cv2.resize(l,(1080,round(H*1080/W)),interpolation=cv2.INTER_AREA);l=l+(l-cv2.GaussianBlur(l,(0,0),.8))*.35;im=np.expm1(l.clip(0))/6
    return post(im,i)
if __name__=='__main__':
    fs=sorted(glob.glob(sys.argv[1]+'/*.exr'));cv2.imwrite(sys.argv[2],np.hstack([finish(f,k)[...,::-1] for k,f in enumerate(fs)]))
