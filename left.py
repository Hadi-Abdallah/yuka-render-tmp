# what stands on the left, in front of the slats. LEFT = none | chair | frame | curtain | jacket
LEFT = os.environ.get('LEFT', 'none')
if LEFT == 'chair':
    place(load('modern_arm_chair_01'), (-3.35, WY-5.0, FZ), math.radians(24), 10.0)
elif LEFT == 'frame':
    e = bpy.data.objects.new('fr', None); sc.collection.objects.link(e); e.location = (-2.75, WY+.02, 4.6); FW, FH = 2.5, 3.3
    for sx in (-1, 1): box('f', .22, .30, FH, (sx*(FW/2-.11), -.12, 0), M_BLACKF if 'M_BLACKF' in globals() else mat('ff', (.012, .011, .011), .35, coat=.3), .02, 3, e)
    for sz in (-1, 1): box('f', FW, .30, .22, (0, -.12, sz*(FH/2-.11)), mat('ff2', (.012, .011, .011), .35, coat=.3), .02, 3, e)
    box('paper', FW-.3, .03, FH-.3, (0, -.02, 0), mat('mt', (.60, .57, .52), .85), 0, parent=e)
    m = bpy.data.materials.new('call'); m.use_nodes = True; nt = m.node_tree; b = nt.nodes['Principled BSDF']; tx_ = N(nt, 'ShaderNodeTexImage'); tx_.image = bpy.data.images.load(S+'bk/call.png'); nt.links.new(tx_.outputs[0], b.inputs['Base Color']); b.inputs['Roughness'].default_value = .7
    me_ = bpy.data.meshes.new('art'); aw, ah = FW-.80, FH-.95; me_.from_pydata([(-aw/2, -.045, -ah/2), (aw/2, -.045, -ah/2), (aw/2, -.045, ah/2), (-aw/2, -.045, ah/2)], [], [(0, 1, 2, 3)]); uv_ = me_.uv_layers.new()
    for i_, c_ in enumerate([(0, 0), (1, 0), (1, 1), (0, 1)]): uv_.data[i_].uv = c_
    link(me_, 'art', m, False, e)
    area('frl', (-2.75, WY-2.4, 7.6), (-2.75, WY, 4.6), 1.0, 34, (1, .80, .58), .4, 90)
elif LEFT == 'curtain':
    bm = bmesh.new(); n_ = 420; A_ = []; B_ = []
    for k in range(n_+1):
        u = k/n_; xx = -13+u*10.9; a_ = u*54*math.pi; w1 = .26*math.sin(a_)+.09*math.sin(a_*.47+1.2)+.05*math.sin(a_*2.1); A_.append(bm.verts.new((xx+.08*math.cos(a_), WY-1.0+w1*.9, FZ+.2))); B_.append(bm.verts.new((xx+.04*math.cos(a_), WY-1.0+w1*.55, 20)))
    for k in range(n_): bm.faces.new((A_[k], A_[k+1], B_[k+1], B_[k]))
    me_ = bpy.data.meshes.new('cur'); bm.to_mesh(me_); bm.free(); mc = mat('cur', (.055, .055, .075), .9, bump=.5, bscale=90); mc.node_tree.nodes['Principled BSDF'].inputs['Sheen Weight'].default_value = .4; link(me_, 'cur', mc, True)
elif LEFT == 'jacket':
    place(load('mid_century_lounge_chair'), (-4.4, WY-5.0, FZ), math.radians(32), 10.0)
