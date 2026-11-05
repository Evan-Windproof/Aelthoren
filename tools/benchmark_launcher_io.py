#!/usr/bin/env python3
"""Measure repeated launcher preparation against disposable local configuration."""
import argparse
import json
from pathlib import Path
import statistics
import tempfile
import time
from unittest import mock

import privacy
import run_aelthoren
from prepare_phase1 import ROOT


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('stage',choices=['baseline','candidate'])
    args=parser.parse_args()
    target=ROOT/'docs/phase4'/(args.stage+'-launcher.json')
    if target.exists():
        raise ValueError('Preserve existing measurements first')
    with tempfile.TemporaryDirectory(prefix='launcher-io-',dir='/workspace/aelthoren-benchmarks') as temporary:
        fixture=Path(temporary)
        binary=fixture/'bin'
        with mock.patch.object(run_aelthoren,'PROFILE_ROOT',fixture/'profiles'):
            privacy.install_policies(binary)
            profile=run_aelthoren.prepare_profile('fixture')
            paths=sorted((binary/'distribution').iterdir())+[profile/'.aelthoren-profile']
            before={str(p):p.stat().st_mtime_ns for p in paths}
            privacy.install_policies(binary)
            run_aelthoren.prepare_profile('fixture')
            rewrites=sum(before[str(p)]!=p.stat().st_mtime_ns for p in paths)
            timings=[]
            for _ in range(7):
                start=time.perf_counter()
                for _ in range(200):
                    privacy.install_policies(binary)
                    run_aelthoren.prepare_profile('fixture')
                timings.append((time.perf_counter()-start)*1e6/200)
            result={'stage':args.stage,'method':'install both reviewed configurations and prepare a marked profile; buffered filesystem; excludes full overlay guard and browser startup','batches':7,'iterations_per_batch':200,'microseconds_per_pair':timings,'median_us':statistics.median(timings),'min_us':min(timings),'max_us':max(timings),'unchanged_files_rewritten_per_pair':rewrites,'tracked_files':len(paths)}
    target.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))


if __name__=='__main__':
    main()
