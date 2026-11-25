# Photoreal pass. 1 unit = 10 cm.
import bpy, bmesh, math, sys, os, random, time
from mathutils import Vector, noise, Euler
S = os.path.dirname(os.path.abspath(__file__)).replace(chr(92), "/")+"/"
AS = os.environ.get('AS', S+'assets-polyhaven/')
OLD = S+'old/scene_save.py'
src = open(OLD, encoding='utf8').read(); src = src.replace("bpy.data.fonts.load('C:/Windows/Fonts/segoeui.ttf')", 'None').replace("bpy.data.fonts.load('C:/Windows/Fonts/segoeuib.ttf')", 'None'); exec(src[src.index('bpy.ops.wm.read_factory_settings'):src.index('# ---------- base. x right')], globals())
BL = S+'old/scene.blend'
LH = 2.32; SW = 3.444; SH = SW*9/16; by = .255
with bpy.data.libraries.load(BL) as (a, b): b.objects = [n for n in a.objects if n.split('.')[0] in ('txt', 'gap', 'key', 'btn', 'padbtn', 'nub', 'base', 'basetrim', 'bezel', 'btnwell', 'cammod', 'dell', 'hinge', 'led', 'lid', 'lidshell', 'lipb', 'lipl', 'lipr', 'lipt', 'pad', 'padgap', 'padgap2', 'padgroove', 'rim', 'screen', 'slider', 'cam') and not n == 'cam']
for o in b.objects:
    if o and o.type in ('MESH', 'EMPTY', 'CURVE', 'FONT'): sc.collection.objects.link(o)
for o in sc.objects:   # clear of the space bar
    if o.name.split('.')[0] in ('btn', 'btnwell', 'pad', 'padbtn', 'padgap', 'padgap2', 'padgroove'): o.location.y -= .068
lid = bpy.data.objects['lid']; scr = bpy.data.objects['screen']; bpy.context.view_layer.update()
print('LAP', [(o.name, [round(v, 2) for v in o.matrix_world.translation]) for o in sc.objects if o.name.startswith(('st', 'cam'))][:8])
def gm(n, ob): return bpy.data.objects[ob].data.materials[0]
M_AL = gm('alu', 'base'); M_PAD = gm('pad', 'pad'); M_KEY = gm('key', 'key'); M_BEZ = gm('bezel', 'bezel'); M_WELL = gm('well', 'btnwell')
# hinge cover: the lid's bottom runs down into the base across the hinge span, so the panel no longer floats over a separate bar (small gaps stay at the outer ends)
bpy.data.objects['hinge'].hide_render = True; box('hingecover', 2.90, .115, .0615, (0, -.0175, -.02675), M_BEZ, .006, 2, lid, vertical_r=.035)
random.seed(4)
def link(me, name='o', m=None, smooth=True, parent=None, loc=(0, 0, 0)):
    o = bpy.data.objects.new(name, me); sc.collection.objects.link(o); o.location = loc
    if m: me.materials.append(m)
    for p in me.polygons: p.use_smooth = smooth
    if parent: o.parent = parent
    return o
def bevel(o, w_, n=3, ang=50):
    q = o.modifiers.new('b', 'BEVEL'); q.width = w_; q.segments = n; q.limit_method = 'ANGLE'; q.angle_limit = math.radians(ang); o.modifiers.new('w', 'WEIGHTED_NORMAL'); return o
def cyl(r, d, loc, m, rot=(0, 0, 0), seg=64, r2=None, bev=.01, parent=None):
    bm = bmesh.new(); bmesh.ops.create_cone(bm, cap_ends=True, segments=seg, radius1=r, radius2=r if r2 is None else r2, depth=d); me = bpy.data.meshes.new('c'); bm.to_mesh(me); bm.free()
    o = link(me, 'c', m, True, parent, loc); o.rotation_euler = rot
    return bevel(o, bev) if bev else o
def sphere(r, loc, m, seg=32):
    bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=seg, v_segments=seg//2, radius=r); me = bpy.data.meshes.new('s'); bm.to_mesh(me); bm.free(); return link(me, 's', m, True, None, loc)
def cable(pts, r, m, res=10):
    c = bpy.data.curves.new('cb', 'CURVE'); c.dimensions = '3D'; c.bevel_depth = r; c.bevel_resolution = 5; c.resolution_u = res; sp = c.splines.new('NURBS'); sp.points.add(len(pts)-1); sp.use_endpoint_u = True; sp.order_u = 4
    for p, q in zip(sp.points, pts): p.co = (*q, 1)
    o = bpy.data.objects.new('cb', c); sc.collection.objects.link(o); c.materials.append(m); return o
def area(name, loc, target, size, energy, col, sy=None, spread=None, cam_vis=False):
    l = bpy.data.lights.new(name, 'AREA'); l.energy = energy; l.color = col; l.size = size
    if sy: l.shape = 'RECTANGLE'; l.size_y = sy
    if spread: l.spread = math.radians(spread)
    o = bpy.data.objects.new(name, l); sc.collection.objects.link(o); o.location = loc; o.rotation_euler = (Vector(target)-Vector(loc)).to_track_quat('-Z', 'Y').to_euler(); return o
def emis(name, col, s):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; nt.nodes.clear(); e = nt.nodes.new('ShaderNodeEmission'); o = nt.nodes.new('ShaderNodeOutputMaterial'); e.inputs[0].default_value = (*col, 1); e.inputs[1].default_value = s; nt.links.new(e.outputs[0], o.inputs[0]); return m
def N(nt, t, **k):
    n = nt.nodes.new(t)
    for a, v in k.items(): setattr(n, a, v)
    return n
def photo(name, tex, scale, rot=0, tint=None, rmin=.25, rmax=.65, bump=.25, coat=0, sat=1, val=1):
    """image-based material in object space (box mapped)"""
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; b = nt.nodes['Principled BSDF']; tc = N(nt, 'ShaderNodeTexCoord'); mp = N(nt, 'ShaderNodeMapping'); mp.inputs['Scale'].default_value = (scale,)*3; mp.inputs['Rotation'].default_value = (0, 0, rot); nt.links.new(tc.outputs['Object'], mp.inputs[0])
    def im(k, cs):
        n = N(nt, 'ShaderNodeTexImage', projection='BOX', projection_blend=.15); n.image = bpy.data.images.load(AS+'tex/%s_%s.jpg' % (tex, k), check_existing=True); n.image.colorspace_settings.name = cs; nt.links.new(mp.outputs[0], n.inputs[0]); return n
    d = im('Diffuse', 'sRGB'); h = N(nt, 'ShaderNodeHueSaturation'); h.inputs['Saturation'].default_value = sat; h.inputs['Value'].default_value = val; nt.links.new(d.outputs[0], h.inputs['Color']); out = h.outputs[0]
    if tint:
        mx = N(nt, 'ShaderNodeMix', data_type='RGBA', blend_type='MULTIPLY'); mx.inputs[0].default_value = 1; nt.links.new(out, mx.inputs[6]); mx.inputs[7].default_value = (*tint, 1); out = mx.outputs[2]
    nt.links.new(out, b.inputs['Base Color']); r = im('Rough', 'Non-Color'); mr = N(nt, 'ShaderNodeMapRange'); mr.inputs['To Min'].default_value = rmin; mr.inputs['To Max'].default_value = rmax; nt.links.new(r.outputs[0], mr.inputs[0]); nt.links.new(mr.outputs[0], b.inputs['Roughness'])
    bp = N(nt, 'ShaderNodeBump'); bp.inputs['Strength'].default_value = bump; bp.inputs['Distance'].default_value = .02; nt.links.new(d.outputs[0], bp.inputs['Height']); nt.links.new(bp.outputs[0], b.inputs['Normal'])
    b.inputs['Coat Weight'].default_value = coat; b.inputs['Coat Roughness'].default_value = .16; return m
