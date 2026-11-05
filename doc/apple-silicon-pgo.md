# Optional profile-guided optimization

PGO uses execution counts to guide compiler decisions. It does not change the ordinary O1 default.
The workflow uses installed Apple Clang, `llvm-profdata`, Python 3, and SDK dependencies. It installs no software.
The generation and use modes both default to `-O2 -g` and keep separate object directories.

## Procedure

Run these commands from the repository directory:

```sh
make -f makefile_darwin_arm64 pgo-train MODE=pgo-generate
make -f makefile_darwin_arm64 core-check embedding-check MODE=pgo-use
python3 build-support/test-pgo.py
make -s -f makefile_darwin_arm64 print-binary MODE=pgo-use
```

Training forces a new instrumented build and runs core QA and embedding checks.
The profile runtime writes process/module-specific files into a fresh training directory.
Only files from that directory enter the merge. Previous runs cannot contaminate it.
A failed training command does not publish a replacement profile.
Successful training writes `build/pgo/current.profdata` and its `.json` manifest.
Pass `PROFILE=/absolute/path/name.profdata` to both commands to select another output.
Use the same compiler, SDK, and flag overrides for generation and use.
The validation test expects the default profile and default build settings.

The training corpus covers interpreter operations, native calls, and embedding behavior.
It is a correctness corpus, not a representative user application.
All six item 12 timing workloads remain separate from training.
PGO results therefore describe only this synthetic evaluation.

## Profile checks

The manifest records source/header hashes, build rules, fixture sources, compiler identity, SDK, architecture, and flags.
Profile-use builds validate the manifest and profile checksum before compilation.
`llvm-profdata show` also verifies that the installed tool can read the data.
Missing files, changed sources/settings, corrupt profiles, and incompatible formats stop the build with an error.
Retrain after these changes. An edit to the native makefile or profile helper also requires retraining.
Compiler profile mismatch diagnostics are errors.
The profile checksum is part of the configuration key, so replaced profiles select separate objects.

Ordinary baseline, release, debug, and sanitizer modes do not read a profile or require Python for profile validation.
Raw and merged profiles remain under ignored `build/` directories by default.
Direct execution of a generation binary writes into `build/pgo/raw` unless `LLVM_PROFILE_FILE` overrides that path.
Profiles are local build artifacts; do not use them as portable release inputs across toolchains.

## Measurement

Use [the benchmark runner](../benchmarks/README.md) with baseline, `release-o2`, and `pgo-use` binary paths.
Compare PGO with O2 to isolate the profile effect, and with O1 to compare the ordinary default.
Do not train on the evaluation workloads before measuring them.
Retain debug symbols and keep fast-math disabled.

The workflow follows [Clang's profile-guided optimization documentation](https://clang.llvm.org/docs/UsersManual.html#profile-guided-optimization).

See [the two-session evaluation](../benchmarks/results/2026-11-05-pgo.md) for recorded results and the decision to retain PGO as optional.
