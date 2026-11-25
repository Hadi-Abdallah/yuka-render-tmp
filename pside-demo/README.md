# Passion P-Side showroom demo

- `tool/process.py` - one ordinary product photo -> cut-out (.webp) + relief map (_depth.png) + json. Free, open models (rembg/BiRefNet, Depth Anything V2 Small). Tops lose the photo's hanger automatically.
- `tool/pano_view.py` - still image from the shoe-room panorama (placeholder before WebGL loads).
- `blender/boutique.py` - renders the rooms once (SCENE=tops|bottoms|shoes). Needs Poly Haven textures: `python ../../dl.py "" herringbone_parquet,marble_01,clay_plaster,grey_plaster_02,terrazzo_tiles,smoked_walnut_veneer,black_walnut_veneer_01,brushed_concrete` from this folder.
- `site/index.html` - the page (three.js). Expects `items/`, `plates/` and `how/` next to it (not committed: sample photos are third-party).