def woodm(name, tex, scale, rot, rmin, rmax, bump, val, sat=1, coat=0):
    m = photo(name, tex, scale, 0, rmin=rmin, rmax=rmax, bump=bump, coat=coat, val=val, sat=sat); nt = m.node_tree; mp = [n for n in nt.nodes if n.type == 'MAPPING'][0]; mp.inputs['Rotation'].default_value = rot
    oi = N(nt, 'ShaderNodeObjectInfo'); sc_ = N(nt, 'ShaderNodeVectorMath', operation='SCALE'); sc_.inputs['Scale'].default_value = 7.0; cb = N(nt, 'ShaderNodeCombineXYZ'); wn = N(nt, 'ShaderNodeTexWhiteNoise', noise_dimensions='1D'); nt.links.new(oi.outputs['Random'], wn.inputs['W']); nt.links.new(wn.outputs['Color'], sc_.inputs[0]); nt.links.new(sc_.outputs[0], mp.inputs['Location'])
    # boards never match exactly
    h = [n for n in nt.nodes if n.type == 'HUE_SAT'][0]; mr = N(nt, 'ShaderNodeMapRange'); mr.inputs['To Min'].default_value = val*.86; mr.inputs['To Max'].default_value = val*1.12; nt.links.new(oi.outputs['Random'], mr.inputs[0]); nt.links.new(mr.outputs[0], h.inputs['Value']); return m
def wear(m, smudge=.16, dust=.5, sc_=1.6, dscale=26):
    """greasy smudges in roughness + sparse dust specks, the things CG usually forgets"""
    nt = m.node_tree; b = nt.nodes['Principled BSDF']; tc = N(nt, 'ShaderNodeTexCoord'); n = N(nt, 'ShaderNodeTexNoise'); n.inputs['Scale'].default_value = sc_; n.inputs['Detail'].default_value = 6; n.inputs['Distortion'].default_value = 1.2; nt.links.new(tc.outputs['Object'], n.inputs['Vector'])
    r0 = b.inputs['Roughness'].default_value; mr = N(nt, 'ShaderNodeMapRange'); mr.inputs['From Min'].default_value = .38; mr.inputs['From Max'].default_value = .68; mr.inputs['To Min'].default_value = r0; mr.inputs['To Max'].default_value = min(.95, r0+smudge)
    nt.links.new(n.outputs['Fac'], mr.inputs[0]); nt.links.new(mr.outputs[0], b.inputs['Roughness'])
    v = N(nt, 'ShaderNodeTexVoronoi'); v.inputs['Scale'].default_value = dscale; v.inputs['Randomness'].default_value = 1; nt.links.new(tc.outputs['Object'], v.inputs['Vector']); wn = N(nt, 'ShaderNodeTexWhiteNoise'); nt.links.new(v.outputs['Position'], wn.inputs['Vector'])
    lt = N(nt, 'ShaderNodeMath', operation='LESS_THAN'); lt.inputs[1].default_value = .075; nt.links.new(v.outputs['Distance'], lt.inputs[0]); g = N(nt, 'ShaderNodeMath', operation='GREATER_THAN'); g.inputs[1].default_value = 1-.16*dust; nt.links.new(wn.outputs['Value'], g.inputs[0]); ml = N(nt, 'ShaderNodeMath', operation='MULTIPLY'); nt.links.new(lt.outputs[0], ml.inputs[0]); nt.links.new(g.outputs[0], ml.inputs[1]); k = N(nt, 'ShaderNodeMath', operation='MULTIPLY'); k.inputs[1].default_value = .35; nt.links.new(ml.outputs[0], k.inputs[0])
    mx = N(nt, 'ShaderNodeMix', data_type='RGBA'); mx.inputs[6].default_value = b.inputs['Base Color'].default_value; mx.inputs[7].default_value = (.45, .45, .47, 1); nt.links.new(k.outputs[0], mx.inputs[0])
    if not b.inputs['Base Color'].is_linked: nt.links.new(mx.outputs[2], b.inputs['Base Color'])
    return m
# ---- laptop finish
M_AL.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (.13, .132, .140, 1)
for m_ in bpy.data.materials:
    n_ = m_.node_tree and m_.node_tree.nodes.get('Principled BSDF')
    if n_ and n_.inputs['Emission Strength'].default_value > 0 and not n_.inputs['Emission Strength'].is_linked: n_.inputs['Emission Color'].default_value = (.9, .93, 1, 1); n_.inputs['Emission Strength'].default_value = min(n_.inputs['Emission Strength'].default_value, .22)
ob = bpy.data.objects['base']; mt_ = ob.data.materials[0]; bm = bmesh.new(); pts_ = []
for cx_, cy_, a0 in [(W/2-.11, D/2-.11, 0), (-W/2+.11, D/2-.11, 90), (-W/2+.11, -D/2+.11, 180), (W/2-.11, -D/2+.11, 270)]:
    for k in range(9): t_ = math.radians(a0+k*11.25); pts_.append((cx_+.11*math.cos(t_), cy_+.11*math.sin(t_)))
A_ = [bm.verts.new((x_, y_, -H/2)) for x_, y_ in pts_]; B_ = [bm.verts.new((x_, y_, H/2)) for x_, y_ in pts_]; n_ = len(pts_); bm.faces.new(A_[::-1]); bm.faces.new(B_)
for i in range(n_): bm.faces.new((A_[i], A_[(i+1) % n_], B_[(i+1) % n_], B_[i]))
for k in range(1, 14):
    g_ = bm.verts[:]+bm.edges[:]+bm.faces[:]; bmesh.ops.bisect_plane(bm, geom=g_, plane_co=(0, -D/2+.09*k, 0), plane_no=(0, 1, 0))
for v_ in bm.verts:
    if v_.co.z < 0:
        u_ = max(0, min(1, (v_.co.y+D/2)/1.15)); lift = (1-u_)**1.35; v_.co.z += lift*(H-.052); ins = .030*(1-min(1, (v_.co.y+D/2)/.16)); v_.co.y += max(0, ins)
        e_ = max(0, abs(v_.co.x)-(W/2-.12))/.12; v_.co.x -= math.copysign(.035*e_, v_.co.x)
