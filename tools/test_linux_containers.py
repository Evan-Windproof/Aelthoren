#!/usr/bin/env python3
"""Test the exact tarball in clean official distro images; no source mounted."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import threading

from prepare_phase1 import ROOT, SOURCE

DOCKER = ['docker', '--host=unix:///var/run/docker.sock']
BASES = {'debian13':'debian@sha256:a72b4433de1cf7d6bae0c4cee74d0547f58601a643b3375f070c51600d63b6b2','ubuntu2404':'ubuntu@sha256:fe81560990fae86dc4743202b2cb4d3df98d0bcf949173cecef15ce1127ef852'}


def docker_env():
    env = dict(os.environ)
    for name in ['DOCKER_HOST','DOCKER_CONTEXT','DOCKER_TLS','DOCKER_TLS_VERIFY','DOCKER_CERT_PATH']:
        env.pop(name,None)
    return env


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('archive',type=Path)
    parser.add_argument('--output',type=Path,default=Path('/workspace/aelthoren-packaging/verification'))
    parser.add_argument('--distribution',choices=list(BASES),action='append')
    parser.add_argument('--build-images',action='store_true')
    parser.add_argument('--gui',action='store_true',help='Use an already-running :97 Xorg dummy display')
    parser.add_argument('--branding-audit',action='store_true',help='Extra GUI branding inspection; requires --gui')
    args=parser.parse_args()
    if args.branding_audit and not args.gui:raise ValueError('Branding audit requires GUI')
    archive=args.archive.resolve();output=args.output.resolve();output.mkdir(parents=True,exist_ok=True)
    if output==ROOT or ROOT in output.parents:raise ValueError('Keep raw QA output outside Git')
    with archive.open('rb') as stream:sha=hashlib.file_digest(stream,'sha256').hexdigest()
    summary={'archive':str(archive),'bytes':archive.stat().st_size,'sha256':sha,'cases':[]}
    ca=os.environ.get('CODEX_PROXY_CERT')
    if not ca or not Path(ca).is_file():raise ValueError('Cloud QA requires its supplied proxy CA mount; never disable TLS verification')
    client_auth=output/'container.Xauthority'
    if args.gui:
        auth=subprocess.check_output(['xauth','-f','/workspace/aelthoren-packaging/Xauthority','nlist',':97'])
        if not auth.strip():raise ValueError('No authenticated :97 display entry')
        wildcard=b'\n'.join(b'ffff'+line[4:] for line in auth.splitlines())+b'\n'
        subprocess.run(['xauth','-f',str(client_auth),'nmerge','-'],input=wildcard,check=True,capture_output=True)
        client_auth.chmod(0o600)
    for distro in args.distribution or list(BASES):
        image='aelthoren-test-'+distro
        if args.build_images:
            with (output/(distro+'-image.log')).open('w') as log:
                subprocess.run([*DOCKER,'build','--build-arg','BASE='+BASES[distro],'-t',image,'-f',str(ROOT/'packaging/qa/Dockerfile'),str(ROOT/'packaging/qa')],env=docker_env(),stdout=log,stderr=subprocess.STDOUT,check=True)
        case=output/(distro+('-gui' if args.gui else '-headless'))
        if case.exists():raise ValueError('Preserve existing case before repeating '+str(case))
        case.mkdir()
        with tempfile.TemporaryDirectory(prefix='package-checks-',dir=output) as temporary:
            checks=Path(temporary)
            shutil.copyfile(ROOT/'tools/verify_linux_package.py',checks/'verify.py')
            if args.branding_audit:shutil.copyfile(ROOT/'tools/verify_branding_gui.py',checks/'verify_branding_gui.py')
            helper=SOURCE/'toolkit/components/url-classifier/tests/UrlClassifierTestUtils.sys.mjs'
            shutil.copyfile(helper,checks/helper.name)
            cmd=[*DOCKER,'run','--rm','--mount',f'type=bind,src={archive},dst=/input/package.tar.xz,readonly','--mount',f'type=bind,src={checks},dst=/checks,readonly','--mount',f'type=bind,src={case},dst=/out','--mount',f'type=bind,src={ca},dst=/run/proxy-ca.pem,readonly']
            if args.gui:
                cmd += ['--mount','type=bind,src=/tmp/.X11-unix,dst=/tmp/.X11-unix,readonly','--mount',f'type=bind,src={client_auth},dst=/run/Xauthority,readonly','-e','DISPLAY=:97','-e','XAUTHORITY=/run/Xauthority']
            script='set -eu; mkdir -p "/tmp/Portable Alpha"; tar -xJf /input/package.tar.xz -C "/tmp/Portable Alpha"; cd "/tmp/Portable Alpha/aelthoren-0.1.0-alpha"; sha256sum -c MANIFEST.sha256 > /out/manifest-checks.txt; ./aelthoren --version; python3 /checks/verify.py "/tmp/Portable Alpha/aelthoren-0.1.0-alpha" /out'
            if args.gui:script+=' --gui'
            if args.branding_audit:script+=' --branding-audit'
            cmd += [image,'/bin/sh','-c',script]
            stop=threading.Event()
            def capture_native_prompt():
                while not stop.wait(.1):
                    if (case/'default-prompt.request').exists():
                        subprocess.run(['import','-display',':97','-window','root',str(case/'default-browser-prompt.png')],env=dict(os.environ,XAUTHORITY='/workspace/aelthoren-packaging/Xauthority'),check=True)
                        return
            worker=None
            if args.branding_audit:
                worker=threading.Thread(target=capture_native_prompt,daemon=True);worker.start()
            try:
                with (case/'console.log').open('w') as log:
                    result=subprocess.run(cmd,env=docker_env(),stdout=log,stderr=subprocess.STDOUT)
            finally:
                stop.set()
                if worker:worker.join(timeout=10)
            print(distro,'GUI' if args.gui else 'headless','exit',result.returncode,flush=True)
            if result.returncode:raise RuntimeError('Package verification failed; see '+str(case/'console.log'))
        data=json.loads((case/'results.json').read_text())
        image_id=subprocess.check_output([*DOCKER,'image','inspect',image,'--format','{{.Id}}'],env=docker_env(),text=True).strip()
        summary['cases'].append({'distribution':distro,'base':BASES[distro],'image_id':image_id,'result':data['result'],'gui':data['gui'],'uid':data['uid'],'checks':data['checks'],'os_release':data['distribution'],'package_metadata':data['package_metadata'],'raw_output':str(case)})
        (output/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    print('Verified archive SHA-256:',sha,flush=True)


if __name__=='__main__':main()
