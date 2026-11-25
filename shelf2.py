# real spines cut from photographs of the sets
import json
MT = json.load(open(S+'bk/meta.json')); AW = MT['W']
def spine_mat():
    m = bpy.data.materials.new('spine'); m.use_nodes = True; nt = m.node_tree; b = nt.nodes['Principled BSDF']
    def im(f, cs):
        n = N(nt, 'ShaderNodeTexImage', interpolation='Cubic'); n.image = bpy.data.images.load(S+'bk/'+f, check_existing=True); n.image.colorspace_settings.name = cs; return n
    c = im('atlas.png', 'sRGB'); k = im('gold.png', 'Non-Color'); hs = N(nt, 'ShaderNodeHueSaturation'); hs.inputs['Value'].default_value = .78; hs.inputs['Saturation'].default_value = .96; nt.links.new(c.outputs[0], hs.inputs['Color']); nt.links.new(hs.outputs[0], b.inputs['Base Color'])
    mt = N(nt, 'ShaderNodeMath', operation='MULTIPLY'); mt.inputs[1].default_value = .42; nt.links.new(k.outputs[0], mt.inputs[0]); nt.links.new(mt.outputs[0], b.inputs['Metallic']); r = N(nt, 'ShaderNodeMapRange'); r.inputs['To Min'].default_value = .40; r.inputs['To Max'].default_value = .26; nt.links.new(k.outputs[0], r.inputs[0]); nt.links.new(r.outputs[0], b.inputs['Roughness'])
    tc = N(nt, 'ShaderNodeTexCoord'); n = N(nt, 'ShaderNodeTexNoise'); n.inputs['Scale'].default_value = 34; n.inputs['Detail'].default_value = 5; nt.links.new(tc.outputs['Object'], n.inputs['Vector']); h_ = N(nt, 'ShaderNodeMath', operation='MULTIPLY_ADD'); h_.inputs[1].default_value = .6; nt.links.new(k.outputs[0], h_.inputs[0]); nt.links.new(n.outputs['Fac'], h_.inputs[2]); bp = N(nt, 'ShaderNodeBump'); bp.inputs['Strength'].default_value = .18; bp.inputs['Distance'].default_value = .02; nt.links.new(h_.outputs[0], bp.inputs['Height']); nt.links.new(bp.outputs[0], b.inputs['Normal']); return m
M_SPINE = spine_mat(); CV = {'fath': mat('cvf', (.030, .010, .011), .42, bump=.35, bscale=60), 'x': mat('cvx', (.008, .008, .010), .40, bump=.35, bscale=60)}
M_PAGE = bpy.data.materials.new('pages'); M_PAGE.use_nodes = True; nt = M_PAGE.node_tree; b = nt.nodes['Principled BSDF']; tc = N(nt, 'ShaderNodeTexCoord'); mp = N(nt, 'ShaderNodeMapping'); mp.inputs['Scale'].default_value = (90, 1.5, 1.5); n = N(nt, 'ShaderNodeTexNoise'); n.inputs['Scale'].default_value = 1.6; n.inputs['Detail'].default_value = 4; nt.links.new(tc.outputs['Object'], mp.inputs[0]); nt.links.new(mp.outputs[0], n.inputs['Vector']); cr = N(nt, 'ShaderNodeValToRGB'); cr.color_ramp.elements[0].position = .35; cr.color_ramp.elements[0].color = (.40, .34, .25, 1); cr.color_ramp.elements[1].position = .65; cr.color_ramp.elements[1].color = (.66, .60, .48, 1); nt.links.new(n.outputs['Fac'], cr.inputs[0]); nt.links.new(cr.outputs[0], b.inputs['Base Color']); b.inputs['Roughness'].default_value = .85
def book(key, i, h_, d_, x_, y_, z_, lean=0., yaw_=0.):
    px, pw = MT['s'][key][i]; w_ = pw/MT['H']*h_; e = bpy.data.objects.new('bk', None); sc.collection.objects.link(e); e.location = (x_+w_/2, y_, z_); e.rotation_euler = (0, lean, yaw_); cm = CV.get(key, CV['x']); t_ = .030
    for sx in (-1, 1): box('bd', t_, d_, h_, (sx*(w_/2-t_/2), d_/2, h_/2), cm, .010, 3, e)
    box('pg', w_-2*t_, d_-.07, h_-.10, (0, d_/2-.02, h_/2), M_PAGE, 0, parent=e)
    bm = bmesh.new(); uvl = bm.loops.layers.uv.new(); n_ = 18; zs = [0, .02, .06, .5, h_-.5, h_-.06, h_-.02, h_]; grid = []
    for z2 in zs:
        pull = .010*max(0, 1-min(z2, h_-z2)/.03); rw = []
        for k in range(n_+1):
            a_ = (k/n_-.5)*2; rw.append(bm.verts.new((a_*w_/2, -(.060-pull)*(1-abs(a_)**2.4), z2)))
        grid.append(rw)
    for j in range(len(zs)-1):
        for k in range(n_):
            f_ = bm.faces.new((grid[j][k], grid[j][k+1], grid[j+1][k+1], grid[j+1][k]))
            for lp_, (u, zz) in zip(f_.loops, ((k/n_, zs[j]), ((k+1)/n_, zs[j]), ((k+1)/n_, zs[j+1]), (k/n_, zs[j+1]))): lp_[uvl].uv = ((px+1+u*(pw-2))/AW, zz/h_)
    me_ = bpy.data.meshes.new('sp'); bm.to_mesh(me_); bm.free(); link(me_, 'sp', M_SPINE, True, e); return w_
def wid(key, idx, h_): return sum(MT['s'][key][i][1]/MT['H']*h_ for i in idx)
def row(key, x0, z_, h_, d_=1.75, idx=None, gap=.010, dy=0.):
    for i in (idx if idx is not None else range(len(MT['s'][key]))): x0 += book(key, i, h_, d_, x0, SY-SD/2+.30+dy+random.uniform(0, .07), z_, random.uniform(-.003, .003), random.uniform(-.010, .010))+gap
    return x0
Z = {k: ZS[k]+.12 for k in range(len(ZS))}; L0 = X0+.12; R0 = (X0+X1)/2+.12
row('fatawa', L0+.06, Z[2], 2.42)
x_ = row('bukhari', L0+.10, Z[3], 2.46, idx=[2, 1, 0]); row('fath', x_+.05, Z[3], 2.52)
x_ = row('umda', L0+.25, Z[1], 2.42); x_ = row('sunna', x_+.02, Z[1], 2.40); x_ = row('khallal', x_+.02, Z[1], 2.38); book('bukhari', 3, 2.42, 1.7, x_+.14, SY-SD/2+.36, Z[1], -.085)
x_ = row('bukhari', R0+.10, Z[2], 2.46, idx=[4, 3, 2, 1, 0]); row('umda', x_+.03, Z[2], 2.42)
x_ = row('sunna', R0+.12, Z[3], 2.40); x_ = row('khallal', x_+.02, Z[3], 2.38); row('umda', x_+.02, Z[3], 2.42); row('fath', R0+.15, Z[1], 2.50)