me_ = bpy.data.meshes.new('base2'); bm.to_mesh(me_); bm.free(); me_.materials.append(mt_)
for p in me_.polygons: p.use_smooth = True
ob.data = me_; ob.modifiers.clear(); bevel(ob, .014, 4, 28)
bt = bpy.data.objects.get('basetrim')
if bt: bt.hide_render = True
dl = bpy.data.objects.get('dell')
if dl:
    M_BADGE = bpy.data.materials.new('badge'); M_BADGE.use_nodes = True; bb = M_BADGE.node_tree.nodes['Principled BSDF']; bb.inputs['Base Color'].default_value = (.86, .87, .89, 1); bb.inputs['Metallic'].default_value = 1; bb.inputs['Roughness'].default_value = .11; nt = M_BADGE.node_tree; tc = N(nt, 'ShaderNodeTexCoord'); mp = N(nt, 'ShaderNodeMapping'); mp.inputs['Scale'].default_value = (1, 40, 40); n = N(nt, 'ShaderNodeTexNoise'); n.inputs['Scale'].default_value = 30; nt.links.new(tc.outputs['Object'], mp.inputs[0]); nt.links.new(mp.outputs[0], n.inputs['Vector']); bp = N(nt, 'ShaderNodeBump'); bp.inputs['Strength'].default_value = .03; nt.links.new(n.outputs['Fac'], bp.inputs['Height']); nt.links.new(bp.outputs[0], bb.inputs['Normal'])
    if dl.type == 'CURVE':
        dl.data.materials.clear(); dl.data.materials.append(M_BADGE); dl.data.extrude = .0035; dl.data.bevel_depth = .0011; dl.data.bevel_resolution = 2; dl.location.z += .003; print('DELL curve')
    if dl.type == 'MESH':
        dl.data.materials.clear(); dl.data.materials.append(M_BADGE)
        for p in dl.data.polygons: p.material_index = 0
        print('DELL', dl.dimensions, len(dl.data.polygons), dl.location)
        bm = bmesh.new(); bm.from_mesh(dl.data); zs_ = [v.co.z for v in bm.verts]
        if max(zs_)-min(zs_) < .004:
            r_ = bmesh.ops.extrude_face_region(bm, geom=bm.faces[:]); bmesh.ops.translate(bm, verts=[v for v in r_['geom'] if isinstance(v, bmesh.types.BMVert)], vec=(0, 0, .006)); bm.to_mesh(dl.data)
        bm.free(); q_ = dl.modifiers.new('b', 'BEVEL'); q_.width = .0016; q_.segments = 2; q_.limit_method = 'ANGLE'
for o in list(sc.objects):
    if o.name.split('.')[0] in ('cammod', 'slider', 'cam') and o.type == 'MESH': bpy.data.objects.remove(o)
lt_ = bpy.data.objects.get('lipt'); LT = max((lid.matrix_world.inverted() @ (lt_.matrix_world @ Vector(c_))).y for c_ in lt_.bound_box) if lt_ else by+SH+.03; print('LIPT', LT, by+SH, LH); WTOP = LH-.028; WCY = (LT+.006+WTOP)/2; WZ = .0125
M_WC = mat('wcg', (.0035, .0035, .004), .055); M_WC.node_tree.nodes['Principled BSDF'].inputs['Coat Weight'].default_value = 1; M_WC.node_tree.nodes['Principled BSDF'].inputs['Coat Roughness'].default_value = .05; M_WT = mat('wct', (.005, .005, .0055), .42, 0, coat=.05, bump=.1, bscale=600); M_HOLE = mat('hole', (.001, .001, .001), .6)
wh = min(.070, WTOP-LT-.016); box('wcslot', .432, wh+.010, .004, (0, WCY, WZ-.0016), M_HOLE, 0, parent=lid, vertical_r=(wh+.010)/2-.0005); box('wc', .420, wh, .006, (0, WCY, WZ+.0012), M_WC, .0022, 3, lid, vertical_r=wh/2-.0005)
box('wctrack', .066, wh*.46, .002, (-.114, WCY, WZ+.0044), M_HOLE, 0, parent=lid, vertical_r=wh*.225); box('wctog', .040, wh*.42, .006, (-.127, WCY, WZ+.0062), M_WT, .0015, 3, lid, vertical_r=wh*.205); [box('rib', .0016, wh*.20, .0012, (-.127+dx_, WCY, WZ+.0094), M_WT, .0004, 2, lid) for dx_ in (-.009, -.0045, 0, .0045, .009)]; box('wcend', .020, wh*.30, .001, (-.094, WCY, WZ+.0050), mat('wce', (.004, .004, .004), .4), 0, parent=lid, vertical_r=wh*.149)
M_RG = mat('wcring', (.018, .018, .019), .30, .2, bump=.08, bscale=500); cyl(wh*.235, .004, (0, WCY, WZ+.0050), M_RG, seg=64, bev=.0012, parent=lid); cyl(wh*.100, .0045, (0, WCY, WZ+.0056), mat('wclens', (.0015, .0015, .003), .02), seg=48, bev=.0008, parent=lid)
for sx in (-1, 1): cyl(.0062, .004, (sx*.257, WCY, WZ-.0012), M_HOLE, seg=20, bev=0, parent=lid)
EO = bpy.data.objects.new('deckspace', None); sc.collection.objects.link(EO)
def handled(m, rough_to=.13, amt=1.75, dark=.62):
    nt = m.node_tree; b = nt.nodes['Principled BSDF']; tc = N(nt, 'ShaderNodeTexCoord'); tc.object = EO; mp = N(nt, 'ShaderNodeMapping'); mp.inputs['Scale'].default_value = (1/3.58, 1/2.36, 1); mp.inputs['Location'].default_value = (.5, .5, 0); nt.links.new(tc.outputs['Object'], mp.inputs[0])
    t = N(nt, 'ShaderNodeTexImage', interpolation='Linear', extension='EXTEND'); t.image = bpy.data.images.load(S+'sh/deck.png', check_existing=True); t.image.colorspace_settings.name = 'Non-Color'; nt.links.new(mp.outputs[0], t.inputs[0]); f = N(nt, 'ShaderNodeMath', operation='MULTIPLY'); f.inputs[1].default_value = amt; f.use_clamp = True; nt.links.new(t.outputs[0], f.inputs[0])
    for nm, to in (('Roughness', rough_to),):
        src = b.inputs[nm].links[0].from_socket if b.inputs[nm].is_linked else None; mx = N(nt, 'ShaderNodeMix', data_type='FLOAT'); nt.links.new(f.outputs[0], mx.inputs[0]); mx.inputs[3].default_value = to
        if src: nt.links.new(src, mx.inputs[2])
        else: mx.inputs[2].default_value = b.inputs[nm].default_value
        nt.links.new(mx.outputs[0], b.inputs[nm])
    src = b.inputs['Base Color'].links[0].from_socket if b.inputs['Base Color'].is_linked else None; mc = N(nt, 'ShaderNodeMix', data_type='RGBA', blend_type='MULTIPLY'); d = N(nt, 'ShaderNodeMath', operation='MULTIPLY'); d.inputs[1].default_value = dark; nt.links.new(f.outputs[0], d.inputs[0]); nt.links.new(d.outputs[0], mc.inputs[0]); mc.inputs[7].default_value = (.30, .29, .28, 1)
    if src: nt.links.new(src, mc.inputs[6])
    else: mc.inputs[6].default_value = b.inputs['Base Color'].default_value
    nt.links.new(mc.outputs[2], b.inputs['Base Color'])
    # skin oil: a thin dielectric film over the metal
    cw = N(nt, 'ShaderNodeMath', operation='MULTIPLY'); cw.inputs[1].default_value = .9; nt.links.new(f.outputs[0], cw.inputs[0]); nt.links.new(cw.outputs[0], b.inputs['Coat Weight']); b.inputs['Coat Roughness'].default_value = .16
