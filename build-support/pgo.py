#!/usr/bin/env python3
"""Train and validate optional native profiles with installed LLVM tools."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shlex
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parent.parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def output(args):
    return subprocess.check_output(args, text=True, cwd=ROOT).strip()


def identity():
    files = sorted(set(ROOT.glob('*.c')) | set(ROOT.glob('*.h')))
    files += [ROOT / name for name in ['util/embedding-test.c', 'util/ffitest.c', 'util/arm64-callback.c']]
    files += [ROOT / 'makefile_darwin_arm64', ROOT / 'build-support/apple-silicon-deps.sh', Path(__file__).resolve()]
    cc = shlex.split(os.environ['PGO_CC'])
    return {
        'files': {str(p.relative_to(ROOT)): sha(p) for p in files},
        'compiler': output(cc + ['--version']),
        'settings': {k: os.environ.get('PGO_' + k, '') for k in
                     ['CC', 'SDKROOT', 'CPPFLAGS', 'CFLAGS', 'LDFLAGS', 'LDLIBS']},
        'sdk_version': output(['xcrun', '--sdk', os.environ['PGO_SDKROOT'], '--show-sdk-version']),
        'architecture': output(['uname', '-m']),
    }


def validate(profile):
    manifest = json.loads(Path(str(profile) + '.json').read_text())
    if manifest['identity'] != identity():
        raise ValueError('stale profile: source, compiler, SDK, or flags changed; run pgo-train again')
    if manifest['profile_sha256'] != sha(profile):
        raise ValueError('profile checksum mismatch; run pgo-train again')
    tool = output(['xcrun', '--find', 'llvm-profdata'])
    subprocess.run([tool, 'show', str(profile)], check=True, stdout=subprocess.DEVNULL)
    return manifest['profile_sha256']


def train(profile):
    profile.parent.mkdir(parents=True, exist_ok=True)
    before = identity()
    raw = Path(tempfile.mkdtemp(prefix='training-', dir=profile.parent)).resolve()
    env = dict(os.environ, LLVM_PROFILE_FILE=str(raw / '%m-%p.profraw'))
    # Each training run has a fresh directory. Old and failed runs cannot enter this merge.
    subprocess.run(['make', '-B', '-f', 'makefile_darwin_arm64', 'core-check',
                    'embedding-check', 'MODE=pgo-generate'], cwd=ROOT, env=env, check=True)
    if identity() != before:
        raise ValueError('source or build settings changed during training; retry')
    profiles = sorted(raw.glob('*.profraw'))
    if not profiles:
        raise ValueError('training produced no profiles')
    tool = output(['xcrun', '--find', 'llvm-profdata'])
    merged = raw / 'merged.profdata'
    subprocess.run([tool, 'merge', '-o', str(merged)] + [str(p) for p in profiles], check=True)
    manifest = {'identity': before, 'profile_sha256': sha(merged),
                'training': 'core-check and embedding-check; no benchmark timing workloads',
                'raw_profile_count': len(profiles)}
    merged.replace(profile)
    Path(str(profile) + '.json').write_text(json.dumps(manifest, indent=2) + '\n')
    print('Profile ready:', profile)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['train', 'validate'])
    parser.add_argument('profile', type=Path)
    args = parser.parse_args()
    try:
        if args.action == 'train':
            train(args.profile.resolve())
        else:
            print(validate(args.profile.resolve()))
    except (OSError, ValueError, KeyError, subprocess.CalledProcessError) as exc:
        print('PGO: ' + str(exc), file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
