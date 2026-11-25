# stoneware mug with a cappuccino. 1 unit = 10 cm
def lathe(prof, m, name, seg=128, loc=(0, 0, 0)):
    bm = bmesh.new(); vs = [bm.verts.new((r_, 0, z_)) for r_, z_ in prof]; es = [bm.edges.new((vs[i], vs[i+1])) for i in range(len(vs)-1)]
    bmesh.ops.spin(bm, geom=vs+es, cent=(0, 0, 0), axis=(0, 0, 1), angle=2*math.pi, steps=seg); bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=.0004); bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me_ = bpy.data.meshes.new(name); bm.to_mesh(me_); bm.free(); return link(me_, name, m, True, None, loc)
MH = .93
out_ = [(.0, .014), (.285, .014), (.305, .0), (.328, .0), (.345, .015), (.376, .048), (.394, .100), (.4005, .18), (.4015, .40), (.4020, .66), (.4035, .89)]
rim_ = [(.4040, .914), (.4005, .927), (.3930, .932), (.3850, .928), (.3800, .917)]
in_ = [(.3755, .86), (.3745, .60), (.3735, .25), (.358, .108), (.31, .062), (.0, .052)]
def smooth_prof(p, n=5):
    r_ = []
    for i in range(len(p)-1):
        p0, p1, p2, p3 = p[max(0, i-1)], p[i], p[i+1], p[min(len(p)-1, i+2)]
        for k in range(n):
            t_ = k/n; r_.append(tuple(.5*((2*p1[a])+(-p0[a]+p2[a])*t_+(2*p0[a]-5*p1[a]+4*p2[a]-p3[a])*t_*t_+(-p0[a]+3*p1[a]-3*p2[a]+p3[a])*t_**3) for a in (0, 1)))
    return r_+[p[-1]]
body = lathe(smooth_prof(out_+rim_+in_), None or mat('tmp', (1, 1, 1)), 'mugb')
# handle: swept oval, buried in the wall, then everything remeshed so the joint has a real fillet
hp_ = [(.370, .770), (.455, .792), (.575, .768), (.655, .680), (.672, .540), (.640, .390), (.555, .272), (.455, .208), (.370, .186)]
hp_ = smooth_prof(hp_, 6); bm = bmesh.new(); rings = []
for i, (x_, z_) in enumerate(hp_):
    a_ = Vector(hp_[max(0, i-1)]); b_ = Vector(hp_[min(len(hp_)-1, i+1)]); t_ = (b_-a_).normalized(); n2 = Vector((-t_.y, t_.x)); f_ = abs(i/(len(hp_)-1)-.5)*2; ra, rb = .036+.014*f_**3, .066+.022*f_**3
    rings.append([bm.verts.new((x_+n2.x*ra*math.cos(q), rb*math.sin(q), z_+n2.y*ra*math.cos(q))) for q in [2*math.pi*k/20 for k in range(20)]])
for A_, B_ in zip(rings, rings[1:]):
    for k in range(20): bm.faces.new((A_[k], A_[(k+1) % 20], B_[(k+1) % 20], B_[k]))
