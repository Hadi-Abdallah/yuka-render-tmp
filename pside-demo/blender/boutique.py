# Photoreal backdrops for the PASSION P-SIDE demo. Rendered once; products are added live in the browser.
#   SCENE=tops|bottoms|shoes RES=2048 SPP=128 OUT=out/ blender -b -P boutique.py
# tops/bottoms: square plate + camera json (fixed camera, the rail slides in WebGL)
# shoes: 360 equirect panorama from the centre of a round room (camera only rotates, so it lines up exactly)
import bpy, math, os, json, random
from mathutils import Vector
D = os.path.dirname(os.path.abspath(__file__)) + '/'
SC = os.environ.get('SCENE', 'tops'); OUT = os.environ.get('OUT', D + 'out/'); os.makedirs(OUT, exist_ok=True)
RES = int(os.environ.get('RES', '2048')); SPP = int(os.environ.get('SPP', '128'))
TX = D + 'assets-polyhaven/tex/'; ITEMS = os.environ.get('ITEMS', '')
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene; random.seed(7)

def N(nt, t, **k):
    n = nt.nodes.new(t)
    for a, b in k.items(): setattr(n, a, b)
    return n

def mat(name, col=(.5, .5, .5), rough=.5, metal=0, tex=None, scale=1., tint=(1, 1, 1), bump=.25, coat=0, rough_add=0, emit=None, es=0):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; b = nt.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*col, 1); b.inputs['Roughness'].default_value = rough; b.inputs['Metallic'].default_value = metal
    if coat: b.inputs['Coat Weight'].default_value = coat; b.inputs['Coat Roughness'].default_value = .08
    if emit: b.inputs['Emission Color'].default_value = (*emit, 1); b.inputs['Emission Strength'].default_value = es
    if tex:
        tc = N(nt, 'ShaderNodeTexCoord'); mp = N(nt, 'ShaderNodeMapping'); mp.inputs['Scale'].default_value = (scale, scale, scale)
        nt.links.new(tc.outputs['Object'], mp.inputs['Vector'])
        def im(k, cs):
            p = TX + tex + '_' + k + '.jpg'
            if not os.path.exists(p): return None
            t = N(nt, 'ShaderNodeTexImage', projection='BOX', projection_blend=.25); t.image = bpy.data.images.load(p); t.image.colorspace_settings.name = cs
            nt.links.new(mp.outputs[0], t.inputs[0]); return t
        d = im('Diffuse', 'sRGB'); r = im('Rough', 'Non-Color'); n = im('nor_gl', 'Non-Color')
        if d:
            mx = N(nt, 'ShaderNodeMix', data_type='RGBA', blend_type='MULTIPLY'); mx.inputs[0].default_value = 1; mx.inputs[7].default_value = (*tint, 1)
            nt.links.new(d.outputs[0], mx.inputs[6]); nt.links.new(mx.outputs[2], b.inputs['Base Color'])
        if r:
            ma = N(nt, 'ShaderNodeMath', operation='MULTIPLY_ADD'); ma.inputs[1].default_value = rough * 2; ma.inputs[2].default_value = rough_add
            nt.links.new(r.outputs[0], ma.inputs[0]); nt.links.new(ma.outputs[0], b.inputs['Roughness'])
        if n:
            nm = N(nt, 'ShaderNodeNormalMap'); nm.inputs['Strength'].default_value = bump; nt.links.new(n.outputs[0], nm.inputs['Color']); nt.links.new(nm.outputs[0], b.inputs['Normal'])
    return m

def obj(me, name, m, loc=(0, 0, 0), rot=(0, 0, 0)):
    o = bpy.data.objects.new(name, me); sc.collection.objects.link(o); o.location = loc; o.rotation_euler = rot
    if m: me.materials.append(m)
    return o

def box(name, s, loc, m, bev=.004, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc, rotation=rot); o = bpy.context.object; o.name = name; o.scale = s
    bpy.ops.object.transform_apply(scale=True)
    if bev:
        md = o.modifiers.new('b', 'BEVEL'); md.width = bev; md.segments = 3; md.limit_method = 'ANGLE'
    o.data.materials.append(m); [setattr(p, 'use_smooth', True) for p in o.data.polygons]; return o

def cyl(name, r, a, b, m, seg=48):
    a, b = Vector(a), Vector(b); d = b - a
    bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=d.length, vertices=seg, location=(a + b) / 2); o = bpy.context.object; o.name = name
    o.rotation_mode = 'QUATERNION'; o.rotation_quaternion = d.to_track_quat('Z', 'Y'); o.data.materials.append(m)
    [setattr(p, 'use_smooth', True) for p in o.data.polygons]; return o

