#!/usr/bin/env python3
"""Check profile validation through the native make entry point."""
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parent.parent
PROFILE = ROOT / 'build/pgo/current.profdata'


def make(profile, *extra):
    return subprocess.run(['make', '-s', '-f', 'makefile_darwin_arm64', 'print-binary',
                           'MODE=pgo-use', 'PROFILE=' + str(profile), *extra],
                          cwd=ROOT, capture_output=True, text=True)


def reject(profile, message, *extra):
    p = make(profile, *extra)
    assert p.returncode != 0 and message in p.stderr, p.stdout + p.stderr


def main():
    valid = make(PROFILE)
    assert valid.returncode == 0, valid.stderr
    original = json.loads(Path(str(PROFILE) + '.json').read_text())
    with tempfile.TemporaryDirectory(prefix='validation-', dir=PROFILE.parent) as tmp:
        profile = Path(tmp) / 'test.profdata'
        manifest = Path(str(profile) + '.json')
        reject(profile, 'Missing or invalid PGO profile')
        ordinary = subprocess.run(['make', '-s', '-f', 'makefile_darwin_arm64',
                                   'print-binary', 'MODE=baseline', 'PROFILE=' + str(profile)],
                                  cwd=ROOT, capture_output=True, text=True)
        assert ordinary.returncode == 0, ordinary.stderr
        profile.write_bytes(PROFILE.read_bytes())
        reject(profile, 'Missing or invalid PGO profile')
        manifest.write_text(json.dumps(original))
        reject(profile, 'stale profile', 'CFLAGS=-O3 -g')
        stale = json.loads(json.dumps(original))
        stale['identity']['files']['newlisp.c'] = 'changed'
        manifest.write_text(json.dumps(stale))
        reject(profile, 'stale profile')
        manifest.write_text(json.dumps(original))
        profile.write_bytes(b'invalid profile')
        reject(profile, 'checksum mismatch')
        incompatible = json.loads(json.dumps(original))
        incompatible['profile_sha256'] = hashlib.sha256(profile.read_bytes()).hexdigest()
        manifest.write_text(json.dumps(incompatible))
        reject(profile, 'Missing or invalid PGO profile')
        tool = subprocess.check_output(['xcrun', '--find', 'llvm-profdata'], text=True).strip()
        subprocess.run([tool, 'merge', '-weighted-input=2,' + str(PROFILE), '-o', str(profile)], check=True)
        updated = json.loads(json.dumps(original))
        updated['profile_sha256'] = hashlib.sha256(profile.read_bytes()).hexdigest()
        manifest.write_text(json.dumps(updated))
        newer = make(profile)
        assert newer.returncode == 0, newer.stderr
        # Compare at the same path: only profile contents change the configuration key.
        profile.write_bytes(PROFILE.read_bytes())
        manifest.write_text(json.dumps(original))
        older = make(profile)
        assert older.returncode == 0 and older.stdout != newer.stdout, older.stdout + newer.stdout
    print('PGO validation SUCCESSFUL: missing files, stale source/settings, tampering, incompatible data, and content isolation')


if __name__ == '__main__':
    main()