bm.faces.new(rings[0][::-1]); bm.faces.new(rings[-1]); bmesh.ops.recalc_face_normals(bm, faces=bm.faces); bm.from_mesh(body.data); me_ = bpy.data.meshes.new('mug'); bm.to_mesh(me_); bm.free(); bpy.data.objects.remove(body)
MUGV = int(os.environ.get('MUGV', '2'))
def glaze():
    """gloss black outside, white inside, white screen print of the shahada (thuluth) facing the lens"""
    m = bpy.data.materials.new('glaze'); m.use_nodes = True; nt = m.node_tree; b = nt.nodes['Principled BSDF']; tc = N(nt, 'ShaderNodeTexCoord'); sp = N(nt, 'ShaderNodeSeparateXYZ'); nt.links.new(tc.outputs['Object'], sp.inputs[0])
    def mt(op, a_, b_=0, c_=0):
        q = N(nt, 'ShaderNodeMath', operation=op)
        for k_, v_ in enumerate((a_, b_, c_)):
            if isinstance(v_, (int, float)): q.inputs[k_].default_value = v_
            else: nt.links.new(v_, q.inputs[k_])
        return q.outputs[0]
    n = N(nt, 'ShaderNodeTexNoise'); n.inputs['Scale'].default_value = 2.6; n.inputs['Detail'].default_value = 6; nt.links.new(tc.outputs['Object'], n.inputs['Vector'])
    rad = mt('SQRT', mt('ADD', mt('MULTIPLY', sp.outputs[0], sp.outputs[0]), mt('MULTIPLY', sp.outputs[1], sp.outputs[1])))
    ang = mt('ARCTAN2', mt('SUBTRACT', mt('MULTIPLY', sp.outputs[1], math.cos(DEC)), mt('MULTIPLY', sp.outputs[0], math.sin(DEC))), mt('ADD', mt('MULTIPLY', sp.outputs[0], math.cos(DEC)), mt('MULTIPLY', sp.outputs[1], math.sin(DEC))))
    u = mt('ADD', mt('DIVIDE', ang, 2*HALF), .5); v = mt('ADD', mt('DIVIDE', mt('SUBTRACT', sp.outputs[2], .480), .402*2*HALF*742/2000), .5); cb = N(nt, 'ShaderNodeCombineXYZ'); nt.links.new(u, cb.inputs[0]); nt.links.new(v, cb.inputs[1])
    tx_ = N(nt, 'ShaderNodeTexImage', interpolation='Cubic', extension='CLIP'); tx_.image = bpy.data.images.load(S+'sh/shahada.png', check_existing=True); tx_.image.colorspace_settings.name = 'Non-Color'; nt.links.new(cb.outputs[0], tx_.inputs[0])
    outside = mt('GREATER_THAN', rad, .3915); pw_ = N(nt, 'ShaderNodeTexNoise'); pw_.inputs['Scale'].default_value = 26; pw_.inputs['Detail'].default_value = 6; nt.links.new(tc.outputs['Object'], pw_.inputs['Vector']); dm = mt('MULTIPLY', mt('MULTIPLY', tx_.outputs[0], outside), mt('SUBTRACT', 1, mt('MULTIPLY', mt('GREATER_THAN', pw_.outputs['Fac'], (2, .70, .70, .665)[MUGV-1]), .8)))
    inner = mt('MULTIPLY', mt('LESS_THAN', rad, .3815), mt('GREATER_THAN', sp.outputs[2], .20))
    # the white glaze rolls over the lip a little
    lipn = mt('GREATER_THAN', mt('ADD', sp.outputs[2], mt('MULTIPLY', n.outputs['Fac'], .006)), .9335)
    c1 = N(nt, 'ShaderNodeMix', data_type='RGBA'); nt.links.new(mt('MAXIMUM', inner, mt('MULTIPLY', lipn, mt('LESS_THAN', rad, .391))), c1.inputs[0]); c1.inputs[6].default_value = (.0065, .0065, .0072, 1); c1.inputs[7].default_value = (.64, .625, .60, 1)
    c2 = N(nt, 'ShaderNodeMix', data_type='RGBA'); nt.links.new(dm, c2.inputs[0]); nt.links.new(c1.outputs[2], c2.inputs[6]); c2.inputs[7].default_value = (.66, .655, .64, 1)
    # unglazed foot
    ft = mt('LESS_THAN', sp.outputs[2], .008); c3 = N(nt, 'ShaderNodeMix', data_type='RGBA'); nt.links.new(ft, c3.inputs[0]); nt.links.new(c2.outputs[2], c3.inputs[6]); c3.inputs[7].default_value = (.36, .33, .29, 1)
    # what is left of the coffee: a thin tan film between the old level and the new one, a dark tide line, a few runs
    th = mt('ARCTAN2', sp.outputs[1], sp.outputs[0]); su = mt('FRACT', mt('DIVIDE', mt('ADD', th, MROT+4*math.pi), 2*math.pi)); cs = N(nt, 'ShaderNodeCombineXYZ'); nt.links.new(su, cs.inputs[0]); nt.links.new(mt('DIVIDE', sp.outputs[2], .93), cs.inputs[1])
    st_ = N(nt, 'ShaderNodeTexImage', interpolation='Cubic', extension='EXTEND'); st_.image = bpy.data.images.load(S+'sh/stain.png', check_existing=True); st_.image.colorspace_settings.name = 'Non-Color'; nt.links.new(cs.outputs[0], st_.inputs[0]); film = mt('MULTIPLY', st_.outputs[0], mt('MAXIMUM', inner, mt('MULTIPLY', mt('GREATER_THAN', sp.outputs[2], .905), mt('LESS_THAN', rad, .400))))
    # thin = honey, thick = nearly black
    dk = N(nt, 'ShaderNodeValToRGB'); e_ = dk.color_ramp.elements; e_[0].position = 0; e_[0].color = (1, 1, 1, 1); e_[1].position = 1; e_[1].color = (.035, .010, .003, 1)
    for p_, c_ in ((.10, (.93, .84, .68, 1)), (.28, (.74, .52, .28, 1)), (.55, (.34, .145, .045, 1))): x_ = e_.new(p_); x_.color = c_
    nt.links.new(film, dk.inputs[0]); c4 = N(nt, 'ShaderNodeMix', data_type='RGBA', blend_type='MULTIPLY'); c4.inputs[0].default_value = 1; nt.links.new(c3.outputs[2], c4.inputs[6]); nt.links.new(dk.outputs[0], c4.inputs[7]); nt.links.new(c4.outputs[2], b.inputs['Base Color'])
    wt = N(nt, 'ShaderNodeTexImage', interpolation='Cubic', extension='EXTEND'); wt.image = bpy.data.images.load(S+'sh/mugw.png', check_existing=True); wt.image.colorspace_settings.name = 'Non-Color'; nt.links.new(cs.outputs[0], wt.inputs[0]); wr = N(nt, 'ShaderNodeSeparateColor'); nt.links.new(wt.outputs[0], wr.inputs[0])
    gre = mt('MULTIPLY', mt('MULTIPLY', wr.outputs[0], outside), (.75, .95, .95, .95)[MUGV-1]); scr_ = mt('MULTIPLY', mt('MULTIPLY', wr.outputs[1], outside), (0, .55, .55, .85)[MUGV-1]); dry = mt('MULTIPLY', mt('MULTIPLY', wr.outputs[2], mt('GREATER_THAN', rad, .388)), (0, 0, .85, .60)[MUGV-1])
    c4b = N(nt, 'ShaderNodeMix', data_type='RGBA'); nt.links.new(mt('MULTIPLY', gre, (.40, .55, .55, .62)[MUGV-1]), c4b.inputs[0]); nt.links.new(c4.outputs[2], c4b.inputs[6]); c4b.inputs[7].default_value = (.058, .057, .060, 1); c4 = c4b
    # grey hairline wear, then dried coffee, over everything
    c5 = N(nt, 'ShaderNodeMix', data_type='RGBA'); nt.links.new(mt('MULTIPLY', scr_, .75), c5.inputs[0]); nt.links.new(c4.outputs[2], c5.inputs[6]); c5.inputs[7].default_value = (.16, .16, .165, 1)
    c6 = N(nt, 'ShaderNodeMix', data_type='RGBA'); nt.links.new(dry, c6.inputs[0]); nt.links.new(c5.outputs[2], c6.inputs[6]); c6.inputs[7].default_value = (.200, .098, .042, 1)
    # dust that settles, a breath of grey
    du = N(nt, 'ShaderNodeTexNoise'); du.inputs['Scale'].default_value = 95; du.inputs['Detail'].default_value = 2; nt.links.new(tc.outputs['Object'], du.inputs['Vector']); dsp = mt('MULTIPLY', mt('MULTIPLY', mt('GREATER_THAN', du.outputs['Fac'], .735), outside), (.25, .35, .35, .45)[MUGV-1]); c7 = N(nt, 'ShaderNodeMix', data_type='RGBA'); nt.links.new(dsp, c7.inputs[0]); nt.links.new(c6.outputs[2], c7.inputs[6]); c7.inputs[7].default_value = (.36, .36, .37, 1)
    # worn lip: the black glaze is thinner where it is drunk from
    c8 = N(nt, 'ShaderNodeMix', data_type='RGBA'); lw_ = mt('MULTIPLY', mt('MULTIPLY', mt('GREATER_THAN', sp.outputs[2], .921), mt('GREATER_THAN', rad, .386)), mt('MULTIPLY', mt('MAXIMUM', mt('SUBTRACT', n.outputs['Fac'], .44), 0), (0, 1.4, 1.4, 3.2)[MUGV-1])); nt.links.new(lw_, c8.inputs[0]); nt.links.new(c7.outputs[2], c8.inputs[6]); c8.inputs[7].default_value = (.20, .15, .12, 1); nt.links.new(c8.outputs[2], b.inputs['Base Color'])
    ro = N(nt, 'ShaderNodeMapRange'); ro.inputs['From Min'].default_value = .35; ro.inputs['From Max'].default_value = .7; ro.inputs['To Min'].default_value = .085; ro.inputs['To Max'].default_value = .17; nt.links.new(n.outputs['Fac'], ro.inputs[0]); nt.links.new(mt('ADD', mt('ADD', ro.outputs[0], mt('MULTIPLY', dm, .22)), mt('ADD', mt('MULTIPLY', ft, .6), mt('ADD', mt('MULTIPLY', gre, .55), mt('ADD', mt('MULTIPLY', scr_, .3), mt('MULTIPLY', dry, .30))))), b.inputs['Roughness'])
    nb = N(nt, 'ShaderNodeTexNoise'); nb.inputs['Scale'].default_value = 4.5; nb.inputs['Detail'].default_value = 2; nt.links.new(tc.outputs['Object'], nb.inputs['Vector']); bp = N(nt, 'ShaderNodeBump'); bp.inputs['Strength'].default_value = .07; bp.inputs['Distance'].default_value = .03; nt.links.new(mt('ADD', nb.outputs['Fac'], mt('MULTIPLY', dm, .02)), bp.inputs['Height']); nt.links.new(bp.outputs[0], b.inputs['Normal']); return m