def spot(name, loc, target, energy, col, size=55, blend=.85, radius=.04):
    l = bpy.data.lights.new(name, 'SPOT'); l.energy = energy; l.color = col; l.spot_size = math.radians(size); l.spot_blend = blend; l.shadow_soft_size = radius
    o = bpy.data.objects.new(name, l); sc.collection.objects.link(o); o.location = loc
    o.rotation_mode = 'QUATERNION'; o.rotation_quaternion = (Vector(target) - Vector(loc)).to_track_quat('-Z', 'Y'); return o

def area(name, loc, target, sx, sy, energy, col, spread=180):
    l = bpy.data.lights.new(name, 'AREA'); l.shape = 'RECTANGLE'; l.size = sx; l.size_y = sy; l.energy = energy; l.color = col; l.spread = math.radians(spread)
    o = bpy.data.objects.new(name, l); sc.collection.objects.link(o); o.location = loc
    o.rotation_mode = 'QUATERNION'; o.rotation_quaternion = (Vector(target) - Vector(loc)).to_track_quat('-Z', 'Y'); return o

def world(col, s):
    w = bpy.data.worlds.new('w'); sc.world = w; w.use_nodes = True; bg = w.node_tree.nodes['Background']; bg.inputs[0].default_value = (*col, 1); bg.inputs[1].default_value = s

def camera(loc, target, lens=30):
    c = bpy.data.cameras.new('cam'); c.lens = lens; c.sensor_fit = 'VERTICAL'; c.sensor_height = 36; o = bpy.data.objects.new('cam', c); sc.collection.objects.link(o)
    o.location = loc; o.rotation_mode = 'QUATERNION'; o.rotation_quaternion = (Vector(target) - Vector(loc)).to_track_quat('-Z', 'Y'); sc.camera = o
    return o, 2 * math.atan(18 / lens)

WARM = (1, .80, .60); NEUTRAL = (1, .93, .86); COOL = (.80, .88, 1)
meta = {'scene': SC}

if SC in ('tops', 'bottoms'):
    W = 7.0; H = 3.2
    if SC == 'tops':
        floor = mat('parquet', tex='herringbone_parquet', scale=1.7, tint=(.42, .34, .29), rough=.32, bump=.35, coat=.35)
        wallm = mat('plaster_dark', tex='grey_plaster_02', scale=.4, tint=(.16, .14, .13), rough=.85, bump=.5)
        slat = mat('walnut', tex='black_walnut_veneer_01', scale=1.6, tint=(.75, .62, .52), rough=.42, bump=.3, coat=.15)
        railm = mat('brass', (.80, .58, .32), .26, 1)
        box('floor', (W + 4, 7, .02), (0, -3, -.01), floor, 0)
        box('wall', (W + 4, .1, H + .2), (0, .05, H / 2), wallm, 0)
        box('ceiling', (W + 4, 7, .05), (0, -3, H + .025), mat('ceil', (.03, .03, .032), .8), 0)
        # fluted walnut panel behind the rail, with a shadow gap at top and bottom
        x = -2.95
        while x <= 2.95:
            box('slat', (.034, .028, 2.62), (x, -.014, .19 + 1.31), slat, .006); x += .046
        box('plinthband', (W + 4, .03, .12), (0, -.015, .06), mat('skirting', (.02, .02, .02), .5), .002)
        # LED cove washing down the slats
        box('cove', (6.0, .05, .03), (0, -.10, 2.93), mat('led', emit=(1, .78, .55), es=18), 0)
        area('coveL', (0, -.12, 2.92), (0, -.05, 0), 6.0, .04, 220, (1, .8, .58))
        RZ, RY, RX = 1.80, -.30, 2.45
        cyl('rail', .0145, (-RX, RY, RZ), (RX, RY, RZ), railm)
        for sx in (-1, 1):
            cyl('arm', .011, (sx * (RX - .08), -.02, RZ), (sx * (RX - .08), RY, RZ), railm)
            cyl('rose', .032, (sx * (RX - .08), 0, RZ), (sx * (RX - .08), -.02, RZ), railm)
        L = [(x_, -1.25, 3.15) for x_ in (-1.7, 0, 1.7)]
        for i, p in enumerate(L): spot('spot%d' % i, p, (p[0], 0, 1.25), 260, (1, .84, .66), 46, .9)
        area('fill', (0, -4.5, 2.2), (0, 0, 1.4), 4, 2, 60, (.85, .88, 1))
        world((.012, .011, .010), 1)
    else:
        floor = mat('concrete', tex='brushed_concrete', scale=.45, tint=(.78, .74, .70), rough=.45, bump=.3, coat=.2)
        wallm = mat('limewash', tex='clay_plaster', scale=1.1, tint=(1.0, .95, .88), rough=.9, bump=.22)
        blk = mat('steel', (.018, .018, .02), .38, 1)
        box('floor', (W + 4, 7, .02), (0, -3, -.01), floor, 0)
        box('wall', (W + 4, .1, H + .2), (0, .05, H / 2), wallm, 0)
        box('ceiling', (W + 4, 7, .05), (0, -3, H + .025), mat('ceil', (.85, .84, .82), .9), 0)
        box('reveal', (W + 4, .02, .012), (0, -.004, .10), mat('gap', (.01, .01, .01), .6), 0)
        RZ, RY, RX = 1.62, -.26, 2.45
        box('rail', (2 * RX, .022, .022), (0, RY, RZ), blk, .002)
        for sx in (-1, 1):
            box('drop', (.022, .022, H - RZ), (sx * (RX - .06), RY, (H + RZ) / 2), blk, .002)
        # low stone bench and a vase on the right, a hint of a gallery
        bench = mat('stone', tex='marble_01', scale=.8, tint=(.93, .86, .76), rough=.35, bump=.2)
        box('bench', (1.1, .42, .40), (2.05, -.45, .20), bench, .01)
        bpy.ops.mesh.primitive_uv_sphere_add(radius=.12, location=(2.25, -.45, .51), segments=48, ring_count=24); v = bpy.context.object; v.scale = (1, 1, 1.35)
        v.data.materials.append(mat('ceramic', (.12, .10, .09), .55)); [setattr(p, 'use_smooth', True) for p in v.data.polygons]
        # soft daylight from an unseen window at left, warm accent spots
        area('window', (-5.5, -1.6, 2.0), (0, -.2, 1.2), 2.2, 2.6, 3800, (.90, .94, 1.0), 120)
        L = [(x_, -1.3, 3.15) for x_ in (-1.5, 1.5)]
        for i, p in enumerate(L): spot('spot%d' % i, p, (p[0] * .7, 0, 1.0), 200, (1, .86, .70), 60, .95, .08)
        area('fill', (0, -4.5, 2.4), (0, 0, 1.3), 5, 2.5, 90, (1, .97, .94))
        world((.35, .36, .38), .25)
    cam, fov = camera((0, -3.35, 1.40), (0, 0, 1.30), 30)
    meta.update(rail={'z': RZ, 'y': RY, 'x': RX}, fov=math.degrees(fov), cam=list(cam.location), target=[0, 0, 1.30],
                lights=[list(p) for p in L], wall_y=0, floor_z=0)
    sc.render.resolution_x = sc.render.resolution_y = RES
