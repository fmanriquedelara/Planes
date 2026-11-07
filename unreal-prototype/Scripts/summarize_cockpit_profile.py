"""Summarize actual native CSV profiler frames, excluding CSV footer/header rows."""
import csv
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / 'artifacts/ue008'
FIELDS = ['FrameTime', 'GameThreadTime', 'RenderThreadTime', 'GPUTime',
          'RHI/DrawCalls', 'RHI/PrimitivesDrawn', 'GPUMem/LocalUsedMB', 'MemoryFreeMB']


def percentile(values, q):
    pos = (len(values) - 1) * q
    lo, hi = math.floor(pos), math.ceil(pos)
    return values[lo] + (values[hi] - values[lo]) * (pos - lo)


result = {'method': 'Native normal-game CSV profiler; uncapped VSync off; 360 warmup frames',
          'limitations': ['Offscreen uncooked Development game, not packaged build',
                          'Short straight-flight sample; not a long-run stability or worst-case weather test'],
          'variants': {}}
for variant in ['baseline', 'detail', 'detail-85pct']:
    path = ROOT / variant / 'profile.csv'
    if not path.exists():
        continue
    columns = {field: [] for field in FIELDS}
    with path.open(newline='', encoding='utf-8-sig') as file:
        for row in csv.DictReader(file):
            try:
                frame = float(row['FrameTime'])
            except (ValueError, TypeError, KeyError):
                continue
            if frame <= 0:
                continue
            for field in FIELDS:
                try:
                    columns[field].append(float(row[field]))
                except (ValueError, TypeError, KeyError):
                    pass
    metrics = {}
    for field, values in columns.items():
        if not values:
            continue
        values.sort()
        metrics[field] = {'mean': sum(values) / len(values), 'median': percentile(values, .5),
                          'p95': percentile(values, .95), 'p99': percentile(values, .99),
                          'max': values[-1], 'samples': len(values)}
    metrics['average_fps_from_mean_frame_time'] = 1000 / metrics['FrameTime']['mean']
    run_path = ROOT / variant / 'profile-run.json'
    metrics['run'] = json.loads(run_path.read_text(encoding='utf-8-sig')) if run_path.exists() else None
    if metrics['run'] and metrics['FrameTime']['samples'] != metrics['run']['profile_frames']:
        raise RuntimeError('Sample count does not match completed run metadata for ' + variant)
    result['variants'][variant] = metrics
if 'baseline' in result['variants'] and 'detail' in result['variants']:
    keys = ['width', 'height', 'screen_percentage', 'dynamic_resolution', 'profile_frames']
    a, b = [result['variants'][v]['run'] for v in ['baseline', 'detail']]
    if not a or not b or any(a.get(k) != b.get(k) for k in keys):
        raise RuntimeError('Baseline and detail profiling settings do not match')
    result['matched_settings'] = {k: a[k] for k in keys}
    baseline = result['variants']['baseline']['FrameTime']['mean']
    detail = result['variants']['detail']['FrameTime']['mean']
    result['mean_frame_time_delta_ms'] = detail - baseline
    result['mean_frame_time_delta_percent'] = 100 * (detail / baseline - 1)
if 'detail' in result['variants'] and 'detail-85pct' in result['variants']:
    runs = [result['variants'][v]['run'] for v in ['detail', 'detail-85pct']]
    hashes = [r.get('input_sha256') if r else None for r in runs]
    if hashes[0] != hashes[1]:
        raise RuntimeError('Native and upscaled detail samples refer to different asset revisions')
    if runs[0].get('native_material_revision') != runs[1].get('native_material_revision'):
        raise RuntimeError('Native and upscaled detail samples use different native materials')
(ROOT / 'performance-summary.json').write_text(json.dumps(result, indent=2))
print(json.dumps(result, indent=2))
