#!/usr/bin/env python3
"""Inventory every packaged file, omni image and Mozilla/Firefox text-bearing resource."""
import argparse
import hashlib
import io
import json
import re
import tarfile
import zipfile
from pathlib import Path

PATTERN=re.compile(r'Mozilla|Firefox|mozilla\.org|firefox\.com',re.I)
TEXT=('.ftl','.properties','.ini','.desktop','.html','.xhtml','.txt','.md','.js','.mjs','.css','.json','.cfg')
IMAGES=('.svg','.png','.webp','.jpg','.jpeg','.gif','.ico')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('archive',type=Path);parser.add_argument('output',type=Path)
    args=parser.parse_args();files=[];resources=[]
    with tarfile.open(args.archive,'r:xz') as archive:
        for member in archive:
            if not member.isfile():continue
            data=archive.extractfile(member).read();item={'path':member.name,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()}
            if data.startswith(b'\x7fELF'):
                item['native_identity_tokens']={t.decode():len(re.findall(t,data,re.I)) for t in [b'firefox',b'mozilla']}
                item['disposition']='Native binary unchanged; identity/compatibility/attribution require full-build review'
            files.append(item)
            entries=zipfile.ZipFile(io.BytesIO(data)) if member.name.endswith('/omni.ja') else None
            for name,body in ((n,entries.read(n)) for n in entries.namelist()) if entries else [(member.name,data)]:
                image=name.endswith(IMAGES);text=name.endswith(TEXT)
                if not image and not text:continue
                decoded=body.decode(errors='replace') if text or name.endswith('.svg') else ''
                matches=[{'line':i,'text':line[:500]} for i,line in enumerate(decoded.splitlines(),1) if PATTERN.search(line)]
                if image or matches:
                    record={'archive':member.name if entries else None,'path':name,'kind':'image' if image else 'text','sha256':hashlib.sha256(body).hexdigest()}
                    if matches:
                        record['matching_lines']=len(matches)
                        # Full localizable/product/legal text; minified code excerpts are not a semantic audit.
                        if name.endswith(('.ftl','.properties','.ini','.desktop','.html','.xhtml','.txt','.md')):record['matches']=matches
                    resources.append(record)
    report={'archive':args.archive.name,'bytes':args.archive.stat().st_size,'sha256':hashlib.file_digest(args.archive.open('rb'),'sha256').hexdigest(),'scope':'All regular packaged files and every omni member enumerated; all image resources indexed; text reference inventory is evidence, not legal clearance. Dynamic remote/UI paths and native binaries remain distribution blockers.','files':files,'resources':resources}
    args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(report,indent=2)+'\n')
    print('Indexed',len(files),'package files;',len(resources),'image/text resources;',args.output.stat().st_size,'report bytes')


if __name__=='__main__':main()