else:
    R = 2.75; H = 3.1; PR = 1.45; NP = 8; PH = .88; PS = .40
    floor = mat('terrazzo', tex='terrazzo_tiles', scale=.9, tint=(.15, .15, .15), rough=.22, bump=.15, coat=.5)
    wallm = mat('wall', tex='clay_plaster', scale=1.0, tint=(.30, .28, .26), rough=.9, bump=.2)
    marble = mat('marble', tex='marble_01', scale=.45, tint=(.95, .94, .92), rough=.18, bump=.1, coat=.4)
    niche_back = mat('nicheback', tex='smoked_walnut_veneer', scale=1.2, tint=(.6, .5, .42), rough=.45, bump=.2)
    glass = mat('glass', (.9, .9, .9), .05); glass.node_tree.nodes['Principled BSDF'].inputs['Transmission Weight'].default_value = 1
    bpy.ops.mesh.primitive_circle_add(vertices=128, radius=R + .3, fill_type='NGON', location=(0, 0, 0)); f = bpy.context.object; f.data.materials.append(floor)
    bpy.ops.mesh.primitive_circle_add(vertices=128, radius=R + .3, fill_type='NGON', location=(0, 0, H)); c = bpy.context.object; c.data.materials.append(mat('ceil', (.025, .024, .024), .8))
    bpy.ops.mesh.primitive_cylinder_add(vertices=160, radius=R, depth=H, location=(0, 0, H / 2), end_fill_type='NOTHING'); w = bpy.context.object
    w.data.materials.append(wallm); [setattr(p, 'use_smooth', True) for p in w.data.polygons]
    for p in w.data.polygons: p.flip()
    # cove ring of light in the ceiling + small LED ring
    bpy.ops.mesh.primitive_torus_add(major_radius=1.75, minor_radius=.012, location=(0, 0, H - .02)); t = bpy.context.object
    t.data.materials.append(mat('ring', emit=(1, .86, .7), es=30))
    shoes = [p for p in ITEMS.split(',') if p]
    stock = []
    for p in shoes:
        im = bpy.data.images.load(p); m = bpy.data.materials.new('shoe'); m.use_nodes = True; nt = m.node_tree; b = nt.nodes['Principled BSDF']
        tx = N(nt, 'ShaderNodeTexImage'); tx.image = im; nt.links.new(tx.outputs['Color'], b.inputs['Base Color']); nt.links.new(tx.outputs['Alpha'], b.inputs['Alpha'])
        b.inputs['Roughness'].default_value = .5; stock.append((m, im.size[0] / im.size[1]))
    plinths = []
    for k in range(NP):
        a = k * 2 * math.pi / NP; ca, sa = math.cos(a), math.sin(a)
        # plinth faces the centre
        box('plinth%d' % k, (PS, PS, PH), (PR * ca, PR * sa, PH / 2), marble, .006, rot=(0, 0, a))
        plinths.append([PR * ca, PR * sa, PH])
        spot('pl%d' % k, (PR * .55 * ca, PR * .55 * sa, H - .05), (PR * ca, PR * sa, PH + .15), 60, (1, .88, .74), 28, .7, .05)
        # backlit wall niche with three glass shelves of shoes
        nw, nh, nz = 1.05, 1.55, 1.55; nd = .32
        cx, cy = (R - nd / 2) * ca, (R - nd / 2) * sa
        box('nb%d' % k, (nw, .03, nh), ((R - .02) * ca, (R - .02) * sa, nz), niche_back, 0, rot=(0, 0, a + math.pi / 2))
        for side in (-1, 1):
            ox, oy = -sa * side * nw / 2, ca * side * nw / 2
            box('ns', (nd, .03, nh), (cx + ox, cy + oy, nz), wallm, .003, rot=(0, 0, a))
        box('nt', (nd, nw, .03), (cx, cy, nz + nh / 2), wallm, .003, rot=(0, 0, a)); box('nbt', (nd, nw, .03), (cx, cy, nz - nh / 2), wallm, .003, rot=(0, 0, a))
        box('led', (.02, nw - .06, .012), ((R - nd + .03) * ca, (R - nd + .03) * sa, nz + nh / 2 - .03), mat('nled', emit=(1, .85, .68), es=25), 0, rot=(0, 0, a))
        area('nl%d' % k, ((R - nd / 2) * ca, (R - nd / 2) * sa, nz + nh / 2 - .05), ((R - nd / 2) * ca, (R - nd / 2) * sa, 0), .25, nw - .1, 40, (1, .86, .70))
        for j, sz in enumerate((nz - .42, nz + .08)):
            box('shelf', (nd - .04, nw - .06, .012), (cx, cy, sz), glass, .002, rot=(0, 0, a))
            if stock:
                for q in (-1, 1):
                    m, asp = random.choice(stock); h_ = .13; w_ = h_ * asp
                    if w_ > .30: w_ = .30; h_ = w_ / asp
                    bpy.ops.mesh.primitive_plane_add(size=1, location=(cx - sa * q * .22 + ca * .02, cy + ca * q * .22 + sa * .02, sz + .006 + h_ / 2), rotation=(math.pi / 2, 0, a + math.pi / 2))
                    s = bpy.context.object; s.scale = (w_, h_, 1); s.data.materials.append(m)
    area('fill', (0, 0, H - .1), (0, 0, 0), 2.0, 2.0, 120, (1, .92, .84))
    world((.01, .01, .012), 1)
    cam = bpy.data.cameras.new('cam'); cam.type = 'PANO'
    try: cam.panorama_type = 'EQUIRECTANGULAR'
    except Exception: cam.cycles.panorama_type = 'EQUIRECTANGULAR'
    co = bpy.data.objects.new('cam', cam); sc.collection.objects.link(co); co.location = (0, 0, 1.28); co.rotation_euler = (math.pi / 2, 0, -math.pi / 2); sc.camera = co
    meta.update(eye=[0, 0, 1.28], plinths=plinths, plinth_size=PS, yaw_offset_deg=0)
    sc.render.resolution_x = RES; sc.render.resolution_y = RES // 2

sc.render.engine = 'CYCLES'; c = sc.cycles; c.device = 'CPU'; c.samples = SPP; c.use_adaptive_sampling = True; c.adaptive_threshold = .02
c.use_denoising = True; c.denoiser = 'OPENIMAGEDENOISE'; c.max_bounces = 6; c.sample_clamp_indirect = 4
sc.view_settings.view_transform = 'AgX'; sc.view_settings.look = 'AgX - Medium High Contrast'
sc.render.image_settings.file_format = 'JPEG'; sc.render.image_settings.quality = 92; sc.render.resolution_percentage = 100
sc.render.filepath = OUT + SC + '.jpg'; bpy.ops.render.render(write_still=True)
json.dump(meta, open(OUT + SC + '.json', 'w'), indent=1); print('DONE', SC, meta)