for m_ in {M_AL, M_PAD}: handled(m_)
if os.environ.get('DBG'): print('ROUGH', M_AL.node_tree.nodes['Principled BSDF'].inputs['Roughness'].is_linked)
# ---- desk: photographed walnut veneer
DZ = -H-.035
M_DESK2 = photo('walnut', 'smoked_walnut_veneer', .115, math.pi/2, rmin=.26, rmax=.55, bump=.18, coat=.18, val=.62)
box('desk', 19, 11.0, .28, (0, -1.5, DZ-.14), M_DESK2, .035)
for x_ in (-1.55, 1.55):   # rubber feet
    for y_ in (-.10, .95): cyl(.09, .035, (x_, y_, DZ+.017), M_BLK, bev=.005)
# ---- room
WY = 16.0; FZ = -7.6
def paint(name, col):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; b = nt.nodes['Principled BSDF']; tc = N(nt, 'ShaderNodeTexCoord'); n = N(nt, 'ShaderNodeTexNoise'); n.inputs['Scale'].default_value = 9; n.inputs['Detail'].default_value = 8; n.inputs['Roughness'].default_value = .7; nt.links.new(tc.outputs['Object'], n.inputs['Vector']); n2 = N(nt, 'ShaderNodeTexNoise'); n2.inputs['Scale'].default_value = .28; n2.inputs['Detail'].default_value = 3; nt.links.new(tc.outputs['Object'], n2.inputs['Vector'])
    cr = N(nt, 'ShaderNodeMapRange'); cr.inputs['To Min'].default_value = .93; cr.inputs['To Max'].default_value = 1.05; nt.links.new(n2.outputs['Fac'], cr.inputs[0]); mx = N(nt, 'ShaderNodeMix', data_type='RGBA', blend_type='MULTIPLY'); mx.inputs[0].default_value = 1; mx.inputs[6].default_value = (*col, 1); nt.links.new(cr.outputs[0], mx.inputs[7]); nt.links.new(mx.outputs[2], b.inputs['Base Color']); b.inputs['Roughness'].default_value = .72; b.inputs['Specular IOR Level'].default_value = .3
    bp = N(nt, 'ShaderNodeBump'); bp.inputs['Strength'].default_value = .10; bp.inputs['Distance'].default_value = .03; nt.links.new(n.outputs['Fac'], bp.inputs['Height']); nt.links.new(bp.outputs[0], b.inputs['Normal']); return m
M_PL = paint('plaster', (.30, .295, .31))
M_SLAT = woodm('slat', 'black_oak_veneer', .13, (0, math.pi/2, 0), .42, .70, .14, .95, 1.0)
M_SH = woodm('shelfw', 'american_walnut_veneer', .13, (0, 0, 0), .36, .62, .10, 1.05, 1.1, .06); M_SHV = woodm('shelfv', 'american_walnut_veneer', .13, (0, math.pi/2, 0), .36, .62, .10, 1.05, 1.1, .06); M_SHB = woodm('shelfb', 'american_walnut_veneer', .13, (0, math.pi/2, 0), .45, .7, .08, .75, 1.0)
box('wall', 60, .2, 40, (0, WY+.5, 8), M_PL, 0); box('floor', 60, 40, .1, (0, 0, FZ), photo('floor', 'dark_wood', .05, 0, rmin=.3, rmax=.6, val=.5), 0)
x = -19.0
while x < -1.2: box('slat', .34, .30, 34, (x, WY+.26, 8), M_SLAT, .03, 2); x += .52
box('slatb', 18.2, .04, 34, (-10.2, WY+.38, 8), M_BLK, 0)
BLUE = (.035, .16, 1.0); INDIGO = (.10, .07, 1.0); VIOLET = (.34, .055, 1.0)
for dx_ in (-.075, .075): box('prof', .03, .16, 34, (-.98+dx_, WY+.36, 8), mat('prf', (.35, .35, .37), .35, 1), .004)
box('seam', .11, .02, 34, (-.98, WY+.33, 8), emis('ledB', (.17, .32, 1), 4.6), 0)
for dx_, e_ in ((-1, 150), (1, 210)):
    l_ = bpy.data.lights.new('grz', 'AREA'); l_.shape = 'RECTANGLE'; l_.size = .10; l_.size_y = 22; l_.energy = e_; l_.color = (.05, .17, 1); o_ = bpy.data.objects.new('grz', l_); sc.collection.objects.link(o_); o_.location = (-.98+dx_*.10, WY+.22, 4.5); o_.rotation_euler = Vector((dx_*.86, .50, 0)).to_track_quat('-Z', 'Y').to_euler(); o_.visible_camera = False
    o_.rotation_euler = (math.pi/2, 0, -math.atan2(dx_*.86, .50))
# bookcase: uprights, boards, back left open to the wall
X0, X1, SD = 1.2, 13.2, 2.6; SY = WY-SD/2+.35
XM = (X0+X1)/2; TH = .20
for x_ in (X0, XM, X1): box('up', TH, SD, 24, (x_, SY, FZ+12), M_SHV, .010, 2)
for a_, b_ in ((X0, XM), (XM, X1)): box('back', b_-a_, .06, 24, ((a_+b_)/2, SY+SD/2-.05, FZ+12), M_SHB, 0)
ZS = [-4.6, -1.2, 2.2, 5.6, 9.0, 12.4]; M_PIN = mat('pin', (.55, .50, .42), .3, 1)
for z_ in ZS:
    for a_, b_ in ((X0, XM), (XM, X1)):
        w_ = b_-a_-TH-.012; bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1); bmesh.ops.scale(bm, vec=(w_, SD-.14, TH), verts=bm.verts)
        for k in range(1, 12): bmesh.ops.bisect_plane(bm, geom=bm.verts[:]+bm.edges[:]+bm.faces[:], plane_co=(-w_/2+w_*k/12, 0, 0), plane_no=(1, 0, 0))
        for v_ in bm.verts: v_.co.z -= .028*(1-(2*v_.co.x/w_)**2)   # loaded shelves sag a little
        me_ = bpy.data.meshes.new('bd'); bm.to_mesh(me_); bm.free(); o_ = bevel(link(me_, 'bd', M_SH, True, None, ((a_+b_)/2, SY-.04, z_+.02)), .010, 2, 40)
        box('lip', w_, .07, .13, ((a_+b_)/2, SY-SD/2+.085, z_-.130), M_SH, .006)
        for sx in (-1, 1):
            for dy_ in (-.8, .8): cyl(.028, .12, ((a_+b_)/2+sx*(w_/2-.03), SY+dy_, z_-.10), M_PIN, (0, math.pi/2, 0), 16, bev=0)
        box('ls', w_-.5, .05, .02, ((a_+b_)/2, SY-SD/2+.20, z_-.095), emis('sl', (1, .74, .50), 3.2), 0)
        l_ = bpy.data.lights.new('sl', 'AREA'); l_.shape = 'RECTANGLE'; l_.size = w_-.5; l_.size_y = .06; l_.energy = 92; l_.color = (1, .71, .46); o_ = bpy.data.objects.new('sl', l_); sc.collection.objects.link(o_); o_.location = ((a_+b_)/2, SY-SD/2+.20, z_-.115); o_.rotation_euler = (math.radians(14), 0, 0); o_.visible_camera = False
