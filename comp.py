import json, sys, subprocess, numpy as np, cv2, os, glob
cv2.setNumThreads(2)
S = os.path.dirname(os.path.abspath(__file__))+'/'
C = json.load(open(S+'cams.json')); cams = [np.array(c) for c in C['cams']]
WW, HH = 1080, 1920
FPX = C['lens']/36*HH
lid = np.array(C['lid']); SW, SH, by, W, D, H, LH = [C[k] for k in ('SW', 'SH', 'by', 'W', 'D', 'H', 'LH')]
lo = lid[:3, 3]; lx, ly, lz = lid[:3, 0], lid[:3, 1], lid[:3, 2]
yy, xx = np.mgrid[0:HH, 0:WW].astype(np.float32)
K2 = json.load(open(S+'cams.json')) if 0 else None

def project(M, P):
    R, o = M[:3, :3], M[:3, 3]
    q = (P-o.astype(np.float32)) @ R.astype(np.float32)
    z = np.maximum(-q[..., 2], 1e-3)
    return np.stack([WW/2+FPX*q[..., 0]/z-.5, HH/2-FPX*q[..., 1]/z-.5], -1), z

def raycast(M):
    """analytic depth of lid front, base deck/front/sides, desk, wall -> point, id"""
    R, o = M[:3, :3], M[:3, 3].astype(np.float32)
    d = np.stack([(xx+.5-WW/2)/FPX, -(yy+.5-HH/2)/FPX, -np.ones_like(xx)], -1) @ R.T.astype(np.float32)
    t = np.full((HH, WW), 1e9, np.float32); ID = np.zeros((HH, WW), np.uint8)
    def hit(po, n, test, i):
        nonlocal t, ID
        n = np.asarray(n, np.float32); den = d @ n; den = np.where(abs(den) < 1e-6, 1e-6, den)
        tt = float((np.asarray(po, np.float32)-o) @ n)/den
        P = o+d*tt[..., None]; ok = (tt > 0) & (tt < t) & test(P); t = np.where(ok, tt, t); ID = np.where(ok, i, ID)
    def lt(P):
        a = (P-lo.astype(np.float32)); x = a @ lx.astype(np.float32); y = a @ ly.astype(np.float32); return (abs(x) < W/2) & (y > 0) & (y < LH)
    hit(lo+lz*.0125, lz, lt, 1)
    hit((0, 0, .005), (0, 0, 1), lambda P: (abs(P[..., 0]) < W/2) & (abs(P[..., 1]) < D/2), 2)
    hit((0, -D/2, 0), (0, -1, 0), lambda P: (abs(P[..., 0]) < W/2) & (P[..., 2] < .005) & (P[..., 2] > -H), 3)
    for s in (1, -1): hit((s*W/2, 0, 0), (s, 0, 0), lambda P: (abs(P[..., 1]) < D/2) & (P[..., 2] < .005) & (P[..., 2] > -H), 4)
    hit((0, 0, -H-.03), (0, 0, 1), lambda P: (abs(P[..., 0]) < 7) & (P[..., 1] < 4.7) & (P[..., 1] > -2.3), 5)
    hit((0, 9.45, 0), (0, -1, 0), lambda P: P[..., 0] < 1e8, 6)
    t = np.minimum(t, 60)
    return o+d*t[..., None], ID

def exr(p):
    r = subprocess.run(['ffmpeg', '-v', 'error', '-i', p, '-f', 'rawvideo', '-pix_fmt', 'gbrpf32le', '-'], capture_output=True).stdout
    g = np.frombuffer(r, 'f4').reshape(3, HH, WW); return np.ascontiguousarray(np.stack([g[2], g[0], g[1]], -1)[..., ::1]).clip(0, None)  # R,G,B
keys = sorted(int(os.path.basename(f)[:4]) for f in glob.glob(S+'rend/????.exr'))
cache = {}
def key(i):
    if i not in cache:
        if len(cache) > 3: cache.pop(min(cache))
        im = exr(S+'rend/%04d.exr' % i); _, ID = raycast(cams[i]); cache[i] = (im, ID.astype(np.float32))
    return cache[i]
def warp(i, P, ID):
    im, kid = key(i); uv, _ = project(cams[i], P); u, v = uv[..., 0].astype(np.float32), uv[..., 1].astype(np.float32)
    o = cv2.remap(np.log1p(im*4), u, v, cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE); o = np.expm1(o)/4
    inside = ((u > -1) & (u < WW) & (v > -1) & (v < HH)).astype(np.float32)
    same = (abs(cv2.remap(kid, u, v, cv2.INTER_NEAREST, borderMode=cv2.BORDER_REPLICATE)-ID) < .5).astype(np.float32)
    w = inside*(.02+.98*same)+.001
    return o.clip(0, None), cv2.GaussianBlur(w, (0, 0), 2.5)

