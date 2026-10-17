"""Retain only generated pigment on bare rock; preserve every ancestor pixel outside it."""
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess

spec = importlib.util.spec_from_file_location('png_codec27', 'gathering/finish_wall.py')
png = importlib.util.module_from_spec(spec)
spec.loader.exec_module(png)


def main():
    old = Path('artifacts/line-2/wall-v6.png')
    output = Path('artifacts/line-2/wall-v7.png')
    ancestor_sha = hashlib.sha256(old.read_bytes()).hexdigest()
    assert ancestor_sha == '0988fca17fed92b5ee05af3a667a71f8f1d0aee744587bbaad97a8f61c8a0a28'
    draft_sha = hashlib.sha256(output.read_bytes()).hexdigest()
    width, height, original = png.read_png(old)
    dw, dh, draft = png.read_png(output)
    assert (width, height) == (dw, dh) == (1254, 1254)
    final = original[:]
    rectangle = (925, 495, 150, 110)
    x0, y0, rw, rh = rectangle
    for y in range(y0, y0 + rh):
        for x in range(x0, x0 + rw):
            index = (y * width + x) * 3
            r, g, b = draft[index:index + 3]
            distances = [((x-cx)/rx)**2 + ((y-cy)/ry)**2
                         for cx,cy,rx,ry in ((958,548,29,49),(1040,548,29,49))]
            distance = min(distances)
            alpha = 0.0
            if distance < 1 and r > 1.55*g and r > 2.2*b:
                alpha = .92 * min(1, (1-distance)*5)
            # The dots and short cord come from the generated draft itself.
            if ((distance < .7) or (977 <= x <= 1023 and 529 <= y <= 553)) and r < 110 and g < 85:
                alpha = max(alpha, min(.94, (110-r)/40))
            if alpha:
                for c in range(3):
                    final[index+c] = round(original[index+c]*(1-alpha)+draft[index+c]*alpha)
    changed = outside = 0
    for i in range(width*height):
        if final[3*i:3*i+3] != original[3*i:3*i+3]:
            changed += 1
            x,y = i%width, i//width
            outside += not (x0 <= x < x0+rw and y0 <= y < y0+rh)
    assert changed > 0 and outside == 0
    digest = png.write_png(output,width,height,final)
    continuation = Path('artifacts/line-2/wall.png')
    assert continuation.is_symlink() and continuation.readlink() == Path('wall-v6.png')
    continuation.unlink()
    continuation.symlink_to('wall-v7.png')
    rgba = bytearray()
    for y in range(512):
        ya,yb = y*height//512, (y+1)*height//512
        for x in range(512):
            xa,xb = x*width//512, (x+1)*width//512
            n = (yb-ya)*(xb-xa)
            for c in range(3):
                rgba.append(round(sum(final[(sy*width+sx)*3+c]
                                      for sy in range(ya,yb) for sx in range(xa,xb))/n))
            rgba.append(255)
    js = """
const fs = require('fs');
const encode = require('./line-3/tools/corpus-change-receipt/vendor/jpeg-js/lib/encoder.js');
const data = fs.readFileSync(0);
if (data.length !== 512*512*4) throw Error('bad input');
const result = encode({data,width:512,height:512},78);
if (result.data.length > 100000) throw Error('JPEG too large');
fs.writeFileSync('dist/line-2/27.jpg',result.data);
"""
    subprocess.run(['node','-e',js],input=rgba,check=True)
    report = {'round':27, 'ancestorSha256':ancestor_sha, 'generatedDraftSha256':draft_sha,
              'wallSha256':digest, 'dimensions':[width,height], 'format':'PNG', 'channels':'RGB',
              'newMarkRectangle':list(rectangle), 'changedPixels':changed,
              'changedPixelsOutsideRectangle':outside,
              'method':'Built-in imagegen; retained only generated pigment on bare rock, preserving the inherited pixels elsewhere.',
              'visualReview':'Pending final inspection', 'unmetVisualRequirements':[], 'images':[]}
    for path,kind,size in ((output,'PNG',[1254,1254]),(continuation,'PNG',[1254,1254]),
                           (Path('dist/line-2/27.jpg'),'JPEG',[512,512])):
        data = path.read_bytes()
        report['images'].append({'path':str(path),'format':kind,'dimensions':size,
                                 'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()})
    Path('line-2/REVIEW-27.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))


if __name__ == '__main__':
    main()