# ---- scanned props
def load(name):
    with bpy.data.libraries.load(AS+name+'/'+name+'.blend') as (a, b): b.objects = a.objects
    return [o for o in b.objects if o and o.type == 'MESH' and not o.name.startswith('wdg') and 'stash' not in o.name]
def bounds(obs):
    lo = Vector((9e9,)*3); hi = -lo
    for o in obs:
        for c in o.bound_box:
            p = o.matrix_world @ Vector(c); lo = Vector(map(min, lo, p)); hi = Vector(map(max, hi, p))
    return lo, hi
def place(obs, loc, rz=0, s=10.0):
    """drop a group so its bottom centre sits at loc"""
    for o in obs:
        if o.name not in sc.collection.objects: sc.collection.objects.link(o)
    bpy.context.view_layer.update(); lo, hi = bounds(obs); e = bpy.data.objects.new('prop', None); sc.collection.objects.link(e); w_ = {o: o.matrix_world.copy() for o in obs}
    for o in obs:
        o.parent = None; o.matrix_world = w_[o]
    bpy.context.view_layer.update(); off = Vector(((lo.x+hi.x)/2, (lo.y+hi.y)/2, lo.z))
    for o in obs: o.matrix_world = __import__('mathutils').Matrix.Translation(-off) @ w_[o]; o.parent = e
    e.scale = (s,)*3; e.location = loc; e.rotation_euler = (0, 0, rz); return e
T = .12
exec(open(S+'shelf2.py', encoding='utf8').read(), globals())
pass
pass; pass; pass
pass; pass
exec(open(S+'left.py', encoding='utf8').read(), globals())
pass
# ---- desk clutter (sparse, real)
MUG = (-2.34, -.64)
M_BCAB = mat('bcab', (.012, .012, .013), .5); M_WCAB = mat('wcab', (.62, .62, .63), .55, bump=.5, bscale=260)
def fall(x_, y0=4.02): return [(x_, y0-.35, DZ+.034), (x_, y0-.08, DZ+.034), (x_+.01, y0+.06, DZ-.02), (x_+.02, y0+.10, DZ-.4), (x_+.02, y0+.10, DZ-3)]
def lay(pts, r): return [(x_, y_, DZ+r+dz) for x_, y_, dz in pts]
M_BRD = mat('braid', (.016, .016, .018), .72, bump=.9, bscale=170)
# power: leaves the left side, rests on the desk, goes over the back edge
cable([(-1.78, .62, -.095), (-1.95, .62, -.097), (-2.12, .63, -.11)]+lay([(-2.34, .68, .05), (-2.62, .86, .004), (-2.95, 1.25, 0), (-3.12, 1.85, 0), (-3.02, 2.6, 0), (-2.86, 3.2, 0)], .028)+fall(-2.82), .028, M_BCAB, 24)
cyl(.047, .24, (-1.93, .62, -.096), M_BCAB, (0, math.pi/2, 0), bev=.012); cyl(.036, .13, (-2.09, .622, -.104), M_BCAB, (0, math.pi/2+.1, 0), r2=.029, bev=.004)
# usb lead on the right: one lazy curve to the back
cable([(1.78, .05, -.095), (1.95, .05, -.096), (2.08, .055, -.105)]+lay([(2.26, .10, .045), (2.5, .30, .003), (2.72, .75, 0), (2.78, 1.4, 0), (2.62, 2.1, 0), (2.5, 2.9, 0), (2.5, 3.4, 0)], .020)+fall(2.5), .020, M_BRD, 24)
box('usbp', .20, .118, .052, (1.885, .05, -.095), M_BCAB, .014, 4); cyl(.026, .10, (2.02, .052, -.099), M_BCAB, (0, math.pi/2, 0), r2=.021, bev=.004)
# hdmi: thicker, crosses over the first
cable([(1.78, .50, -.095), (1.98, .50, -.097), (2.14, .51, -.11)]+lay([(2.36, .58, .04), (2.62, .84, .030), (2.86, 1.2, .03), (3.15, 1.75, .0), (3.3, 2.5, 0), (3.22, 3.2, 0)], .030)+fall(3.2), .030, M_BCAB, 24)
box('hdmi', .25, .20, .085, (1.91, .50, -.096), M_BCAB, .016, 4); cyl(.044, .14, (2.08, .505, -.105), M_BCAB, (0, math.pi/2+.1, 0), r2=.032, bev=.004)
exec(open(S+'mug.py', encoding='utf8').read(), globals())
# ---- iPhone (71.5 x 149.6 x 8.2 mm)
PW, PHH, PT = .715, 1.496, .082
ph = bpy.data.objects.new('phone', None); sc.collection.objects.link(ph); PX_, PY_ = .78, -2.55; LEAN = math.radians(22)
M_TI = mat('ti', (.21, .20, .19), .34, 1, bump=.10, bscale=700); wear(M_TI, .12, .2, 5); M_GLASS = mat('pglass', (.002, .002, .0025), .045); M_BAND = mat('band', (.12, .115, .11), .45)
def rr(w_, h_, r_, n=14):
    p = []
    for cx_, cy_, a0 in [(w_/2-r_, h_/2-r_, 0), (-w_/2+r_, h_/2-r_, 90), (-w_/2+r_, -h_/2+r_, 180), (w_/2-r_, -h_/2+r_, 270)]:
        for k in range(n+1): t_ = math.radians(a0+k*90/n); p.append((cx_+r_*math.cos(t_), cy_+r_*math.sin(t_)))
    return p
def loft(secs, m, name, parent, cap=True):
    """stack of rounded rects -> closed body. secs: (z, inset)"""
    R0 = .118; bm = bmesh.new(); rings = []
    for z_, ins in secs: rings.append([bm.verts.new((x_, y_+PHH/2, z_)) for x_, y_ in rr(PW-2*ins, PHH-2*ins, R0-ins)])
    for a_, b_ in zip(rings, rings[1:]):
        for i in range(len(a_)): bm.faces.new((a_[i], a_[(i+1) % len(a_)], b_[(i+1) % len(a_)], b_[i]))
    bm.faces.new(rings[0][::-1])
    if cap: bm.faces.new(rings[-1])
    me_ = bpy.data.meshes.new(name); bm.to_mesh(me_); bm.free(); return bevel(link(me_, name, m, True, parent), .0012, 2, 30)