def s2l(x): return np.where(x < .04045, x/12.92, ((x+.055)/1.055)**2.4).astype(np.float32)
QX = np.array([[-SW/2, by+SH], [SW/2, by+SH], [SW/2, by], [-SW/2, by]])
rng = np.random.default_rng(7)
grain = [cv2.GaussianBlur(rng.normal(0, 1, (HH, WW)).astype(np.float32), (0, 0), .75) for _ in range(12)]
vy = ((xx/WW-.5)**2*.55+(yy/HH-.5)**2*.9); vig = 1-.40*vy
def frame(i):
    a = max(k for k in keys if k <= i); b = min([k for k in keys if k >= i] or [a]); P, ID = raycast(cams[i])
    A, wa = warp(a, P, ID)
    if b != a:
        B, wb = warp(b, P, ID); f = (i-a)/(b-a); wa = wa*(1-f)+1e-5; wb = wb*f+1e-5; im = (A*wa[..., None]+B*wb[..., None])/(wa+wb)[..., None]
    else: im = A
    # ---- crisp screen, supersampled
    s = cv2.imread(S+'screen/%04d.jpg' % i)[..., ::-1]; sh, sw = s.shape[:2]
    pts = np.array([lo+lx*x+ly*y+lz*.0135 for x, y in QX]); uv, _ = project(cams[i], pts.astype(np.float32)); uv = uv+.5
    SS = 2
    Hm = cv2.getPerspectiveTransform(np.float32([[0, 0], [sw, 0], [sw, sh], [0, sh]]), np.float32(uv*SS))
    big = cv2.warpPerspective(s, Hm, (WW*SS, HH*SS), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
    m = cv2.warpPerspective(np.full((sh, sw), 255, np.uint8), Hm, (WW*SS, HH*SS), flags=cv2.INTER_LINEAR)
    sc = cv2.resize(s2l(big/255.), (WW, HH), interpolation=cv2.INTER_AREA); mk = cv2.resize(m/255., (WW, HH), interpolation=cv2.INTER_AREA).astype(np.float32)[..., None]
    sc = sc*.95*np.array([1.0, .975, .975], np.float32)
    # the rendered plate holds its own (older) screen: pull the bezel over its fringe, then lay the clean one in
    mko = cv2.dilate(mk[..., 0], np.ones((7, 7)))[..., None]
    ring = (mko > .01) & (mk < .999); bez = np.array([.0035, .0006, .0008], np.float32)
    im = np.where(ring, np.minimum(im, bez*2), im)
    im = im*(1-mk)+sc*mk
    # ---- lens: halation + bloom, vignette, filmic shoulder, grain
    q = cv2.resize(im, (WW//4, HH//4), interpolation=cv2.INTER_AREA); hi = np.clip(q-.45, 0, None)
    bl = cv2.GaussianBlur(hi, (0, 0), 5)*.6+cv2.GaussianBlur(hi, (0, 0), 22)*.4; bl = cv2.resize(bl, (WW, HH), interpolation=cv2.INTER_CUBIC)
    im = im+bl*np.array([.07, .028, .03], np.float32)
    im = im*vig[..., None]
    im = np.where(im > .8, .8+.2*np.tanh((im-.8)/.2), im)
    o = np.where(im < .0031308, im*12.92, 1.055*np.power(np.clip(im, 1e-8, None), 1/2.4)-.055)
    o = o+(o-cv2.GaussianBlur(o, (0, 0), 1.1))*.22*mk
    L = o.mean(-1, keepdims=True); o = o+(grain[(i*5) % 12] if i % 2 else grain[(i*5) % 12][::-1])[..., None]*.011*(1-.75*np.clip(L, 0, 1))
    return (np.clip(o, 0, 1)*255+.5).astype(np.uint8)
if __name__ == '__main__':
    if sys.argv[1] == 'test':
        for i in map(int, sys.argv[2:]): cv2.imwrite(S+'test%04d.png' % i, frame(i)[..., ::-1])
    else:
        a, b, out = int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
        p = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', '1080x1920', '-r', '30', '-i', '-', '-vf', 'scale=out_color_matrix=bt709:out_range=tv,format=yuv420p', '-c:v', 'libx264', '-preset', 'medium', '-crf', '10', '-colorspace', 'bt709', '-color_primaries', 'bt709', '-color_trc', 'bt709', out], stdin=subprocess.PIPE)
        for i in range(a, b):
            p.stdin.write(frame(i).tobytes())
            if i % 50 == 0: print(i, flush=True)
        p.stdin.close(); p.wait()
