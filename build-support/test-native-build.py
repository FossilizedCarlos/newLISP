#!/usr/bin/env python3
"""Check native make rules in temporary directories without compiling sources."""
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parent.parent
MODES = {
    'baseline': '-O1', 'debug': '-O0', 'asan': '-fsanitize=address',
    'ubsan': '-fsanitize=undefined', 'release-o2': '-O2',
    'release-o3': '-O3', 'release-lto': '-flto=thin',
    'pgo-generate': '-fprofile-instr-generate=',
    'pgo-use': '-fprofile-instr-use=',
}


class NativeBuildTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        shutil.copy(ROOT / 'makefile_darwin_arm64', self.root)
        support = self.root / 'build-support'
        support.mkdir()
        (support / 'apple-silicon-deps.sh').write_text(
            'echo probed > dependency-probe\nmkdir -p "$(dirname "$1")"\n'
            'printf "DEP_CPPFLAGS :=\\nDEP_LDFLAGS :=\\n" > "$1"\n')
        (support / 'pgo.py').write_text(
            'from pathlib import Path\nPath("profile-probe").touch()\nprint("test-profile")\n')
        for source in ROOT.glob('*.c'):
            (self.root / source.name).touch()

    def make(self, mode, *goals, overrides=()):
        return subprocess.run(
            ['make', '-n', '-f', 'makefile_darwin_arm64', 'CC=clang',
             'SDKROOT=/test-sdk', 'MODE=' + mode, *overrides, *goals],
            cwd=self.root, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

    def test_unknown_modes_stop_before_probes(self):
        for mode in ('assn', 'unknown', '', 'baseline debug', 'baseline unknown'):
            with self.subTest(mode=mode):
                result = self.make(mode, 'all')
                self.assertNotEqual(result.returncode, 0, result.stdout)
                self.assertIn('Supported modes: ' + ' '.join(MODES), result.stdout)
                self.assertFalse((self.root / 'dependency-probe').exists())
                self.assertFalse((self.root / 'profile-probe').exists())
                self.assertNotIn(' -c ', result.stdout)

    def test_supported_modes_keep_compile_and_link_flags(self):
        for mode, flag in MODES.items():
            with self.subTest(mode=mode):
                result = self.make(mode, 'all')
                self.assertEqual(result.returncode, 0, result.stdout)
                commands = [line for line in result.stdout.splitlines() if line.startswith('clang ')]
                self.assertTrue(any(' -c ' in line for line in commands), result.stdout)
                self.assertTrue(any(' -lm ' in line for line in commands), result.stdout)
                self.assertTrue(all(flag in line for line in commands), result.stdout)

    def test_explicit_flags_remain_in_commands(self):
        result = self.make('asan', 'all', overrides=(
            'CC=custom-clang', 'CPPFLAGS=-DUSER_FLAG', 'CFLAGS=-O0 -g3',
            'LDFLAGS=-L/custom', 'LDLIBS=-lcustom'))
        self.assertEqual(result.returncode, 0, result.stdout)
        commands = [line for line in result.stdout.splitlines() if line.startswith('custom-clang ')]
        self.assertTrue(commands, result.stdout)
        self.assertTrue(all('-O0 -g3' in line and '-fsanitize=address' in line for line in commands))
        self.assertIn('-DUSER_FLAG', result.stdout)
        self.assertIn('-L/custom', result.stdout)
        self.assertIn('-lcustom', result.stdout)


if __name__ == '__main__':
    unittest.main()