h2 = PT/2; loft([(-h2, .016), (-h2+.004, .007), (-h2+.012, .0015), (-h2+.020, 0), (h2-.020, 0), (h2-.012, .0015), (h2-.005, .0065)], M_TI, 'frame', ph)
loft([(h2-.008, .0085), (h2-.002, .0085), (h2+.001, .0098), (h2+.0022, .0125), (h2+.0026, .017)], M_GLASS, 'glass', ph)
M_CASE = mat('case', (.010, .013, .024), .62, 0, bump=.22, bscale=520); wear(M_CASE, .14, .9, 3, 30); M_CASE.node_tree.nodes['Principled BSDF'].inputs['Sheen Weight'].default_value = .25
CT = .015; loft([(-h2-.016, .020), (-h2-.013, .004), (-h2-.004, -.011), (-h2+.012, -CT), (h2-.014, -CT), (h2+.001, -CT+.0015), (h2+.0075, -.0105), (h2+.0095, -.0055), (h2+.0088, .0005), (h2+.0050, .0048), (h2+.0015, .0080)], M_CASE, 'case', ph, False)
for z_, l_ in ((1.19, .10), (1.02, .15), (.85, .15)): box('cbt', .012, l_, .034, (-PW/2-CT-.003, z_, 0), M_CASE, .005, 3, ph, vertical_r=.005)
box('cbt', .012, .23, .034, (PW/2+CT+.003, .99, 0), M_CASE, .005, 3, ph, vertical_r=.005)
for z_, l_ in ((1.19, .085), (1.02, .135), (.85, .135)): box('btn', .012, l_, .030, (-PW/2-.003, z_, 0), M_TI, .004, 3, ph, vertical_r=.005)
box('btn', .012, .21, .030, (PW/2+.003, .99, 0), M_TI, .004, 3, ph, vertical_r=.005)
for x_, y_ in ((-PW/2, 1.30), (PW/2, 1.30), (-PW/2, .19), (PW/2, .19)): box('ant', .0035, .012, PT-.026, (x_, y_, 0), M_BAND, 0, parent=ph)
PSW = PW-2*.0235; PSH = PSW*844/390; pts = [(x_, y_+PHH/2) for x_, y_ in rr(PSW, PSH, .093)]; me = bpy.data.meshes.new('pscreen'); me.from_pydata([(x_, y_, h2+.0029) for x_, y_ in pts], [], [list(range(len(pts)))]); uv = me.uv_layers.new(); py0 = (PHH-PSH)/2
for i, (x_, y_) in enumerate(pts): uv.data[i].uv = (x_/PSW+.5, (y_-py0)/PSH)
psc = bpy.data.objects.new('pscreen', me); sc.collection.objects.link(psc); psc.parent = ph
def screen_mat(name, peak, rough, spec, black, smud, fall, spark, samt, glow, wb):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; nt.nodes.clear(); out = N(nt, 'ShaderNodeOutputMaterial'); tx_ = N(nt, 'ShaderNodeTexImage', interpolation='Cubic', extension='EXTEND')
    b = N(nt, 'ShaderNodeBsdfPrincipled'); b.inputs['Base Color'].default_value = (*black, 1); b.inputs['IOR'].default_value = 1.5; b.inputs['Specular IOR Level'].default_value = spec
    tc = N(nt, 'ShaderNodeTexCoord'); n = N(nt, 'ShaderNodeTexNoise'); n.inputs['Scale'].default_value = 2.1; n.inputs['Detail'].default_value = 7; n.inputs['Distortion'].default_value = 2.2; nt.links.new(tc.outputs['Object'], n.inputs['Vector']); mr = N(nt, 'ShaderNodeMapRange'); mr.inputs['From Min'].default_value = .42; mr.inputs['From Max'].default_value = .66; mr.inputs['To Min'].default_value = rough; mr.inputs['To Max'].default_value = rough+smud; nt.links.new(n.outputs['Fac'], mr.inputs[0]); nt.links.new(mr.outputs[0], b.inputs['Roughness'])
    # off-axis dimming, edge falloff, anti-glare sparkle, black glow, slow exposure band: what a lens sees on a lit panel
    lw = N(nt, 'ShaderNodeLayerWeight'); lw.inputs[0].default_value = .5; fr = N(nt, 'ShaderNodeMapRange'); fr.inputs['From Max'].default_value = .85; fr.inputs['To Min'].default_value = peak; fr.inputs['To Max'].default_value = peak*.60; nt.links.new(lw.outputs['Facing'], fr.inputs[0])
    def mth(op, a_, b_):
        q = N(nt, 'ShaderNodeMath', operation=op)
        for k_, v_ in enumerate((a_, b_)):
            if isinstance(v_, (int, float)): q.inputs[k_].default_value = v_
            else: nt.links.new(v_, q.inputs[k_])
        return q.outputs[0]
    uvn = N(nt, 'ShaderNodeTexCoord'); sp = N(nt, 'ShaderNodeSeparateXYZ'); nt.links.new(uvn.outputs['UV'], sp.inputs[0]); u_, v_ = sp.outputs[0], sp.outputs[1]
    ex = mth('POWER', mth('ABSOLUTE', mth('MULTIPLY', mth('SUBTRACT', u_, .5), 2), 0), 4); ey = mth('POWER', mth('ABSOLUTE', mth('MULTIPLY', mth('SUBTRACT', v_, .5), 2), 0), 4)
    edge = mth('SUBTRACT', 1, mth('MULTIPLY', mth('ADD', ex, ey), fall))
    wn = N(nt, 'ShaderNodeTexNoise'); wn.inputs['Scale'].default_value = spark; wn.inputs['Detail'].default_value = 1; nt.links.new(uvn.outputs['Object'], wn.inputs['Vector']); sk = mth('ADD', 1-.5*samt, mth('MULTIPLY', wn.outputs['Fac'], samt))
    ph_ = mth('ADD', mth('MULTIPLY', v_, 9.0), 0); BAND.append(ph_.node.inputs[1]); ph_.node.label = 'BAND'; band = mth('ADD', 1, mth('MULTIPLY', mth('SINE', ph_, 0), .012))
    bl = N(nt, 'ShaderNodeTexNoise'); bl.inputs['Scale'].default_value = .9; nt.links.new(uvn.outputs['Object'], bl.inputs['Vector']); mura = mth('ADD', .965, mth('MULTIPLY', bl.outputs['Fac'], .07))
    tot = mth('MULTIPLY', mth('MULTIPLY', mth('MULTIPLY', mth('MULTIPLY', fr.outputs[0], edge), sk), band), mura)
    mx = N(nt, 'ShaderNodeMix', data_type='RGBA', blend_type='ADD'); mx.inputs[0].default_value = 1; mx.inputs[7].default_value = (*glow, 1); nt.links.new(tx_.outputs['Color'], mx.inputs[6]); tn = N(nt, 'ShaderNodeMix', data_type='RGBA', blend_type='MULTIPLY'); tn.inputs[0].default_value = 1; tn.inputs[7].default_value = (*wb, 1); nt.links.new(mx.outputs[2], tn.inputs[6])
    nt.links.new(tn.outputs[2], b.inputs['Emission Color']); nt.links.new(tot, b.inputs['Emission Strength']); nt.links.new(tx_.outputs['Color'], b.inputs['Base Color']); nt.links.new(b.outputs[0], out.inputs[0]); return m, tx_
