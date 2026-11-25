import bpy, math, sys, os, json
from mathutils import Vector, Matrix
S = '/tmp/'
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
# units: 1 = 10 cm. Dell 15.6": 35.8 x 23.5 cm, base 1.6 cm
W, D, H = 3.58, 2.36, 0.15
FONT = bpy.data.fonts.load('C:/Windows/Fonts/segoeui.ttf')
FONTB = bpy.data.fonts.load('C:/Windows/Fonts/segoeuib.ttf')

def mat(name, col, rough=.5, metal=0, emit=None, es=0, bump=0, bscale=900, coat=0, rvar=0):
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree; b = nt.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*col, 1); b.inputs['Roughness'].default_value = rough
    b.inputs['Metallic'].default_value = metal
    if coat: b.inputs['Coat Weight'].default_value = coat; b.inputs['Coat Roughness'].default_value = .2
    if emit: b.inputs['Emission Color'].default_value = (*emit, 1); b.inputs['Emission Strength'].default_value = es
    if bump or rvar:
        tc = nt.nodes.new('ShaderNodeTexCoord'); n = nt.nodes.new('ShaderNodeTexNoise')
        n.inputs['Scale'].default_value = bscale; n.inputs['Detail'].default_value = 3
        nt.links.new(tc.outputs['Object'], n.inputs['Vector'])
        if bump:
            bp = nt.nodes.new('ShaderNodeBump'); bp.inputs['Strength'].default_value = bump; bp.inputs['Distance'].default_value = .002
            nt.links.new(n.outputs['Fac'], bp.inputs['Height']); nt.links.new(bp.outputs['Normal'], b.inputs['Normal'])
        if rvar:
            n2 = nt.nodes.new('ShaderNodeTexNoise'); n2.inputs['Scale'].default_value = 2.2; n2.inputs['Detail'].default_value = 5
            nt.links.new(tc.outputs['Object'], n2.inputs['Vector'])
            mr = nt.nodes.new('ShaderNodeMapRange'); mr.inputs['To Min'].default_value = rough - rvar; mr.inputs['To Max'].default_value = rough + rvar
            nt.links.new(n2.outputs['Fac'], mr.inputs['Value']); nt.links.new(mr.outputs['Result'], b.inputs['Roughness'])
    return m

M_AL = mat('alu', (.15, .152, .16), .38, .9, bump=.12, bscale=260)
M_PAD = mat('pad', (.15, .153, .16), .33, .75)
M_EDGE = mat('edge', (.5, .5, .52), .18, 1)
M_KEY = mat('key', (.006, .006, .0065), .5, 0, bump=.08, bscale=300)
M_WELL = mat('well', (.006, .006, .007), .6)
M_LEG = mat('legend', (.9, .9, .92), .5, emit=(1, .93, .9), es=.28)
M_BEZ = mat('bezel', (.006, .006, .0065), .32, coat=.25)
M_LOGO = mat('logo', (.75, .75, .78), .4, .6, emit=(1,.75,.75), es=.07)
M_DESK = mat('desk', (.018, .014, .014), .22, 0, bump=.0, rvar=.07, coat=.35)
M_WALL = mat('wall', (.10, .095, .095), .85, bump=.3, bscale=30)
M_BLK = mat('blk', (.004, .004, .004), .5)

