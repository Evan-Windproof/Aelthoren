#!/usr/bin/env python3
"""Compare a final archive with preserved Phase 5A bytes; no extraction or execution."""
import argparse
import hashlib
import io
import json
from pathlib import Path
import tarfile
import zipfile


def runtime(archive):
    return {m.name.split('/runtime/',1)[1]:m for m in archive.getmembers() if '/runtime/' in m.name and m.isfile()}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('original',type=Path);parser.add_argument('final',type=Path);parser.add_argument('output',type=Path)
    args=parser.parse_args();manifest=json.loads((Path(__file__).resolve().parents[1]/'branding/final-resources.json').read_text())
    changes=[];native=[];unchanged=0
    with tarfile.open(args.original,'r:xz') as original,tarfile.open(args.final,'r:xz') as final:
        old=runtime(original);new=runtime(final)
        for name,member in new.items():
            data=final.extractfile(member).read()
            if data.startswith(b'\x7fELF'):
                if name not in old or data!=original.extractfile(old[name]).read():raise ValueError('Native binary changed: '+name)
                native.append({'path':name,'sha256':hashlib.sha256(data).hexdigest(),'byte_identical_to_original':True})
        for arc in ['omni.ja','browser/omni.ja']:
            before=zipfile.ZipFile(io.BytesIO(original.extractfile(old[arc]).read()));after=zipfile.ZipFile(io.BytesIO(final.extractfile(new[arc]).read()))
            if set(before.namelist())!=set(after.namelist()):raise ValueError('Resource membership changed')
            for name in before.namelist():
                a=before.read(name);b=after.read(name)
                if a!=b:changes.append({'archive':arc,'path':name,'before_sha256':hashlib.sha256(a).hexdigest(),'after_sha256':hashlib.sha256(b).hexdigest()})
                else:unchanged+=1
        expected={(c['archive'],c['path']):c['sha256'] for c in manifest['entries']}
        if {(c['archive'],c['path']):c['before_sha256'] for c in changes}!=expected:raise ValueError('Changes differ from reviewed manifest')
    def digest(path):
        with path.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()
    report={'result':'PASS','original_sha256':digest(args.original),'archive_sha256':digest(args.final),'approved_resource_changes':len(changes),'unchanged_omni_resources':unchanged,'native_binaries':native,'changed_resources':changes}
    args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(report,indent=2)+'\n')
    print('PASS:',len(changes),'approved changes;',unchanged,'unchanged resources;',len(native),'unchanged ELF binaries')


if __name__=='__main__':main()
