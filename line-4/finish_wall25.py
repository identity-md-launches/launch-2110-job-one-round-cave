"""One-shot composite of image-tool pigment; preserve every ancestor pixel elsewhere.

Requires the inherited wall.png and the generated pictograph in wall-v7.png.
Only the two required wall PNGs and the numbered JPEG are written.
"""
import ctypes
import hashlib
import importlib.util
import json
from pathlib import Path

spec = importlib.util.spec_from_file_location('png_codec', Path(__file__).with_name('finish_wall22.py'))
codec = importlib.util.module_from_spec(spec)
spec.loader.exec_module(codec)
ancestor = Path('artifacts/line-4/wall.png')
output = Path('artifacts/line-4/wall-v7.png')
old_sha = hashlib.sha256(ancestor.read_bytes()).hexdigest()
assert old_sha == 'a1743f337cb5aa4ffd350818fc8c165a233147726d90bf77fb2c9b24be4c410f', 'expected ancestor; never apply twice'
w, h, original = codec.read_png(ancestor)
dw, dh, pigment = codec.read_png(output)
assert (w, h) == (1254, 1254)
assert (dw, dh) == (1024, 1024)
final = original[:]
# This unused area is above all earlier paintings and clear of Pepe's head.
x0, y0, x1, y1 = 750, 250, 1005, 369
sx0, sy0, sx1, sy1 = 40, 280, 970, 715
changed = 0
for y in range(y0, y1):
    for x in range(x0, x1):
        weight = 0.0
        color = [0.0, 0.0, 0.0]
        # Four area samples remove the pale source background without drawing
        # replacement rock. Only the image tool's actual pigment is retained.
        for dy in (.25, .75):
            for dx in (.25, .75):
                sx = int(sx0 + (x-x0+dx)*(sx1-sx0)/(x1-x0))
                sy = int(sy0 + (y-y0+dy)*(sy1-sy0)/(y1-y0))
                at = (sy*dw+sx)*3
                rgb = pigment[at:at+3]
                opacity = .72 * max(0, min(1, (220-min(rgb))/130))
                weight += opacity/4
                for c in range(3):
                    color[c] += rgb[c]*opacity/4
        if weight:
            at = (y*w+x)*3
            for c in range(3):
                final[at+c] = round(original[at+c]*(1-weight)+color[c])
            changed += final[at:at+3] != original[at:at+3]
assert 1000 < changed < (x1-x0)*(y1-y0)
sha = codec.write_png(output, w, h, final)
# Verify the preservation claim against all decoded ancestor pixels.
_, _, decoded = codec.read_png(output)
points = [(i % w, i // w) for i in range(w*h)
          if decoded[3*i:3*i+3] != original[3*i:3*i+3]]
assert len(points) == changed
assert all(x0 <= x < x1 and y0 <= y < y1 for x, y in points)

# System libgd only encodes a resampled JPEG; it is not a tool dependency.
gd = ctypes.CDLL('libgd.so.3')
ptr, integer = ctypes.c_void_p, ctypes.c_int
gd.gdImageCreateFromPngPtr.argtypes = [integer, ptr]
gd.gdImageCreateFromPngPtr.restype = ptr
gd.gdImageCreateTrueColor.argtypes = [integer, integer]
gd.gdImageCreateTrueColor.restype = ptr
gd.gdImageCopyResampled.argtypes = [ptr, ptr] + [integer]*8
gd.gdImageJpegPtr.argtypes = [ptr, ctypes.POINTER(integer), integer]
gd.gdImageJpegPtr.restype = ptr
gd.gdFree.argtypes = [ptr]
gd.gdImageDestroy.argtypes = [ptr]
raw = output.read_bytes()
buffer = ctypes.create_string_buffer(raw)
source = gd.gdImageCreateFromPngPtr(len(raw), buffer)
target = gd.gdImageCreateTrueColor(512, 512)
assert source and target
gd.gdImageCopyResampled(target, source, 0, 0, 0, 0, 512, 512, w, h)
size = integer()
encoded = gd.gdImageJpegPtr(target, ctypes.byref(size), 85)
assert encoded
jpeg = ctypes.string_at(encoded, size.value)
gd.gdFree(encoded)
gd.gdImageDestroy(source)
gd.gdImageDestroy(target)
assert len(jpeg) < 100000 and jpeg[:2] == b'\xff\xd8'
Path('dist/line-4/25.jpg').write_bytes(jpeg)
ancestor.write_bytes(output.read_bytes())
evidence = {'ancestor_sha256': old_sha, 'wall_sha256': sha,
            'dimensions': [w,h], 'format': 'PNG', 'mode': 'RGB',
            'outputs': ['artifacts/line-4/wall-v7.png', 'artifacts/line-4/wall.png'],
            'new_mark_rectangle_xyxy': [x0,y0,x1,y1],
            'changed_bounds_xyxy': [min(x for x,y in points), min(y for x,y in points),
                                    max(x for x,y in points), max(y for x,y in points)],
            'changed_pixels': changed, 'changed_pixels_outside_rectangle': 0,
            'method': 'Installed image tool generated pigment; masked area samples composite only the new pictograph over inherited rock.',
            'preview': {'path': 'dist/line-4/25.jpg', 'format': 'JPEG',
                        'dimensions': [512,512], 'bytes': len(jpeg)},
            'unmet_visual_requirements': []}
Path('line-4/IMAGE-25.json').write_text(json.dumps(evidence, indent=2)+'\n')
print(json.dumps(evidence, indent=2))
