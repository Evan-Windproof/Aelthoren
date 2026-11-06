#!/usr/bin/env python3
"""Explicit integrity-checked omni resource overlay; never edits native binaries."""
import hashlib
import io
import json
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / 'branding/final-resources.json'


def apply(runtime):
    from PIL import Image
    manifest = json.loads(MANIFEST.read_text())
    if manifest['engine_revision'] != json.loads((ROOT/'upstream.lock.json').read_text())['revision']:
        raise ValueError('Final branding manifest is for another upstream revision')
    brandzip = zipfile.ZipFile(runtime/'browser/omni.ja')
    logo = brandzip.read('chrome/browser/content/branding/about-logo.svg')
    png = brandzip.read('chrome/browser/content/branding/about-logo.png')
    neutral = (ROOT/'branding/artwork/neutral-browser.svg').read_bytes()
    result=[]
    for archive in sorted({e['archive'] for e in manifest['entries']}):
        path=runtime/archive
        changes={e['path']:e for e in manifest['entries'] if e['archive']==archive}
        with zipfile.ZipFile(path) as source:
            if not set(changes).issubset(source.namelist()):
                raise ValueError('Missing reviewed branding resource')
            replacements={}
            for name,entry in changes.items():
                old=source.read(name)
                if hashlib.sha256(old).hexdigest()!=entry['sha256']:
                    raise ValueError('Unreviewed branding input: '+name)
                kind=entry['replacement']
                if kind=='text':
                    text=old.decode()
                    for before,after in entry['substitutions'].items():
                        if before not in text:raise ValueError('Missing exact replacement: '+name)
                        text=text.replace(before,after)
                    data=text.encode()
                elif name.endswith('.svg'):
                    data=logo if kind=='owner-logo' else neutral
                else:
                    # Preserve raster dimensions and format; owner logo, no fox-derived art.
                    with Image.open(io.BytesIO(old)) as original: size=original.size
                    with Image.open(io.BytesIO(png)) as icon:
                        image=icon.convert('RGBA');image.thumbnail(size)
                        canvas=Image.new('RGBA',size);canvas.paste(image,((size[0]-image.width)//2,(size[1]-image.height)//2))
                        output=io.BytesIO();canvas.save(output,format='PNG');data=output.getvalue()
                replacements[name]=data
                result.append({'archive':archive,'path':name,'before_sha256':entry['sha256'],'after_sha256':hashlib.sha256(data).hexdigest(),'replacement':kind})
            temporary=path.with_suffix('.branding-partial')
            if temporary.exists():raise ValueError('Preserve existing partial branding archive')
            with zipfile.ZipFile(temporary,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as target:
                for info in source.infolist():
                    target.writestr(info,replacements.get(info.filename,source.read(info.filename)))
        temporary.replace(path)
    return result
