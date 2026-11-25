import numpy as np,cv2
from scipy.ndimage import gaussian_filter as gf, gaussian_filter1d as g1, rotate, map_coordinates
rng=np.random.default_rng(23)
def noise(h,w,s,seed,o=4,ax=(1,1)):
    r=np.random.default_rng(seed);a=np.zeros((h,w),'f4');amp=1
    for k in range(o):
        n=r.random((max(2,int(h/(s*ax[0])*2**k)+2),max(2,int(w/(s*ax[1])*2**k)+2))).astype('f4');a+=amp*cv2.resize(n,(w,h),interpolation=cv2.INTER_CUBIC);amp*=.5
    a-=a.min();return a/a.max()
def print_(px,seed,smear=0,ang=0,press=1.0,wd=13,ht=18):
    """one fingertip: ridge flow with a core, uneven pressure, optional drag. px per mm"""
    r=np.random.default_rng(seed);h=int((ht+10)*px);w=int((wd+10)*px);yy,xx=np.mgrid[0:h,0:w].astype('f4');x=(xx-w/2)/px;y=(yy-h/2)/px
    wx=(noise(h,w,7*px,seed+1)-.5)*3.2;wy=(noise(h,w,7*px,seed+2)-.5)*3.2;X=x+wx;Y=y+wy+1.5
    th=np.arctan2(Y,X);rad=np.hypot(X*1.15,Y*.82);loop=np.where(Y>0,np.hypot(X*1.15,Y*.55),rad);ph=loop/.46*2*np.pi+.8*np.sin(th*2+r.random()*6)
    rd=np.clip(np.cos(ph)*.9+.35,0,1);rd*=np.clip((noise(h,w,.9*px,seed+3,2)-.22)*2.2,0,1)
    m=np.clip(1.25-np.hypot(x/(wd/2),y/(ht/2))**3.2*1.1,0,1);m*=np.clip((noise(h,w,6*px,seed+4)-.18)*1.7,0,1)
    g=(rd*.85+.15)*m*press
    if smear:
        L=int(abs(smear)*px);k=np.linspace(1,.15,L);k/=k.sum();g=cv2.filter2D(g,-1,k[None].astype('f4') if smear>0 else k[:,None].astype('f4'))*1.5
    return rotate(g,ang,reshape=True,order=1).clip(0,1)
def stamp(A,g,cx,cy,s=1.):
    h,w=g.shape;x0,y0=int(cx-w/2),int(cy-h/2);X0,Y0=max(0,x0),max(0,y0);X1,Y1=min(A.shape[1],x0+w),min(A.shape[0],y0+h)
    if X1>X0 and Y1>Y0: A[Y0:Y1,X0:X1]=np.maximum(A[Y0:Y1,X0:X1],g[Y0-y0:Y1-y0,X0-x0:X1-x0]*s)
# ---------------- laptop deck, 8 px/mm, x -179..179 mm, y back(top) +118 .. front -118
P=8;W,H=358*P,236*P;A=np.zeros((H,W),'f4');U=lambda mm:(mm+179)*P;V=lambda mm:(118-mm)*P
yy,xx=np.mgrid[0:H,0:W].astype('f4');xm=xx/P-179;ym=118-yy/P
fine=noise(H,W,1.1*P,5,3);mid=noise(H,W,9*P,6);big=noise(H,W,45*P,7)
def palm(cx,cy,a,rx,ry,s,seed):
    global A
    c,q=np.cos(np.radians(a)),np.sin(np.radians(a));u=(xm-cx)*c+(ym-cy)*q;v=-(xm-cx)*q+(ym-cy)*c
    e=np.clip(1.35-np.hypot(u/rx,v/ry)**2.2,0,1);st=noise(H,W,3.2*P,seed,4,(1,5));p=np.clip((noise(H,W,13*P,seed+1)-.30)*1.9,0,1)
    A=np.maximum(A,e*p*(.45+.55*st)*(.5+.7*fine)*s)
# heels of both hands, the side of the thumb, and the drag marks they leave
palm(-104,-86,-18,30,17,.85,31);palm(-78,-70,-35,17,10,.55,33);palm(-128,-72,-60,13,22,.40,35);palm(60,-86,20,32,17,.85,37);palm(34,-72,34,16,9,.55,39);palm(86,-70,60,12,22,.42,41);palm(-96,-104,-4,36,8,.45,43);palm(66,-104,4,38,8,.45,45)
for k in range(9):
    cx,cy=(rng.normal(-98,20),rng.normal(-84,10)) if k%2 else (rng.normal(62,20),rng.normal(-84,10));palm(cx,cy,rng.normal(0,30),rng.uniform(16,34),rng.uniform(1.6,3.6),rng.uniform(.22,.42),60+k*3)
# trackpad: swipes and taps
for k in range(16):
    cx,cy=rng.normal(-42,17),rng.normal(-70,10);palm(cx,cy,rng.choice([rng.normal(82,14),rng.normal(5,16)]),rng.uniform(10,24),rng.uniform(3,5.2),rng.uniform(.30,.62),120+k*3)
