# perspective still from the equirect shoe-room panorama (used as the instant placeholder before WebGL starts)
import sys, numpy as np, cv2
src, out, w, h, fov, pitch = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4]), float(sys.argv[5]), float(sys.argv[6])
im = cv2.imread(src); H, W = im.shape[:2]
f = (h / 2) / np.tan(np.radians(fov) / 2)
xs, ys = np.meshgrid(np.arange(w) - w / 2 + .5, np.arange(h) - h / 2 + .5)
d = np.stack([np.full_like(xs, f), -xs, -ys], -1)          # forward +X, right -Y, up +Z (Blender)
p = np.radians(pitch); R = np.array([[np.cos(p), 0, -np.sin(p)], [0, 1, 0], [np.sin(p), 0, np.cos(p)]])
d = d @ R.T; d /= np.linalg.norm(d, axis=-1, keepdims=True)
lon = np.arctan2(-d[..., 1], d[..., 0]); lat = np.arcsin(d[..., 2])
u = (.5 + lon / (2 * np.pi)) * W; v = (.5 - lat / np.pi) * H
cv2.imwrite(out, cv2.remap(im, u.astype('f4'), v.astype('f4'), cv2.INTER_AREA, borderMode=cv2.BORDER_WRAP), [cv2.IMWRITE_JPEG_QUALITY, 72])
