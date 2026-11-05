# Synthetic release benchmarks

These workloads measure interpreter behavior. They do not represent a user application.
Every process checks a deterministic result and returns a nonzero status on failure.

- `evaluation`: recursive integer function calls.
- `allocation`: construct, map, sum, and release lists.
- `lists`: traverse a retained list repeatedly.
- `symbols`: retrieve values through dynamically resolved symbols.
- `numeric`: fixed-width integer arithmetic and remainder operations.
- `ffi`: typed calls to the native `labs` function.

The default scale is ten in the measurement runner. It makes process startup a small part of each observation.
The runner uses Python 3 standard-library modules and the installed macOS `/usr/bin/time` utility. It installs nothing.

## Procedure

Build and run `core-check embedding-check` for each mode before measuring:

```sh
make -B -f makefile_darwin_arm64 core-check embedding-check MODE=baseline
make -B -f makefile_darwin_arm64 core-check embedding-check MODE=release-o2
make -B -f makefile_darwin_arm64 core-check embedding-check MODE=release-o3
make -B -f makefile_darwin_arm64 core-check embedding-check MODE=release-lto
```

The modes use `-O1`, `-O2`, `-O3`, and `-O3 -flto=thin`, respectively. All retain `-g`.
Get each binary path with `make -s -f makefile_darwin_arm64 print-binary MODE=<mode>`.
Pass the paths to the runner:

```sh
python3 benchmarks/run.py \
  --candidate baseline=/absolute/path/to/baseline/newlisp \
  --candidate o2=/absolute/path/to/release-o2/newlisp \
  --candidate o3=/absolute/path/to/release-o3/newlisp \
  --candidate lto=/absolute/path/to/release-lto/newlisp \
  --output build/benchmarks/release.json
```

Use an otherwise idle machine. Do not run builds during measurement.
Each candidate/workload pair receives one warmup and nine measured runs.
A seeded shuffle interleaves pairs in each round to reduce ordering bias.
Elapsed time includes process startup and validation. Peak RSS is measured separately for each process.
The JSON records raw samples, medians, median absolute deviations, ranges, RSS, binary hashes, and toolchain details.

## Selection rule

Require at least a five-percent improvement in the geometric mean of workload median times before changing the default.
Reject a default candidate with a workload median regression above five percent.
Treat close results as inconclusive when the observed variation is comparable to the difference.
Prefer the less aggressive configuration when qualifying candidates are within three percent overall.
Confirm a proposed default with a second measurement session. Retain other candidates as explicit options.
Keep `-ffast-math` disabled. Do not infer real-program performance from these synthetic results.

## Recorded results

[2026-11-05 measurements](results/2026-11-05.md) retain the O1 default and expose the other modes as options.

## PGO evaluation

For item 13, train with core QA and embedding tests, then measure these six workloads without further training.
Compare `pgo-use` against both `baseline` and `release-o2`.
See the [PGO procedure](../doc/apple-silicon-pgo.md) for profile checks and build commands.