for k,(cx,cy,a,s,sm) in enumerate([(-36,-66,8,.95,0),(-52,-74,-12,.85,0),(-24,-76,16,.7,5),(-60,-62,-22,.6,0),(-44,-93,4,.75,0),(-18,-92,12,.6,4),(-120,-98,35,.8,0),(-112,-90,28,.55,3),(84,-100,-30,.8,0),(98,-92,-38,.6,0),(20,-60,12,.5,0),(6,-112,2,.8,0),(-8,-110,-6,.6,0),(118,-60,-15,.5,6),(-146,-58,20,.5,0),(-150,-20,40,.4,0),(140,-84,-25,.55,0)]):
    stamp(A,print_(P,300+k,sm,a,1,rng.uniform(11,14),rng.uniform(15,19)),U(cx),V(cy),s)
# faint polish over the whole palm rest from daily use, and one careless wipe
A=np.maximum(A,np.clip((-ym-28)/30,0,1)*(.10+.16*big*mid))
A=gf(A.clip(0,1),.6);cv2.imwrite('sh/deck.png',(A*255).astype('u1'));cv2.imwrite('sh/deck_v.png',cv2.resize((A*255).astype('u1')[int(H*.45):],(1790,int(1790*H*.55/W))))
# ---------------- mug outside: R grease, G scratches, B dried coffee; x=angle, y=height, 16 px/mm, camera faces u=.761
PX=16;W=3768;H=1488;G=np.zeros((H,W),'f4');Sc=np.zeros((H,W),'f4');Co=np.zeros((H,W),'f4');cu=.761*W;mmx=lambda d:int(cu+d*PX);mmy=lambda z:int((93-z)*PX)
for k,(dx,z,a,s,sm) in enumerate([(-17,30,70,.9,0),(-14,47,62,.8,0),(-12,64,55,.65,0),(19,74,-30,.7,0),(26,58,-40,.55,6),(8,82,10,.6,0),(-4,16,20,.45,0),(31,40,-20,.6,0),(-30,72,40,.7,0),(14,24,-12,.4,5),(38,66,-30,.5,0)]): stamp(G,print_(PX,500+k,sm,a,1,rng.uniform(12,15),rng.uniform(16,21)),mmx(dx),mmy(z),s)
b1=noise(H,W,14*PX,71);b2=noise(H,W,2.2*PX,72,4,(1,4));G=np.maximum(G,np.clip((b1-.50)*2.4,0,1)*(.25+.45*b2)*.55)
yy,xx=np.mgrid[0:H,0:W].astype('f4');z=93-yy/PX;G=np.maximum(G,np.clip(1-np.abs(z-87)/5,0,1)*(.2+.5*b2)*.5)
for k in range(260):
    x=rng.random()*W;zz=rng.choice([abs(rng.normal())*7+2,rng.uniform(5,85)],p=[.6,.4]);L=min(6.5,rng.exponential(2.6)+.6);a=rng.normal(0,.5) if rng.random()<.6 else rng.uniform(0,3.14);n=int(L*PX);t=np.linspace(0,1,n);xs=(x+np.cos(a)*t*n+np.sin(t*3)*2).astype(int)%W;ys=np.clip((93-zz)*PX-np.sin(a)*t*n,0,H-1).astype(int);Sc[ys,xs]=np.maximum(Sc[ys,xs],rng.uniform(.25,.9)*np.sin(np.pi*t)**.5)
Sc=gf(Sc,.8)*1.6
# two dried runs from the lip, where somebody drinks, and the print of the lips
for k,(dx,ln,wd,s) in enumerate([(20.5,21,1.15,.85),(24.2,8.5,.8,.6)]):
    ys=np.arange(0,int(ln*PX));t=ys/len(ys);x=mmx(dx)+np.cumsum(g1(np.random.default_rng(800+k).normal(size=len(ys)),26))*1.1;bw=wd*(.62+.30*t+.10*np.sin(t*7))
    for j,yv in enumerate(ys):
        xs=np.arange(int(x[j]-40),int(x[j]+41));d=np.abs(xs-x[j])/PX;Co[yv,xs]=np.maximum(Co[yv,xs],s*(.34*(d<bw[j])*(.5+.5*t[j])+.62*np.exp(-((d-bw[j])/.10)**2)))
    R=wd*1.15;dd=np.hypot((yy-ys[-1])/PX*.8,(xx-x[-1])/PX);Co=np.maximum(Co,s*(.55*(dd<R)+.8*np.exp(-((dd-R)/.11)**2)))
Co=np.maximum(Co,np.clip(1-yy/PX/3.2,0,1)*np.clip(1-np.abs(xx-mmx(21))/PX/11,0,1)*np.clip((b2-.25)*1.6,0,1)*.6);Co=gf(Co,.9)
cv2.imwrite('sh/mugw.png',np.stack([Co,Sc.clip(0,1),G],-1).clip(0,1)*255)
# coffee ring on the desk, 20 px/mm, 100 mm square
N=2000;yy,xx=np.mgrid[0:N,0:N].astype('f4');r=np.hypot(xx-N/2,yy-N/2)/20;t=np.arctan2(yy-N/2,xx-N/2);k1=noise(N,N,160,81);k2=noise(N,N,26,82);R0=31.6;gap=np.clip(np.cos(t-.6)*1.3+.45+(k1-.5)*2.2,0,1);ring=(np.exp(-((r-R0-.75+.25*(k2-.5))/.22)**2)+.45*np.exp(-((r-R0+.7+.5*(k2-.5))/.34)**2)+.20*np.exp(-((r-R0)/.8)**4))*gap*(.45+.8*k2);cv2.imwrite('sh/ring.png',(gf(ring,1).clip(0,1)*255).astype('u1'))