CZ = .708; OLD_ = .826; MROT = math.radians(-176); DEC = math.radians(-86)-MROT; HALF = math.radians(60)
mug = link(me_, 'mug', glaze(), True, None, (MUG[0], MUG[1], DZ+.001)); mug.rotation_euler = (0, 0, MROT)
q = mug.modifiers.new('r', 'REMESH'); q.mode = 'VOXEL'; q.voxel_size = .0075; q.use_smooth_shade = True; q = mug.modifiers.new('s', 'SMOOTH'); q.factor = .5; q.iterations = 7
# black coffee: a clear dark liquid, so the surface mirrors the room; thin amber where it meets the wall; a few real bubbles
def coffee():
    m = bpy.data.materials.new('coffee'); m.use_nodes = True; nt = m.node_tree; b = nt.nodes['Principled BSDF']; tc = N(nt, 'ShaderNodeTexCoord'); ln = N(nt, 'ShaderNodeVectorMath', operation='LENGTH'); nt.links.new(tc.outputs['Object'], ln.inputs[0])
    cr = N(nt, 'ShaderNodeValToRGB'); e_ = cr.color_ramp.elements; e_[0].position = .78; e_[0].color = (.0055, .0020, .0008, 1); e_[1].position = 1.0; e_[1].color = (.16, .062, .016, 1); x_ = e_.new(.93); x_.color = (.030, .010, .003, 1); d_ = N(nt, 'ShaderNodeMath', operation='DIVIDE'); d_.inputs[1].default_value = .3745; nt.links.new(ln.outputs['Value'], d_.inputs[0]); nt.links.new(d_.outputs[0], cr.inputs[0])
    nt.links.new(cr.outputs[0], b.inputs['Base Color']); b.inputs['Roughness'].default_value = .025; b.inputs['IOR'].default_value = 1.34; b.inputs['Specular IOR Level'].default_value = .5
    n = N(nt, 'ShaderNodeTexNoise'); n.inputs['Scale'].default_value = 2.2; nt.links.new(tc.outputs['Object'], n.inputs['Vector']); bp = N(nt, 'ShaderNodeBump'); bp.inputs['Strength'].default_value = .02; bp.inputs['Distance'].default_value = .02; nt.links.new(n.outputs['Fac'], bp.inputs['Height']); nt.links.new(bp.outputs[0], b.inputs['Normal']); return m
