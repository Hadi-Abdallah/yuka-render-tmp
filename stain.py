# dried coffee on the inner wall. x = angle (wraps), y = height from rim (0) to base. 16 px/mm
import numpy as np,cv2
from scipy.ndimage import gaussian_filter as gf, gaussian_filter1d as g1
rng=np.random.default_rng(11);PX=16;W=int(2*np.pi*37.5*PX);MM=93;H=MM*PX;W-=W%2
def nz(sx,sy,seed,o=4):
    r=np.random.default_rng(seed);a=np.zeros((H,W),'f4');amp=1
    for k in range(o):
        n=r.random((max(2,int(H/(sy*PX)*2**k)+2),max(3,int(W/(sx*PX)*2**k)))).astype('f4');n=np.hstack([n,n[:,:2]]);b=cv2.resize(n,(int(W*(n.shape[1])/(n.shape[1]-2)),H),interpolation=cv2.INTER_CUBIC)[:,:W];a+=amp*b;amp*=.5
    a-=a.min();return a/a.max()
y=np.arange(H)[:,None]/PX; z=MM-y            # mm above base
th=(np.arange(W)/W*2*np.pi)[None]
A=np.zeros((H,W),'f4')                         # optical amount of dried coffee
def line1(amp,per,seed): # periodic 1-D wobble
    r=np.random.default_rng(seed);f=np.zeros(W);
    for k in range(1,per): f+=r.normal()*np.cos(k*th[0]+r.random()*6.28)/k**1.1
    return amp*f/np.abs(f).max()
# the mug was set down at these levels (mm), each one left a tide mark; the drinking side (th0) was swept to the lip
th0=np.pi*1.5
sweep=np.clip(np.cos(th[0]-th0),0,1)**3
lv=[(82.6,1.05,1.5),(79.2,.30,.9),(75.4,.20,.7)]
n1=nz(6,3,1);n2=nz(1.2,.9,2,3);n3=nz(22,9,3);n4=nz(.5,.5,9,2)
for k,(l,s,w) in enumerate(lv):
    L=l+line1(.34,9,20+k)+line1(.14,70,40+k)+.10*np.abs(line1(1,160,60+k))+sweep*(15-k*2.5)*(.8+.2*np.cos(5*th[0]));d=L[None]-z   # d>0 below the mark
    patch=np.clip((gf(rng.random((1,W)),(0,60),mode='wrap')-.5)*(9 if k==0 else 16)+(.72 if k==0 else .12),.16 if k==0 else 0,1)          # the mark is broken, stronger here, gone there
    edge=np.exp(-(d/(.13+.10*n2))**2)*(.80 if k==0 else .45)+np.exp(-np.clip(d,0,None)/(.9*w))*(d>0)*(.62 if k==0 else .5)         # sharp on top, bleeding down
    A+=s*edge*patch*(.55+.75*n2)
# the film that drained between the old surface and the coffee now
L0=lv[0][0]+line1(.34,9,20)+line1(.14,70,40)+.10*np.abs(line1(1,160,60))+sweep*15;below=np.clip((L0[None]-z)/.5,0,1)
A+=below*(.016+.040*n1**1.6+.026*n3)*(.75+.5*n2)*np.exp(-np.clip(L0[None]-z,0,40)/26)
# bare islands where the film pulled back (dewetting)
isl=np.clip((nz(4,2.6,5,3)-.58)*7,0,1);A*=1-.50*isl*below
# a few thin runs, different lengths, each one swelling into a bead
for k in range(9):
    x0=rng.random()*W;top=lv[0][0]+rng.normal()*.2-(.2 if k%3 else 2.6);ln=rng.choice([1.4,2.2,3.5,5.5,9.0,13]);wd=rng.uniform(.14,.36);st=rng.uniform(.10,.30)
    yy=np.arange(int((MM-top)*PX),min(H,int((MM-top+ln)*PX)));t=(yy-yy[0])/max(1,len(yy));x=x0+np.cumsum(g1(rng.normal(size=len(yy)),14))*1.1;bw=wd*(.75+.25*np.sin(t*9+k))*(1-.45*t)
    for j,yv in enumerate(yy):
        xs=np.arange(int(x[j]-14),int(x[j]+15));d=(xs-x[j])/PX;h=np.exp(-(d/bw[j])**4);e=np.exp(-((np.abs(d)-bw[j])/.05)**2);A[yv,xs%W]+=st*(.60*h+.30*e)*(.6+.4*t[j])
    cy,cx=yy[-1]/PX,x[-1];R=wd*rng.uniform(1.0,1.35);ys=np.arange(int((cy-1.2)*PX),min(H,int((cy+1.2)*PX)));xs=np.arange(int(cx-20),int(cx+21));dd=np.hypot((ys[:,None]/PX-cy)*.8,(xs[None]-cx)/PX);A[np.ix_(ys,xs%W)]+=st*(.75*np.exp(-(dd/R)**4)+.45*np.exp(-((dd-R)/.07)**2))
# rings left by bubbles that sat against the wall, in little rafts
for c in range(5):
    cx0=rng.random()*W;n=rng.integers(5,16);base=lv[0][0]-rng.exponential(.5)-(0 if c<5 else 4.5)
    for q in range(n):
        R=rng.uniform(.12,.48);cx=cx0+rng.normal()*2.6*PX;cyz=base-rng.random()*1.1-R*.6;cy=MM-cyz;ys=np.arange(int((cy-1)*PX),int((cy+1)*PX));xs=np.arange(int(cx-16),int(cx+17));dd=np.hypot(ys[:,None]/PX-cy,(xs[None]-cx)/PX);A[np.ix_(ys,xs%W)]+=rng.uniform(.06,.20)*np.exp(-((dd-R)/.035)**2)
# splashes above the mark
for q in range(13):
    cx=rng.random()*W;cyz=lv[0][0]+abs(rng.normal())*2.6+.4;R=rng.uniform(.05,.15);cy=MM-cyz
    if cyz>91: continue
    ys=np.arange(int((cy-.6)*PX),int((cy+.6)*PX));xs=np.arange(int(cx-10),int(cx+11));dd=np.hypot((ys[:,None]/PX-cy)*.85,(xs[None]-cx)/PX);A[np.ix_(ys,xs%W)]+=.22*(dd<R)+.5*np.exp(-((dd-R)/.04)**2)*(dd<R+.1)
# lips on the rim
A+=np.clip(1-y/2.6,0,1)*np.clip(np.cos(th-th0)-.86,0,1)*5*(.3+.9*n2)*.45
A*=(.82+.36*n4);A=gf(np.clip(A,0,None),.7,mode=('nearest','wrap'))
a=1-np.exp(-A*1.5);cv2.imwrite('sh/stain.png',(np.clip(a,0,1)*255).astype('u1'))
# preview on white
c=np.stack([.52*np.exp(-A*k) for k in (.75,1.75,3.6)],-1)/.52;v=(np.clip(c,0,1)**(1/2.2)*.95*255).astype('u1')[...,::-1]
cv2.imwrite('sh/stain_v.png',cv2.resize(v[:38*PX,:W//2],(1800,int(1800*38*PX/(W//2)))));print(W,H)
