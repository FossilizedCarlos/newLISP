#!/usr/bin/env python3
"""Measure deterministic synthetic workloads with the Python standard library."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import random
import re
import statistics
import subprocess
import time

WORKLOADS = ['evaluation', 'allocation', 'lists', 'symbols', 'numeric', 'ffi']
ROOT = Path(__file__).resolve().parent.parent


def command_output(*args):
    return subprocess.check_output(args, text=True).strip()


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def measure(binary, workload, scale):
    env = dict(os.environ, NEWLISP_BENCH_SCALE=str(scale))
    start = time.perf_counter()
    proc = subprocess.run(['/usr/bin/time', '-l', str(binary),
                           'benchmarks/synthetic.lsp', workload], cwd=ROOT,
                          env=env, capture_output=True, text=True, timeout=120)
    seconds = time.perf_counter() - start
    if proc.returncode or not proc.stdout.startswith('PASS ' + workload + ' '):
        raise RuntimeError(proc.stdout + proc.stderr)
    match = re.search(r'(\d+)\s+maximum resident set size', proc.stderr)
    if not match:
        raise RuntimeError('Missing macOS peak RSS measurement: ' + proc.stderr)
    return {'seconds': seconds, 'peak_rss_bytes': int(match.group(1)),
            'result': proc.stdout.strip()}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--candidate', action='append', required=True, metavar='LABEL=BINARY')
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--repeats', type=int, default=9)
    parser.add_argument('--warmups', type=int, default=1)
    parser.add_argument('--scale', type=int, default=10)
    parser.add_argument('--seed', type=int, default=20261105)
    args = parser.parse_args()
    if args.repeats < 3 or args.warmups < 1 or args.scale < 1:
        parser.error('Use at least three repeats, one warmup, and scale one.')
    candidates = {}
    for entry in args.candidate:
        label, path = entry.split('=', 1)
        if label in candidates:
            parser.error('Duplicate candidate: ' + label)
        candidates[label] = Path(path).resolve(strict=True)
    if platform.system() != 'Darwin':
        parser.error('This runner uses macOS time -l for peak RSS.')
    result = {
        'kind': 'synthetic', 'source_commit': command_output('git', '-C', str(ROOT), 'rev-parse', 'HEAD'),
        'hardware': command_output('sysctl', '-n', 'machdep.cpu.brand_string'),
        'memory_bytes': int(command_output('sysctl', '-n', 'hw.memsize')),
        'os': command_output('sw_vers'), 'compiler': command_output('xcrun', 'clang', '--version'),
        'scale': args.scale, 'repeats': args.repeats, 'warmups': args.warmups, 'seed': args.seed,
        'script_sha256': digest(ROOT / 'benchmarks/synthetic.lsp'),
        'runner_sha256': digest(__file__),
        'candidates': {label: {'path': str(path), 'sha256': digest(path), 'bytes': path.stat().st_size}
                       for label, path in candidates.items()},
        'samples': {label: {w: [] for w in WORKLOADS} for label in candidates},
    }
    rng = random.Random(args.seed)
    pairs = [(label, w) for label in candidates for w in WORKLOADS]
    for _ in range(args.warmups):
        for label, workload in pairs:
            measure(candidates[label], workload, args.scale)
    for iteration in range(args.repeats):
        rng.shuffle(pairs)
        for label, workload in pairs:
            result['samples'][label][workload].append(measure(candidates[label], workload, args.scale))
        print('Completed measurement round', iteration + 1, flush=True)
    result['summary'] = {}
    for label, workloads in result['samples'].items():
        result['summary'][label] = {}
        for workload, samples in workloads.items():
            values = [s['seconds'] for s in samples]
            median = statistics.median(values)
            result['summary'][label][workload] = {
                'median_seconds': median, 'min_seconds': min(values), 'max_seconds': max(values),
                'mad_seconds': statistics.median(abs(v - median) for v in values),
                'median_peak_rss_bytes': statistics.median(s['peak_rss_bytes'] for s in samples),
            }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + '\n')
    print('Saved', args.output)


if __name__ == '__main__':
    main()
