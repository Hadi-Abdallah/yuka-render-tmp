import bpy, sys, os, time
S = os.path.dirname(os.path.abspath(__file__))+'/'
sc = bpy.context.scene; job, n = map(int, sys.argv[sys.argv.index('--')+1:][:2]); out = os.environ.get('OUT', S+'new/'); os.makedirs(out, exist_ok=True)
T = {k: [x for x in bpy.data.materials[k].node_tree.nodes if x.type == 'TEX_IMAGE'][0] for k in ('pscreen', 'lscreen')}
B = [(i, [x for x in bpy.data.materials[k].node_tree.nodes if x.label == 'BAND'][0]) for i, k in enumerate(('pscreen', 'lscreen'))]
sc.cycles.device = 'CPU'; sc.cycles.samples = int(os.environ.get('SPP', '14')); sc.render.resolution_percentage = int(os.environ.get('PCT', '100'))
for f in list(range(648))[job::n]:
    p = out+'%04d.exr' % f
    if os.path.exists(p): continue
    sc.frame_set(f)
    for k, d in (('pscreen', 'phone'), ('lscreen', 'laptop')):
        im = T[k].image; T[k].image = bpy.data.images.load(S+'%s/%04d.jpg' % (d, f+1));
        if im: bpy.data.images.remove(im)
    for i, nd in B: nd.inputs[1].default_value = f*(6.283185307*22/648)+i*2
    t = time.time(); sc.render.filepath = p; bpy.ops.render.render(write_still=True); print('FRAME', f, round(time.time()-t, 1), flush=True)