CX, CY = MUG; lathe([(.0, 0), (.20, .0), (.330, .0004), (.357, .0035), (.368, .010), (.3742, .021)], coffee(), 'coffee', 96, (CX, CY, DZ+CZ))
if MUGV >= 3:
    me_ = bpy.data.meshes.new('cring'); me_.from_pydata([(-.5, -.5, 0), (.5, -.5, 0), (.5, .5, 0), (-.5, .5, 0)], [], [(0, 1, 2, 3)]); uv_ = me_.uv_layers.new()
    for i_, c_ in enumerate([(0, 0), (1, 0), (1, 1), (0, 1)]): uv_.data[i_].uv = c_
    mr_ = bpy.data.materials.new('cring'); mr_.use_nodes = True; nt = mr_.node_tree; b = nt.nodes['Principled BSDF']; t_ = N(nt, 'ShaderNodeTexImage'); t_.image = bpy.data.images.load(S+'sh/ring.png', check_existing=True); t_.image.colorspace_settings.name = 'Non-Color'; k_ = N(nt, 'ShaderNodeMath', operation='MULTIPLY'); k_.inputs[1].default_value = .88; nt.links.new(t_.outputs[0], k_.inputs[0]); nt.links.new(k_.outputs[0], b.inputs['Alpha']); b.inputs['Base Color'].default_value = (.022, .009, .004, 1); b.inputs['Roughness'].default_value = .22
    link(me_, 'cring', mr_, False, None, (CX+.24, CY-.42, DZ+.0016))
M_BUB = bpy.data.materials.new('bub'); M_BUB.use_nodes = True; bb = M_BUB.node_tree.nodes['Principled BSDF']; bb.inputs['Base Color'].default_value = (.20, .105, .045, 1); bb.inputs['Roughness'].default_value = .06; bb.inputs['Alpha'].default_value = .45
for k in range(34):
    a_ = random.gauss(2.2, .55) if k < 22 else random.uniform(0, 6.28); r_ = random.uniform(.004, .013)*(1 if k < 28 else 1.5); q_ = .362-r_*.8-abs(random.gauss(0, .012)); s_ = sphere(r_, (CX+q_*math.cos(a_), CY+q_*math.sin(a_), DZ+CZ+.004), M_BUB, 14); s_.scale = (1, 1, .55)
