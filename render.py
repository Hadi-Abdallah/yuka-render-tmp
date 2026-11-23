import bpy, sys, os, time
S = os.path.dirname(os.path.abspath(__file__))+'/'
sc = bpy.context.scene; job, n = map(int, sys.argv[sys.argv.index('--')+1:][:2])
fr = [f for f in list(range(0, 1051, 10))+[1057] if not os.path.exists(S+'rend/%04d.exr' % f)]
out = os.environ.get('OUT', S+'new/'); os.makedirs(out, exist_ok=True)
nt = bpy.data.objects['screen'].data.materials[0].node_tree
tx = [x for x in nt.nodes if x.type == 'TEX_IMAGE'][0]
sc.render.resolution_percentage = int(os.environ.get('PCT', '100')); sc.cycles.device = 'CPU'
for f in fr[job::n]:
    sc.frame_set(f); tx.image = bpy.data.images.load(S+'screen/%04d.jpg' % f)
    t = time.time(); sc.render.filepath = out+'%04d.exr' % f; bpy.ops.render.render(write_still=True); print('FRAME', f, time.time()-t, flush=True)
