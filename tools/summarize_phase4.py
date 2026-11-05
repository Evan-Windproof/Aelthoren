#!/usr/bin/env python3
"""Summarize measured per-session samples without pooling nested trials."""
import json
import re
from pathlib import Path
import statistics

from prepare_phase1 import ROOT


def rows(report):
    runs=report['runs']
    assert len(runs)==6 and all(r['exit_code']==0 for r in runs)
    result={}
    for mode in ['profile-cold','warm']:
        matching=[r for r in runs if r['mode']==mode]
        for field in ['startup_listener_ms','startup_responsive_ms']:
            result[f'{mode} {field}']=[r[field] for r in matching]
    for count in [1,5,10]:
        selected=[next(s for s in r['resources'] if s['tabs']==count) for r in runs]
        for field in ['idle_cpu_pct_one_core','rss_mib','processes','http_attempts']:
            result[f'{count} tabs {field}']=[s[field] for s in selected]
        if all(s['pss_mib'] is not None for s in selected):
            result[f'{count} tabs pss_mib']=[s['pss_mib'] for s in selected]
    for field in ['tab_create_ms','tab_switch_ms','newtab_load_ms']:
        result[field]=[statistics.median(r[field]) for r in runs]
    result['after closure rss_mib']=[r['after_tab_closure']['rss_mib'] for r in runs]
    result['after closure processes']=[r['after_tab_closure']['processes'] for r in runs]
    result['unchanged_files_rewritten']=[r['unchanged_files_rewritten'] for r in runs]
    return result


def describe(values):
    return {'median':statistics.median(values),'min':min(values),'max':max(values),'n':len(values)}


def metric_name(label):
    names={'tab_create_ms':'Tab creation + navigation (ms)','tab_switch_ms':'Tab switch + two frames (ms)','newtab_load_ms':'Branded new-tab load (ms)','after closure rss_mib':'RSS after closing back to one tab (MiB)','after closure processes':'Process count after closing back to one tab','unchanged_files_rewritten':'Unchanged managed files rewritten per launch'}
    if label in names:
        return names[label]
    for mode,title in [('profile-cold','Fresh profile'),('warm','Warm restart')]:
        if label==mode+' startup_listener_ms':
            return title+' → automation listener (ms)'
        if label==mode+' startup_responsive_ms':
            return title+' → first-page responsive (ms)'
    match=re.fullmatch(r'(\d+) tabs (.+)',label)
    if match:
        count,field=match.groups()
        field={'idle_cpu_pct_one_core':'Idle CPU (% of one core)','rss_mib':'Summed RSS (MiB)','pss_mib':'Summed PSS (MiB)','processes':'Process count','http_attempts':'HTTP attempts / 5-second window'}[field]
        return f'{field}, {count} tab(s)'
    return label


def main():
    directory=ROOT/'docs/phase4'
    baseline=rows(json.loads((directory/'baseline.json').read_text()))
    candidate=rows(json.loads((directory/'candidate.json').read_text()))
    comparisons={}
    lines=['| Metric | Baseline median [min, max] | Candidate median [min, max] | Change | Repetitions/condition | Environment |','| --- | --- | --- | --- | --- | --- |']
    for label,values in baseline.items():
        b=describe(values)
        c=describe(candidate[label])
        delta=c['median']-b['median']
        percent=100*delta/b['median'] if b['median'] else None
        comparisons[label]={'baseline':b,'candidate':c,'difference':delta,'percent':percent}
        if 'cpu_pct' in label:
            change=f'{delta:+.2f} pp'
        elif 'http_attempts' in label:
            change=f'{delta:+.2f} attempts'
        elif 'processes' in label:
            change=f'{delta:+.2f} processes'
        elif label=='unchanged_files_rewritten':
            change=f'{percent:+.1f}%'
        else:
            change=f'{percent:+.1f}%' if percent is not None else 'n/a'
        display=lambda x:f"{x['median']:.2f} [{x['min']:.2f}, {x['max']:.2f}]"
        lines.append(f'| {metric_name(label)} | {display(b)} | {display(c)} | {change} | {b["n"]} | E1 |')
    for label in ['baseline','candidate']:
        x=json.loads((directory/(label+'-launcher.json')).read_text())
        comparisons[label+'_launcher_preparation_us']=describe(x['microseconds_per_pair'])
    b=comparisons['baseline_launcher_preparation_us'];c=comparisons['candidate_launcher_preparation_us']
    change=100*(c['median']-b['median'])/b['median']
    lines.append(f"| Marked profile + configuration preparation (µs/pair) | {b['median']:.2f} [{b['min']:.2f}, {b['max']:.2f}] | {c['median']:.2f} [{c['min']:.2f}, {c['max']:.2f}] | {change:+.1f}% | 7 batches × 200 | E1 buffered filesystem |")
    (directory/'comparison.json').write_text(json.dumps(comparisons,indent=2)+'\n')
    (directory/'comparison.md').write_text('\n'.join(lines)+'\n')
    print('\n'.join(lines))


if __name__=='__main__':
    main()