def box(name, sx, sy, sz, loc, m, bev=.02, seg=3, parent=None, vertical_r=0):
    me = bpy.data.meshes.new(name)
    if vertical_r:
        # rounded-rect prism
        pts = []; r = vertical_r
        for cx, cy, a0 in [(sx/2-r, sy/2-r, 0), (-sx/2+r, sy/2-r, 90), (-sx/2+r, -sy/2+r, 180), (sx/2-r, -sy/2+r, 270)]:
            for k in range(7):
                a = math.radians(a0 + k*15); pts.append((cx+r*math.cos(a), cy+r*math.sin(a)))
        n = len(pts)
        v = [(x, y, -sz/2) for x, y in pts] + [(x, y, sz/2) for x, y in pts]
        f = [list(range(n))[::-1], list(range(n, 2*n))] + [[i, (i+1) % n, n+(i+1) % n, n+i] for i in range(n)]
    else:
        v = [(x*sx/2, y*sy/2, z*sz/2) for z in (-1, 1) for x, y in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
        f = [(3, 2, 1, 0), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
    me.from_pydata(v, [], f); me.update()
    o = bpy.data.objects.new(name, me); sc.collection.objects.link(o); o.location = loc
    me.materials.append(m)
    if bev:
        b = o.modifiers.new('b', 'BEVEL'); b.width = bev; b.segments = seg; b.limit_method = 'ANGLE'; b.angle_limit = math.radians(40)
    for p in me.polygons: p.use_smooth = True
    if bev:
        w = o.modifiers.new('wn', 'WEIGHTED_NORMAL'); w.keep_sharp = False
    else:
        for p in me.polygons: p.use_smooth = False
    if parent: o.parent = parent
    return o

def text(s, size, loc, m, font=FONT, parent=None, rot=(0, 0, 0), ax='CENTER', ay='CENTER', ext=0):
    c = bpy.data.curves.new('t', 'FONT'); c.body = s; c.font = font; c.size = size; c.align_x = ax; c.align_y = ay; c.extrude = ext
    c.resolution_u = 3
    o = bpy.data.objects.new('t', c); sc.collection.objects.link(o); o.location = loc; o.rotation_euler = rot; c.materials.append(m)
    if parent: o.parent = parent
    return o

# ---------- base. x right, y back, z up; top deck at z=0, hinge at y=+D/2
box('base', W, D, H, (0, 0, -H/2), M_AL, .022, 4, vertical_r=.11)
box('basetrim', W+.002, D+.002, .012, (0, 0, -.034), M_EDGE, .004, 2, vertical_r=.11)
# keyboard well + keys (numpad layout)
U = .186; KEY = .158; kbw = 18.3*U
x0 = -kbw/2; ytop = .80
box('well', kbw+.05, 6*U+.0, .02, (0, ytop-2.93*U+.005, -.0092), M_WELL, .0, vertical_r=.03)
rows = [
 (0.62, [('esc',1),('F1',1),('F2',1),('F3',1),('F4',1),('F5',1),('F6',1),('F7',1),('F8',1),('F9',1),('F10',1),('F11',1),('F12',1),('prt sc',1),None,('home',1),('end',1),('pg up',1),('pg dn',1)]),
 (1, [('`|~',1),('1|!',1),('2|@',1),('3|#',1),('4|$',1),('5|%',1),('6|^',1),('7|&',1),('8|*',1),('9|(',1),('0|)',1),('-|_',1),('=|+',1),('backspace',1.15),None,('num\nlock',1),('/',1),('*',1),('–',1)]),
 (1, [('tab',1.45),('Q',1),('W',1),('E',1),('R',1),('T',1),('Y',1),('U',1),('I',1),('O',1),('P',1),('[|{',1),(']|}',1),('\\||',.7),None,('7',1),('8',1),('9',1),('+',1)]),
 (1, [('caps lock',1.7),('A',1),('S',1),('D',1),('F',1),('G',1),('H',1),('J',1),('K',1),('L',1),(';|:',1),("'|\"",1),('enter',1.45),None,('4',1),('5',1),('6',1),('+',1)]),
 (1, [('shift',2.1),('Z',1),('X',1),('C',1),('V',1),('B',1),('N',1),('M',1),(',|<',1),('.|>',1),('/|?',1),('shift',2.05),None,('1',1),('2',1),('3',1),('enter',1)]),
 (1, [('ctrl',1.2),('fn',1),('win',1),('alt',1.05),('',5),('alt',1),('ctrl',1),('<',.97),('^',.97),('>',.97),None,('0',2),('.',1),('enter',1)]),
]
y = ytop
for h, row in rows:
    x = x0; kh = h*U
    for k in row:
        if k is None: x = x0 + 14.3*U; continue
        s, w = k
        cw = w*U - (U-KEY); ch = kh - (U-KEY)
        cx = x + w*U/2; cy = y - kh/2
        box('k', cw, ch, .05, (cx, cy, -.004), M_KEY, .009, 2, vertical_r=.018)
        z = .0218
        if '|' in s and len(s) >= 3:
            a, b = s[0], s[2:]
            text(a, .052, (cx-.035, cy-.03, z), M_LEG); text(b, .045, (cx-.035, cy+.034, z), M_LEG)
        elif len(s) == 1 and s.isalnum() and h == 1:
            if s.isalpha(): text(s, .066, (cx-.034, cy+.026, z), M_LEG)
            else: text(s, .058, (cx, cy, z), M_LEG)
        elif s: text(s, .038 if len(s) > 1 else .052, (cx, cy, z), M_LEG)
        x += w*U
    y -= kh
# trackpad
PX = -.30; PY = -.78
box('padgroove', 1.10, .66, .004, (PX, PY, -.0012), M_WELL, 0, vertical_r=.035)
box('pad', 1.085, .645, .006, (PX, PY, -.0006), M_PAD, .003, 2, vertical_r=.03)
box('padline', 1.085, .004, .001, (PX, PY-.18, .0012), M_WELL, 0)
box('padline2', .004, .145, .001, (PX, PY-.25, .0012), M_WELL, 0)
# power led
box('led', .035, .010, .003, (1.42, .955, .001), mat('led', (1, 1, 1), emit=(1, .95, .9), es=3), 0)
# hinge bar
cyl = bpy.data.meshes.new('h'); import bmesh
bm = bmesh.new(); bmesh.ops.create_cone(bm, cap_ends=True, segments=32, radius1=.052, radius2=.052, depth=2.9); bm.to_mesh(cyl); bm.free()
o = bpy.data.objects.new('hinge', cyl); sc.collection.objects.link(o); o.rotation_euler = (0, math.pi/2, 0); o.location = (0, D/2-.03, -.01); cyl.materials.append(M_BLK)
for p in cyl.polygons: p.use_smooth = True

# ---------- lid
lid = bpy.data.objects.new('lid', None); sc.collection.objects.link(lid); lid.location = (0, D/2-.02, .02)
TILT = math.radians(16)   # leaning back from vertical
lid.rotation_euler = (math.pi/2 - TILT, 0, 0)  # local x right, local y up the panel, local z toward viewer
LH = 2.32
box('lidshell', W, LH, .055, (0, LH/2, -.03), M_AL, .012, 3, lid, vertical_r=.09)
box('bezel', W-.03, LH-.03, .02, (0, LH/2, .002), M_BEZ, .006, 2, lid, vertical_r=.08)
SW = 3.444; SH = SW*9/16
by = .255
box('rim', SW+.016, SH+.016, .001, (0, by+SH/2, .0122), M_BLK, 0, parent=lid)
me = bpy.data.meshes.new('screen')
me.from_pydata([(-SW/2, by, .0135), (SW/2, by, .0135), (SW/2, by+SH, .0135), (-SW/2, by+SH, .0135)], [], [(0, 1, 2, 3)])
uv = me.uv_layers.new()
for i, c in enumerate([(0, 0), (1, 0), (1, 1), (0, 1)]): uv.data[i].uv = c
scr = bpy.data.objects.new('screen', me); sc.collection.objects.link(scr); scr.parent = lid
sm = bpy.data.materials.new('screen'); sm.use_nodes = True; nt = sm.node_tree; nt.nodes.clear()
em = nt.nodes.new('ShaderNodeEmission'); out = nt.nodes.new('ShaderNodeOutputMaterial'); tx = nt.nodes.new('ShaderNodeTexImage')
tx.interpolation = 'Cubic'
lp = nt.nodes.new('ShaderNodeLightPath'); mr = nt.nodes.new('ShaderNodeMapRange'); mr.inputs['To Min'].default_value = .42; mr.inputs['To Max'].default_value = .9
nt.links.new(lp.outputs['Is Camera Ray'], mr.inputs['Value']); nt.links.new(mr.outputs['Result'], em.inputs['Strength'])
nt.links.new(tx.outputs['Color'], em.inputs['Color']); nt.links.new(em.outputs[0], out.inputs[0]); me.materials.append(sm)
text('DELL', .115, (0, .125, .0130), M_LOGO, FONTB, lid, ext=.001)

# ---------- desk and room
box('desk', 14, 7, .1, (0, 1.2, -H-.05-.03), M_DESK, .03)
wall = box('wall', 40, .1, 18, (0, 9.5, 4), M_WALL, 0)

def area(name, loc, target, size, energy, col, sy=None):
    l = bpy.data.lights.new(name, 'AREA'); l.energy = energy; l.color = col; l.size = size
    if sy: l.shape = 'RECTANGLE'; l.size_y = sy
    o = bpy.data.objects.new(name, l); sc.collection.objects.link(o); o.location = loc
    o.rotation_euler = (Vector(target)-Vector(loc)).to_track_quat('-Z', 'Y').to_euler(); return o
RED = (1, .012, .02)
R = json.load(open(S+'light.json')) if os.path.exists(S+'light.json') else {}
area('redR', (5.5, -1.0, 3.2), (0, .0, 0), 2.6, R.get('redR', 260), RED, .7)
area('redL', (-5.5, 1.2, 2.4), (0, .2, 0), 2.2, R.get('redL', 170), (1, .02, .05), .5)
area('redTop', (0.8, 4.2, 5.2), (0, -.2, 0), 4.5, R.get('redTop', 190), RED, .35)   # grazing strip: key edges + deck sheen
area('soft', (-1.5, -4.5, 5.0), (0, .1, 0), 2.5, R.get('soft', 3), (1, .55, .5))
area('wallglow', (-4.2, 8.6, -.6), (-3.2, 9.5, 5.), 6, R.get('wall', 210), RED, .3)
area('wallglow2', (4.6, 8.6, -.6), (4.2, 9.5, 5.), 4, R.get('wall2', 150), (1, .01, .05), .3)
# out-of-focus practicals
for i, (x, yv, z, r, e) in enumerate([][:0] and [(-3.3, 8.8, 3.4, .10, 22), (-2.5, 8.9, 4.6, .07, 16), (3.1, 8.8, 4.1, .09, 22), (2.4, 9.0, 5.4, .06, 14), (-3.9, 8.7, 5.2, .06, 14), (3.8, 8.7, 2.6, .08, 18)]):
    bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=16, v_segments=8, radius=r); m_ = bpy.data.meshes.new('p'); bm.to_mesh(m_); bm.free()
    o = bpy.data.objects.new('p', m_); sc.collection.objects.link(o); o.location = (x, yv, z); m_.materials.append(mat('pm%d' % i, (0, 0, 0), emit=(1, .03, .04), es=e))
w = bpy.data.worlds.new('w'); sc.world = w; w.use_nodes = True
w.node_tree.nodes['Background'].inputs[0].default_value = (.02, .001, .002, 1); w.node_tree.nodes['Background'].inputs[1].default_value = .25

# ---------- camera
cam = bpy.data.cameras.new('cam'); co = bpy.data.objects.new('cam', cam); sc.collection.objects.link(co); sc.camera = co
cam.sensor_fit = 'VERTICAL'; cam.sensor_height = 36; cam.lens = 50
cam.dof.use_dof = True; cam.dof.aperture_fstop = .9  # in this 1=10cm scale; tuned by eye
cam.dof.aperture_blades = 0
bpy.context.view_layer.update()
SCRN = lid.matrix_world @ Vector((0, by+SH/2, .0135))
FWD = (lid.matrix_world.to_3x3() @ Vector((0, 0, 1))).normalized()
UPV = (lid.matrix_world.to_3x3() @ Vector((0, 1, 0))).normalized()
def scr_pt(u, v): return SCRN + Vector((1, 0, 0))*(u*SW/2) + UPV*(v*SH/2)

def ease(u): u = max(0., min(1., u)); return u*u*u*(u*(u*6-15)+10)
# keyframes: t, position, look target. Slow gimbal moves only.
K = [
 (0.0,  Vector((-1.55, -6.6, 4.35)), Vector((-.10, .25, .62))),
 (4.4,  Vector((-.55, -6.15, 3.75)), Vector((0, .45, .78))),
 (10.4, Vector((.28, -3.55, 2.15)), Vector((0, .9, 1.02))),
 (16.0, Vector((.80, -3.15, 1.75)), Vector((.03, .9, 1.13))),
 (22.0, Vector((-.62, -3.10, 1.95)), Vector((-.02, .9, 1.10))),
 (29.5, Vector((.45, -3.0, 1.85)), Vector((.02, .9, 1.12))),
 (35.4, Vector((.05, -4.05, 2.45)), Vector((0, .75, .95))),
]
def catmull(t):
    # monotone-ish hermite through keys: C1 so the gimbal never jerks
    ts = [k[0] for k in K]
    i = max(0, min(len(K)-2, sum(1 for x in ts if x <= t)-1))
    t0, t1 = ts[i], ts[i+1]; h = t1-t0; u = max(0, min(1, (t-t0)/h))
    def tang(j, c):
        if j == 0 or j == len(K)-1: return Vector((0, 0, 0))
        out = Vector((0, 0, 0))
        for a in range(3):
            d0 = (K[j][c][a]-K[j-1][c][a])/(ts[j]-ts[j-1]); d1 = (K[j+1][c][a]-K[j][c][a])/(ts[j+1]-ts[j])
            out[a] = 0 if d0*d1 <= 0 else 2*d0*d1/(d0+d1)
        return out
    r = []
    for c in (1, 2):
        p0, p1, m0, m1 = K[i][c], K[i+1][c], tang(i, c), tang(i+1, c)
        r.append((2*u**3-3*u*u+1)*p0 + (u**3-2*u*u+u)*h*m0 + (-2*u**3+3*u*u)*p1 + (u**3-u*u)*h*m1)
    return r
def set_cam(t):
    p, tg = catmull(t)
    # 2 mm operator float, so it reads as a human on a gimbal and not a robot
    p = p + Vector((math.sin(t*.83+.4)*.018+math.sin(t*1.9)*.005, 0, math.sin(t*.67+2)*.014+math.sin(t*2.3+1)*.004))
    co.location = p; q = (tg-p).to_track_quat('-Z', 'Y'); co.rotation_euler = q.to_euler()
    f = scr_pt(0, -.1); d = (f-p).dot((tg-p).normalized()); cam.dof.focus_distance = d
def set_screen(i):
    f = S+'screen/%04d.jpg' % i
    if tx.image: bpy.data.images.remove(tx.image)
    tx.image = bpy.data.images.load(f)
    
# ---------- render
sc.render.resolution_x = 1080; sc.render.resolution_y = 1920; sc.render.resolution_percentage = int(os.environ.get('PCT', '100'))
sc.render.use_persistent_data = True
sc.view_settings.view_transform = 'Standard'  # graded in post from linear EXR
eng = os.environ.get('ENG', 'CYCLES')
if eng == 'CYCLES':
    sc.render.engine = 'CYCLES'; c = sc.cycles; c.device = 'CPU'; c.samples = int(os.environ.get('SPP', '24')); c.use_adaptive_sampling = True; c.adaptive_threshold = .04
    c.use_denoising = True; c.denoiser = 'OPENIMAGEDENOISE'; c.denoising_input_passes = 'RGB_ALBEDO_NORMAL'
    c.max_bounces = 4; c.diffuse_bounces = 2; c.glossy_bounces = 3; c.transmission_bounces = 0; c.sample_clamp_indirect = 3
    c.caustics_reflective = False; c.caustics_refractive = False
else:
    sc.render.engine = eng
    e = sc.eevee; e.taa_render_samples = int(os.environ.get('SPP', '48'))
    try:
        e.use_raytracing = True; e.use_shadows = True
    except Exception as x: print(x)
sc.render.image_settings.file_format = 'OPEN_EXR'; sc.render.image_settings.color_depth = '16'; sc.render.image_settings.exr_codec = 'DWAA'
OUT = os.environ.get('OUT', S+'rend/'); os.makedirs(OUT, exist_ok=True)
a = sys.argv[sys.argv.index('--')+1:]
frames = [int(x) for x in a[0].split(',')] if ',' in a[0] or a[0].isdigit() else list(range(*[int(x) for x in a[0].split(':')]))
if os.environ.get('SAVE'):
    for i in range(1058):
        set_cam(i/30); co.keyframe_insert('location', frame=i); co.keyframe_insert('rotation_euler', frame=i); cam.dof.keyframe_insert('focus_distance', frame=i)
    for o in [o for o in bpy.data.objects if o.type == 'FONT']:
        n = bpy.data.objects.new('txt', bpy.data.meshes.new_from_object(o.evaluated_get(bpy.context.evaluated_depsgraph_get()))); sc.collection.objects.link(n); n.parent = o.parent; n.matrix_world = o.matrix_world.copy(); bpy.data.objects.remove(o)
    for f_ in list(bpy.data.fonts): bpy.data.fonts.remove(f_)
    os.makedirs(S+'cloud', exist_ok=True); bpy.ops.wm.save_as_mainfile(filepath=S+'cloud/scene.blend', compress=True); sys.exit()
if os.environ.get('CAMS'):
    o_ = []
    for i in range(1058):
        set_cam(i/30); bpy.context.view_layer.update(); o_.append([list(r) for r in co.matrix_world])
    json.dump({'cams': o_, 'lens': cam.lens, 'lid': [list(r) for r in lid.matrix_world], 'SW': SW, 'SH': SH, 'by': by, 'W': W, 'D': D, 'H': H, 'LH': LH}, open(S+'cams.json', 'w')); sys.exit()
import time
from bpy_extras.object_utils import world_to_camera_view as wcv
for i in frames:
    f = OUT+'%04d.exr' % i
    if os.path.exists(f): continue
    set_cam(i/30); set_screen(i); bpy.context.view_layer.update()
    q = [wcv(sc, co, lid.matrix_world @ Vector(v)) for v in [(-SW/2, by+SH, .0135), (SW/2, by+SH, .0135), (SW/2, by, .0135), (-SW/2, by, .0135)]]
    json.dump([[p.x*1080, (1-p.y)*1920] for p in q], open(OUT+'%04d.json' % i, 'w'))
    t0 = time.time(); sc.render.filepath = f+'.tmp.exr'; bpy.ops.render.render(write_still=True); os.replace(f+'.tmp.exr', f)
    print('FRAME', i, round(time.time()-t0, 1), flush=True)
