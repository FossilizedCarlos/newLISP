#!/usr/bin/env python3
"""Collect checked synthetic workload profiles with the installed macOS sampler."""
import argparse
import gzip
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parent.parent
WORKLOADS = ['evaluation', 'allocation', 'lists', 'symbols', 'numeric', 'ffi']


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def summarize(text):
    total = re.search(r'^\s+(\d+) Thread_', text, re.M)
    section = text.split('Sort by top of stack, same collapsed (when >= 5):', 1)[1].split('Binary Images:', 1)[0]
    counts = {}
    for line in section.splitlines():
        match = re.match(r'\s+(.+?)\s+\(in (.+?)\)\s+(\d+)\s*$', line)
        if match:
            name, library, count = match.groups()
            counts[name + ' (' + library + ')'] = int(count)
    if not total or not counts:
        raise ValueError('Missing sample totals or collapsed leaf counts')
    total = int(total.group(1))
    if sum(counts.values()) > total:
        raise ValueError('Leaf counts exceed the single-thread sample count')
    return {'samples': total, 'leaf_counts_at_least_five': counts,
            'unlisted_samples': total - sum(counts.values())}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--binary', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    binary = args.binary.resolve(strict=True)
    args.output.mkdir(parents=True, exist_ok=False)
    result = {'source_commit': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
              'binary': str(binary), 'binary_sha256': digest(binary),
              'workload_sha256': digest(ROOT / 'benchmarks/synthetic.lsp'),
              'runner_sha256': digest(Path(__file__)),
              'tool': '/usr/bin/sample', 'seconds': 3, 'interval_ms': 1, 'scale': 200, 'profiles': []}
    for session in [1, 2]:
        for workload in WORKLOADS:
            raw = args.output / f'{workload}-{session}.txt'
            proc = subprocess.Popen([str(binary), 'benchmarks/synthetic.lsp', workload], cwd=ROOT,
                                    env=dict(os.environ, NEWLISP_BENCH_SCALE='200'),
                                    stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            try:
                sampled = subprocess.run(['/usr/bin/sample', str(proc.pid), '3', '1', '-mayDie', '-file', str(raw.resolve())],
                                         capture_output=True, text=True, timeout=60)
                stdout, stderr = proc.communicate(timeout=120)
                if sampled.returncode or proc.returncode or not stdout.startswith('PASS ' + workload + ' '):
                    raise RuntimeError(sampled.stderr + stdout + stderr)
            finally:
                if proc.poll() is None:
                    proc.kill()
                    proc.communicate()
            text = raw.read_text()
            summary = summarize(text)
            summary.update(workload=workload, session=session, result=stdout.strip(), raw=raw.name + '.gz')
            with gzip.open(str(raw) + '.gz', 'wb') as stream:
                stream.write(raw.read_bytes())
            raw.unlink()
            result['profiles'].append(summary)
            (args.output / 'summary.json').write_text(json.dumps(result, indent=2) + '\n')
            print('Profile complete:', workload, session, summary['samples'], 'samples', flush=True)
    if digest(binary) != result['binary_sha256']:
        raise RuntimeError('Binary changed during profiling')


if __name__ == '__main__':
    main()
