"""Turn one ordinary product photo into a 2.5D item for the 3D shop scenes.

  python process.py photo.jpg out_dir/name --cat top|bottom|shoe

Steps (all free, runs on our server, nothing is generated):
  1. cut the product out of its background (open-source BiRefNet model via rembg)
  2. estimate a relief map: a soft "inflated" volume from the silhouette + fine folds from a
     monocular depth model (Depth Anything V2 Small, Apache-2.0)
  3. write name.webp (RGBA cut-out), name_depth.png (relief) and name.json (size, anchor)
"""
import argparse, json, os, sys
import numpy as np, cv2
from PIL import Image

_S = {}
def session():
    if 'rb' not in _S:
        from rembg import new_session
        _S['rb'] = new_session(os.environ.get('RB_MODEL', 'birefnet-general'))
    return _S['rb']

def depth_model():
    if 'da' not in _S:
        from transformers import pipeline
        _S['da'] = pipeline('depth-estimation', model='depth-anything/Depth-Anything-V2-Small-hf', device='cpu')
    return _S['da']

def cutout(img):
    from rembg import remove
    rgba = np.array(remove(img, session=session(), post_process_mask=True))
    a = rgba[..., 3].astype('f4') / 255
    # keep the biggest blob (drops stray bits of background)
    m = (a > .5).astype('u1'); n, lab, st, _ = cv2.connectedComponentsWithStats(m, 8)
    if n > 2:
        big = 1 + int(np.argmax(st[1:, cv2.CC_STAT_AREA])); keep = (lab == big).astype('u1')
        keep = cv2.dilate(keep, np.ones((9, 9), 'u1')); a *= keep
    rgba[..., 3] = (a * 255).astype('u1')
    return rgba

def relief(rgba):
    a = rgba[..., 3].astype('f4') / 255; m = (a > .5).astype('u1')
    h, w = m.shape; s = max(h, w)
    # 1) soft volume: rounded profile from the distance to the silhouette edge
    d = cv2.distanceTransform(m, cv2.DIST_L2, 5); d = d / (d.max() + 1e-6)
    vol = np.sqrt(np.clip(1 - (1 - d) ** 2, 0, 1)); vol = cv2.GaussianBlur(vol, (0, 0), s * .012)
    # 2) folds and seams from a monocular depth model, kept as fine detail only
    try:
        dep = np.array(depth_model()(Image.fromarray(rgba[..., :3]))['depth'].resize((w, h))).astype('f4')
        inside = m > 0; dn = (dep - dep[inside].mean()) / (dep[inside].std() + 1e-6)
        det = dn - cv2.GaussianBlur(dn, (0, 0), s * .03); det = np.clip(det * .12, -.25, .25)
    except Exception as e:
        print('depth model skipped:', e, file=sys.stderr); det = 0
    r = np.clip(vol * .85 + det + .15, 0, 1) * a
    return (r * 255).astype('u1')

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('src'); ap.add_argument('out'); ap.add_argument('--cat', required=True, choices=['top', 'bottom', 'shoe']); ap.add_argument('--flip', action='store_true')
    ap.add_argument('--max', type=int, default=1024); o = ap.parse_args()
    img = Image.open(o.src).convert('RGB')
    if max(img.size) > 2200: img.thumbnail((2200, 2200), Image.LANCZOS)
    rgba = cutout(img)
    ys, xs = np.where(rgba[..., 3] > 8); pad = 6
    y0, y1, x0, x1 = max(ys.min() - pad, 0), ys.max() + pad, max(xs.min() - pad, 0), xs.max() + pad
    rgba = rgba[y0:y1, x0:x1]
    if o.cat == 'top':   # drop the hanger from the photo; the site hangs every piece on its own 3D hanger
        wid = (rgba[..., 3] > 128).sum(1); start = int(np.argmax(wid >= .35 * wid.max())); cut = max(0, start - int(.015 * len(wid)))
        if cut > 0:
            rgba = rgba[cut:].copy(); m = (rgba[..., 3] > 40).astype('u1'); n, lab, st, _ = cv2.connectedComponentsWithStats(m, 8)
            if n > 2:
                big = 1 + int(np.argmax(st[1:, cv2.CC_STAT_AREA])); rgba[..., 3] = (rgba[..., 3] * cv2.dilate((lab == big).astype('u1'), np.ones((5, 5), 'u1'))).astype('u1')
            ys, xs = np.where(rgba[..., 3] > 8); rgba = rgba[:, max(0, xs.min() - 4):xs.max() + 5]
    if o.flip: rgba = rgba[:, ::-1].copy()
    h, w = rgba.shape[:2]; k = o.max / max(h, w)
    if k < 1: rgba = cv2.resize(rgba, (round(w * k), round(h * k)), interpolation=cv2.INTER_AREA)
    # un-premultiply fringe: pull edge colours from the inside so no halo of the old background remains
    a = rgba[..., 3]; core = (a > 230).astype('u1')
    if core.any():
        fill = cv2.inpaint(rgba[..., :3], (1 - core) * 255, 3, cv2.INPAINT_TELEA)
        edge = (a < 230)[..., None]; rgba[..., :3] = np.where(edge, fill, rgba[..., :3])
    rel = relief(rgba)
    h, w = rgba.shape[:2]; ys, xs = np.where(rgba[..., 3] > 128)
    top = ys.min(); tx = int(np.median(xs[ys < top + max(3, h * .02)]))  # hanger hook / waistband centre
    meta = {'cat': o.cat, 'w': w, 'h': h, 'aspect': w / h, 'anchor_top': [tx / w, top / h], 'bottom': ys.max() / h}
    os.makedirs(os.path.dirname(o.out) or '.', exist_ok=True)
    Image.fromarray(rgba).save(o.out + '.webp', quality=88, method=6)
    Image.fromarray(rel).save(o.out + '_depth.png')
    json.dump(meta, open(o.out + '.json', 'w'))
    print(o.out, w, h)

if __name__ == '__main__': main()