BAND = []
pm, TXP = screen_mat('pscreen', .60, .035, .55, (.002, .002, .003), .10, .05, 900, .05, (.0015, .0015, .003), (.97, .985, 1.03)); me.materials.append(pm)
lm, TXL = screen_mat('lscreen', .50, .17, .46, (.010, .010, .012), .06, .10, 420, .14, (.012, .012, .018), (.95, .985, 1.06)); scr.data.materials.clear(); scr.data.materials.append(lm)
# ---- bent aluminium stand, 4 mm sheet
M_ST = mat('stand', (.17, .172, .18), .38, 1, bump=.16, bscale=420); wear(M_ST, .10, .4, 2.2, 20); M_SIL = mat('sil', (.018, .018, .02), .75)
BZ = DZ+.012; th_ = .030; by_ = PY_+.30; zlip = .235
def sheet(path, wd, m, loc=(0, 0, 0), cx=0):
    """extrude a 2D (y,z) centre line into a bent plate"""
    bm = bmesh.new(); L = []; Rn = []
    for i, p in enumerate(path):
        a_ = Vector(path[max(0, i-1)]); b_ = Vector(path[min(len(path)-1, i+1)]); t_ = (b_-a_).normalized(); n_v = Vector((-t_.y, t_.x))*th_/2; L.append(Vector(p)+n_v); Rn.append(Vector(p)-n_v)
    prof = L+Rn[::-1]; A = [bm.verts.new((cx-wd/2, p.x, p.y)) for p in prof]; B = [bm.verts.new((cx+wd/2, p.x, p.y)) for p in prof]; n_ = len(prof)
    for i in range(n_): bm.faces.new((A[i], A[(i+1) % n_], B[(i+1) % n_], B[i]))
    k = len(L)
    for i in range(k-1):
        for V in (A, B): bm.faces.new((V[i], V[i+1], V[n_-2-i], V[n_-1-i]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces); me_ = bpy.data.meshes.new('sh'); bm.to_mesh(me_); bm.free(); return bevel(link(me_, 'sh', m, True, None, loc), .009, 3, 40)
def arc(c, r, a0, a1, n=10): return [(c[0]+r*math.cos(math.radians(a0+(a1-a0)*k/n)), c[1]+r*math.sin(math.radians(a0+(a1-a0)*k/n))) for k in range(n+1)]
# base plate (flat, rounded) + rear post
bp_ = box('stbase', .86, 1.02, .05, (PX_, by_+.12, BZ+.02), M_ST, .012, 4, vertical_r=.14)
ny, nz = math.sin(LEAN), math.cos(LEAN)          # direction up along the phone in (y,z)
lip = Vector((PY_-.02, BZ+zlip))                  # where the phone's bottom edge sits
back0 = lip+Vector((nz, -ny))*(PT+.030+.032)            # plate behind phone
plate = [tuple(back0+Vector((ny, nz))*s_) for s_ in (0, .2, .5, .8, 1.02)]
sheet(plate, .62, M_ST, (0, 0, 0), PX_)
for sgn in (-1, 1):   # two hooks
    b0 = back0; f0 = lip-Vector((nz, -ny))*.040; path = [tuple(b0+Vector((ny, nz))*.06), tuple(b0), tuple(b0-Vector((ny, nz))*.030+Vector((-nz, ny))*.012), tuple(b0-Vector((ny, nz))*.040+Vector((-nz, ny))*.045), tuple(f0-Vector((ny, nz))*.040+Vector((nz, -ny))*.035), tuple(f0-Vector((ny, nz))*.028), tuple(f0-Vector((ny, nz))*.005), tuple(f0+Vector((ny, nz))*.032)]
    sheet(path, .105, M_ST, (0, 0, 0), PX_+sgn*.205)
    box('sspad', .11, .06, .012, (PX_+sgn*.20, (lip.x+back0.x)/2, lip.y-.010), M_SIL, .004, parent=None).rotation_euler = (-LEAN+math.pi*0, 0, 0)
hp = back0+Vector((ny, nz))*.62; cyl(.050, .64, (PX_, hp.x+.075, hp.y-.02), M_ST, (0, math.pi/2, 0), bev=.006)
post = [(hp.x+.075, hp.y-.02), (hp.x+.12, hp.y-.16), (hp.x+.11, BZ+.30), (hp.x+.06, BZ+.10)]+[(hp.x+.02, BZ+.055), (hp.x-.08, BZ+.047)]
sheet(post, .34, M_ST, (0, 0, 0), PX_)
ph.rotation_euler = (math.pi/2-LEAN, 0, 0); ph.location = (PX_, lip.x+nz*(PT/2+.004)+ny*.016, lip.y-ny*(PT/2+.004)+nz*.016)
yaw = bpy.data.objects.new('yaw', None); sc.collection.objects.link(yaw); yaw.location = (PX_, PY_, 0); bpy.context.view_layer.update()
for o in list(sc.objects):
    if o.parent is None and o is not yaw and (o is ph or o.name.split('.')[0] in ('sh', 'stbase', 'sspad') or (o.name.startswith('c') and abs(o.location.x-PX_) < .01 and abs(o.location.y-(hp.x+.075)) < .01)):
        w_ = o.matrix_world.copy(); o.parent = yaw; o.matrix_parent_inverse = yaw.matrix_world.inverted()
yaw.rotation_euler = (0, 0, math.radians(-6))
# ---- light: the screens, the LEDs and one soft ceiling bounce
area('ceil', (-.8, -3.5, 9.0), (.2, .2, 0), 6.5, 70, (.74, .78, 1.0), 4.0)
area('blueL', (-7.5, 2.2, 3.6), (-.2, .1, .1), 3.4, 560, BLUE, 1.0); area('violR', (7.0, .6, 4.0), (.4, -.4, .1), 3.0, 260, VIOLET, 1.0); area('hair', (0.5, 6.5, 7.5), (0, 0, .2), 6.0, 300, (.26, .25, 1.0), .5)
area('wallB', (-11, WY-1.6, FZ+1), (-9, WY, 9), 9, 1500, BLUE, .6); area('wallI', (-3.2, WY-.6, FZ+1), (-2.6, WY, 8), 4, 320, INDIGO, .4); area('wallV', (14.5, WY-2.6, 12), (9, WY, 2), 6, 620, VIOLET, 1.5); area('shelf', (7.2, 8.5, 9.5), (7.2, WY, 2.5), 5, 110, (.60, .58, 1.0), 3)
box('glint', 11, .05, 1.5, (.4, -16.9, 2.2), emis('glint', (.82, .86, 1), 6.0), 0); box('roomlit', 30, .05, 9, (0, -17.4, 6.5), emis('roomlit', (.30, .32, .55), .55), 0); box('glint2', 5, .05, .7, (-5.2, -16.9, 4.2), emis('glint2', (.62, .60, 1), 4.0), 0); box('win', 4.2, .05, 6.5, (-3.6, -17, 6.5), emis('win', (.45, .55, 1), 1.6), 0); box('winbar', .16, .06, 6.6, (-3.6, -16.94, 6.5), M_BLK, 0); sphere(.8, (6.5, -15, 5.2), emis('lampb', (1, .62, .34), 2)); box('bwall', 60, .2, 40, (0, -18, 8), M_PL, 0)
w = bpy.data.worlds.new('w'); sc.world = w; w.use_nodes = True; w.node_tree.nodes['Background'].inputs[0].default_value = (.016, .016, .05, 1); w.node_tree.nodes['Background'].inputs[1].default_value = .35
# ---- camera: a person holding a camera
FPS = 24; sc.render.fps = FPS; cam = bpy.data.cameras.new('cam'); co = bpy.data.objects.new('cam', cam); sc.collection.objects.link(co); sc.camera = co
cam.sensor_fit = 'VERTICAL'; cam.sensor_height = 36; cam.lens = 40; cam.clip_end = 200; cam.dof.use_dof = True; cam.dof.aperture_blades = 9; bpy.context.view_layer.update()
PC = ph.matrix_world @ Vector((0, PHH/2, PT/2)); LC = lid.matrix_world @ Vector((0, by+SH/2, .0135))
K = [(0.0, (-1.95, -9.9, 4.0), (-.40, .0, .84), .30, .95), (4.0, (-.85, -8.8, 3.35), (-.02, -.1, .84), .26, 1.05), (7.6, (.45, -7.2, 2.65), (.36, -.8, .74), .06, 1.15), (12.0, (.92, -6.1, 2.10), (.56, -1.2, .66), .0, 1.25), (16.0, (.15, -7.5, 2.75), (.12, -.4, .82), .42, 1.3), (20.5, (-.62, -7.7, 2.80), (.16, -.6, .80), .28, 1.25), (22.8, (.66, -5.8, 2.05), (.60, -1.4, .62), .0, 1.2), (27.0, (-1.95, -9.9, 4.0), (-.40, .0, .84), .30, .95)]   # loop: ends on the opening pose, at rest, so frame 648 == frame 0
def herm(t, f):
    ts = [k[0] for k in K]; i = max(0, min(len(K)-2, sum(1 for x_ in ts if x_ <= t)-1)); h_ = ts[i+1]-ts[i]; u = max(0, min(1, (t-ts[i])/h_))
    def tg(j):
        if j in (0, len(K)-1): return 0
        d0 = (f(K[j])-f(K[j-1]))/(ts[j]-ts[j-1]); d1 = (f(K[j+1])-f(K[j]))/(ts[j+1]-ts[j]); return 0 if d0*d1 <= 0 else 2*d0*d1/(d0+d1)
    return (2*u**3-3*u*u+1)*f(K[i])+(u**3-2*u*u+u)*h_*tg(i)+(-2*u**3+3*u*u)*f(K[i+1])+(u**3-u*u)*h_*tg(i+1)
def nz1(t, s_): return noise.noise(Vector((t, s_*17.3, s_*5.1)))
TL = 27.0; LX = 3.0   # loop length (648 frames / 24 fps) and shake crossfade at the end
def shake0(t, s_, a): return a*(nz1(t*.55, s_)*1.0+nz1(t*1.5, s_+9)*.42+nz1(t*4.3, s_+21)*.10)
def shake(t, s_, a):   # periodic handheld shake: the last LX seconds fade into the shake from just before t=0
    t = t % TL; w = max(0., (t-(TL-LX))/LX); w = w*w*(3-2*w)
    return shake0(t, s_, a) if w == 0 else ((1-w)*shake0(t, s_, a)+w*shake0(t-TL, s_, a))/math.sqrt((1-w)**2+w*w)
def set_cam(t):
    t = t % TL
    p = Vector([herm(t, lambda k, a=a: k[1][a]) for a in range(3)]); g = Vector([herm(t, lambda k, a=a: k[2][a]) for a in range(3)])
    p += Vector((shake(t, 1, .10), shake(t, 2, .07), shake(t, 3, .085)+.018*math.sin(t*2*math.pi*7/TL)))
    q = (g-p).to_track_quat('-Z', 'Y').to_euler(); co.location = p; co.rotation_euler = Euler((q.x+shake(t, 4, .0065), q.y+shake(t, 5, .0075), q.z+shake(t, 6, .0065)))
    f = PC.lerp(LC, max(0, min(1, herm(t, lambda k: k[3])+shake(t, 7, .035)))); cam.dof.focus_distance = (f-p).dot((g-p).normalized()); cam.dof.aperture_fstop = herm(t, lambda k: k[4])
NF = 648
M_PER = mat('person', (.012, .011, .012), .9); per = bpy.data.objects.new('per', None); sc.collection.objects.link(per)
for r_, l_, sz in ((.95, (0, 0, 1.5), (.82, .9, 1.12)), (1.0, (0, 0, -.75), (2.05, .95, 1.35)), (.5, (0, 0, .55), (.85, .85, 1)), (.75, (-1.35, .5, -1.1), (.5, .8, 1.4)), (.75, (1.35, .5, -1.1), (.5, .8, 1.4))):
    p_ = sphere(r_, l_, M_PER, 24); p_.parent = per; p_.scale = sz; p_.visible_camera = False; p_.visible_diffuse = False; p_.visible_shadow = False
for i in range(-1, NF+1):
    set_cam(i/FPS); per.location = co.location+Vector((.3+shake(i/FPS, 11, .22), -2.6, -.55+shake(i/FPS, 12, .10))); per.keyframe_insert('location', frame=i); co.keyframe_insert('location', frame=i); co.keyframe_insert('rotation_euler', frame=i); cam.dof.keyframe_insert('focus_distance', frame=i); cam.dof.keyframe_insert('aperture_fstop', frame=i)
def set_screen(i):
    for tx_, d in ((TXP, 'phone'), (TXL, 'laptop')):
        f = S+'cap24/%s/%04d.jpg' % (d, i)
        if not os.path.exists(f): f = S+'cap24/%s/%04d.jpg' % (d, min(869, round(i/FPS*30)))
        if tx_.image: bpy.data.images.remove(tx_.image)
        tx_.image = bpy.data.images.load(f)
sc.render.resolution_x = 1440; sc.render.resolution_y = 2560; sc.render.resolution_percentage = int(os.environ.get('PCT', '100')); sc.render.use_persistent_data = True; sc.view_settings.view_transform = 'Standard'
sc.render.engine = 'CYCLES'; c = sc.cycles; c.device = 'CPU'; c.samples = int(os.environ.get('SPP', '28')); c.use_adaptive_sampling = True; c.adaptive_threshold = .03; c.use_denoising = True; c.denoiser = 'OPENIMAGEDENOISE'; c.denoising_input_passes = 'RGB_ALBEDO_NORMAL'
c.max_bounces = 5; c.diffuse_bounces = 3; c.glossy_bounces = 3; c.transmission_bounces = 2; c.transparent_max_bounces = 6; c.sample_clamp_indirect = 3; c.sample_clamp_direct = 14; c.caustics_reflective = False; c.caustics_refractive = False
sc.view_layers[0].cycles.use_denoising = True; sc.render.use_motion_blur = True; sc.render.motion_blur_shutter = .5; sc.render.use_simplify = False
sc.render.image_settings.file_format = 'OPEN_EXR'; sc.render.image_settings.color_depth = '16'; sc.render.image_settings.exr_codec = 'DWAA'
if os.environ.get('BORDER'):
    bx = [float(v) for v in os.environ['BORDER'].split(',')]; sc.render.use_border = True; sc.render.use_crop_to_border = True; sc.render.border_min_x, sc.render.border_max_x, sc.render.border_min_y, sc.render.border_max_y = bx
OUT = os.environ.get('OUT', S+'rend/'); os.makedirs(OUT, exist_ok=True); a = sys.argv[sys.argv.index('--')+1:]
frames = [int(x_) for x_ in a[0].split(',')] if ':' not in a[0] else list(range(*[int(x_) for x_ in a[0].split(':')]))
if os.environ.get('SAVE'):
    set_screen(0); bpy.ops.outliner.orphans_purge(do_recursive=True); bpy.ops.file.pack_all(); bpy.ops.wm.save_as_mainfile(filepath=S+'pk/room.blend', compress=True); sys.exit()
for i in frames:
    f = OUT+'%04d.exr' % i
    if os.path.exists(f): continue
    sc.frame_set(i); set_screen(i); [setattr(q_, 'default_value', i*(2*math.pi*22/648)+k_*2) for k_, q_ in enumerate(BAND)]; t0 = time.time(); sc.render.filepath = f+'.tmp.exr'; bpy.ops.render.render(write_still=True); os.replace(f+'.tmp.exr', f); print('FRAME', i, round(time.time()-t0, 1), flush=True)
