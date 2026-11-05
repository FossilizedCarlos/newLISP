# Apple Silicon implementation status

Status: Approved on 2026-11-04. Items 1–14, including 9a and 9b, are complete.
Hosted ARM64 verification passes. Item 14 completes with the profiling-report option. The current review confirms passing baseline, debug, ASan, and UBSan core QA.
Earlier failures below describe the state at each commit, not the current test results.

The [detailed plan](Updating%20newLISP%20for%20Apple%20Silicon.md) defines each item and its verification.
Complete and commit each item before starting the next item.

## Completed work

Planning commit: `ea0f278`. Ignore rules: `2554046`.
The ignore rules were checked for whitespace errors and tracked-file matches.
Item 5 ran before item 2 to resolve the initial compilation blocker.
Items 9a and 9b were approved on 2026-11-04.

### Item 1 — Establish a reproducible baseline

**Status:** Complete. **Commit:** `5ec957a`.

Baseline `make` exits 2 at the unavailable legacy callback API. Runtime checks are blocked.

One baseline setup command used a Python tar option unavailable in the installed Python.
The corrected extraction command succeeded. The baseline compilation failure is a recorded source defect.

### Item 2 — Add the native ARM64 executable build

**Status:** Complete. **Commit:** `5695445`.

Two builds failed: missing explicit SDK, then stale copied build rules.
Build attempts stopped for review. Revised configuration uses a forwarding include and explicit SDK.
Recovery succeeded. `make`, explicit `make arm64`, compiler/flag overrides, and `qa-dot` pass.
`file`, `lipo`, and `otool` confirm ARM64 and SDK libraries. Feature reporting includes UTF-8 and libffi.
Switching configurations restores the baseline with zero recompilations. A missing library correctly blocks the dependency probe.
Native cleanup is limited to generated outputs. Legacy selection paths were inspected, not executed.
Item 2 is complete after recovery.

### Item 3 — Make FFI regression fixtures portable

**Status:** Complete. **Commit:** `dfae72a`.

Portable FFI and callback tests pass using configuration-local fixture output.
Intentional assertion failures and legacy errors with exit zero both produce a failing driver status.
Corrected fixture C prototypes to match their declared FFI types.

### Item 4 — Correct FFI return storage

**Status:** Complete. **Commit:** `4b2e1f1`.

ASan reproduces the old return-buffer overflow; the corrected FFI suite passes under ASan.
Return storage meets the prepared size, register-size minimum, and alignment.
The argument vector now follows the prepared count. Regressions cover 24-byte returns and 20 arguments.

### Item 5 — Modernize macOS callback allocation

**Status:** Complete. **Commit:** `0b221eb`.

Native build, 1,000 callback calls, repeat registration, `qa-dot`, and `qa-libffi` pass.
A temporary injected closure-preparation failure returns an error and permits successful registration on retry.
Its first test script used unsupported `(env name nil)`; changing the test to an empty value resolves that harness error.
Published callbacks retain interpreter lifetime. Cleanup releases unpublished closure allocations on failure.
Sanitizer verification follows in item 7. Other platforms were not executed.

### Item 6 — Resolve untyped and variadic ABI behavior

**Status:** Complete. **Commit:** `aa3fb24`.

Explicit variadic marker approved by the user and implemented.
Mixed variadic calls, legacy machine-word calls, invalid floating arguments, structures, and existing callbacks pass.
The complete FFI fixtures pass normally and under ASan. The libc variadic test passes with its declared boundary.
Added its missing completion marker after the QA driver correctly rejected incomplete success reporting.
Unknown native signatures cannot be introspected; caller obligations and unsupported aggregate callback returns are documented.

### Item 7 — Add debug and sanitizer build modes

**Status:** Complete. **Commit:** `84c5e8e`.

Named debug, ASan, and UBSan modes compile and link with separate configuration directories.
Debug core QA passes. The QA driver detects intentional failures and existing sanitizer faults.
UBSan finds signed overflow in `nl-math.c:368`; ASan finds a read underflow in `nl-filesys.c:666`.
These defects block clean sanitizer suites and are assigned to items 8 and 9.

### Item 8 — Correct integer arithmetic edge cases

**Status:** Complete. **Commit:** `ca16571`.

Integer boundaries, float behavior, and 10,000-case bigint QA pass under UBSan.
Defined wrapping arithmetic, validated shift counts, handled minimum/-1 division, and corrected float saturation.
The wider UBSan suite proceeds past arithmetic and stops at the known item 9 line-reading fault.

### Item 9 — Correct input and memory portability faults

**Status:** Complete. **Commit:** `59612b5`.

ASan reproduces `read-line` index -1 reads for an empty line and a leading NUL byte.
Both bounds are checked before the newline and carriage-return tests. NUL truncation behavior is unchanged.
With that fix, ASan reaches a `t-test` overread in `qa-dot` when the first sample is longer.
The cross-product loop is bounded by both sample lengths; it is used only for equal-length dependent samples.
Each regression fails under ASan before its fix and passes after it.
Debug and UBSan core QA pass. ASan core QA passes through `qa-dot` and stops at the XML parser (item 9a).
ASan also finds a bigint division fault in `qa-longnum` and `qa-bigint` (item 9b).

### Item 9a — Bound XML parser reads

**Status:** Complete. **Commit:** `40e4e8a`.

ASan reproduces XML parser overreads for `<a/>`, `<a`, and `<!--x`.
Parse-position checks use bounded comparisons. The not-found check precedes the self-closing check.
A probe found `<!-->` and `<!--->` produce a negative comment length; overlapping terminators are now rejected.
The regression fails under ASan before the fix and passes after it. Valid parse results are unchanged.
Debug and UBSan core QA pass. ASan core QA passes `qa-xml`, then stops at `divModBigint` (item 9b).

### Item 9b — Size bigint division storage

**Status:** Complete. **Commit:** `e99fdd8`.

ASan reproduces three `divModBigint` faults with isolated divisions:
quotient writes past its storage when both operands have the same digit count, `(/ 30000000000000000000L 10000000000000000000L)`;
a product carry writes past its storage when `ny == nx`, `(/ 999999999L 600000000L)`;
zero trimming reads past the remainder when it is zero over all digits, `(% big big)`.
Quotient storage holds `nx - ny + 1` digits, product storage holds `nx + 1` digits, and trimming checks the bound first.
The regression covers each case and checks `q*y + r = x` and `|r| < |y|` for 2,000 seeded random operand pairs.
It fails under ASan before the fix and passes after it.
Default, debug, UBSan, and ASan core QA pass, including 10,000-case bigint QA. No sanitizer diagnostics remain in core QA.
Residual risk: GNU Make 3.81 compares whole-second timestamps. An edit in the same second as a build is not recompiled.
Two before/after checks were affected and repeated after deleting the generated object.

### Item 10 — Validate shared-library loading and embedding

**Status:** Complete. **Commit:** `025cb5e`.

The ARM64 dynamic library uses separate library objects and an `@rpath` install name.
The C host and newLISP loader verify initialization, evaluation, UTF-8, persistent state, error recovery, and callbacks.
Baseline, debug, ASan, and UBSan embedding checks pass. Debug and sanitizer core QA also pass after forced rebuilds.
`file`, `lipo`, and `otool` confirm native ARM64 and expected SDK dependencies.
The first fixture expected `length` to count characters; it was corrected to use `utf8len`.
The API has no shutdown entry point. Tests retain the library until process exit; unload/reload is not claimed.

Add the corresponding ARM64 shared-library build with isolated objects and consistent dependency discovery.
Add a small C embedding fixture and newLISP shared-library loading tests.
Verify initialization, evaluation, return handling, and shutdown where supported by the existing API.

**Proof:** Inspect library architecture and dependencies. Run the embedding and loading fixtures natively in normal and sanitizer modes.

**Commit:** `Support native ARM64 embedding and library loading`

### Item 11 — Add native ARM64 continuous integration

**Status:** Complete. **Implementation commit:** `0edef09`.

The workflow is `.github/workflows/apple-silicon.yml`. It selects the standard ARM64 `macos-15` runner.
Repository metadata confirms a public, active repository with `apple-silicon` as its default branch.
The matrix covers baseline, debug, ASan, and UBSan; each runs core QA and embedding checks.
It verifies binary architecture, retains logs for seven days, and installs no packages.
YAML syntax, trigger structure, matrix values, and pinned action references pass local checks.
The workflow's extracted baseline shell script passes locally. Other matrix commands passed during item 10.
[Hosted run](https://github.com/FossilizedCarlos/newLISP/actions/runs/41861645177), attempt 2, passes all four jobs for commit `74f40b0`.
Each job passes toolchain checks, core QA, embedding checks, architecture checks, and log upload.
All four log artifacts are present. The initial runner-capacity failures were resolved by the rerun.
Verified through the GitHub API on 2026-11-05.

Select an available native ARM64 runner after checking repository access, runner availability, and cost.
Configure correctness and sanitizer jobs with preserved logs and test reports.
Document any CI dependency installation explicitly; obtain approval before introducing installation commands.
Include existing QA, FFI fixtures, integer and input boundaries, and embedding checks.

**Proof:** Observe a real native ARM64 CI run and inspect its results.
If a runner is unavailable, record the blocker and do not claim CI verification is complete.

**Commit:** `Add native Apple Silicon regression CI`

### Item 12 — Measure and select release optimization

**Status:** Complete.

Four candidates pass forced core and embedding QA. Six synthetic workloads pass under ASan and UBSan.
Two sessions use warmups and nine measured runs per candidate/workload pair.
The O2 elapsed-time reductions are 4.91% and 4.48%; neither meets the predefined five-percent threshold.
The default remains baseline O1. Explicit O2, O3, and ThinLTO modes retain symbols and separate objects.
[Measurements and raw data](benchmarks/results/2026-11-05.md) record timing, variation, memory, hashes, and environment.


Add reproducible benchmark workloads for evaluation, allocation, lists, symbols, numeric operations, and FFI.
Use synthetic workloads as selected by the user. Do not claim gains for real user programs.
Compare the correctness baseline with `-O2`, `-O3`, and supported LTO configurations.
Use warmups, repeated runs, identical inputs, and recorded hardware and toolchain settings.
Measure elapsed time, variability, and relevant memory use. Preserve symbols for profiling.
Select the default from measured results. Keep `-ffast-math` disabled.

**Proof:** Run the complete applicable regression suite for each candidate and publish commands and measurements.
Reject apparent improvements that are within measurement noise or change results.

**Commit:** `Add measured release build options`

### Item 13 — Add optional profile-guided optimization

**Status:** Complete.

Generation, training, merge, and profile-use core/embedding checks pass with installed LLVM tools.
Profile rejection tests pass, including changed sources/settings, missing/corrupt data, and content-based object isolation.
Two nine-repeat sessions evaluate six held-out synthetic workloads against O1 and plain O2.
PGO takes 2.59% and 2.12% more aggregate elapsed time than plain O2, with a repeated FFI regression.
PGO remains optional. The ordinary default remains O1.
[Results and raw data](benchmarks/results/2026-11-05-pgo.md) include the training manifest and graph.
One QA repeat failed the existing UDP tests; the complete rerun passes unchanged. Its cause is not established.


Use O2 for both instrumented and profile-use builds. Keep the ordinary O1 default independent of profiles.
Train with core QA and embedding fixtures; reserve all six item 12 timing workloads for evaluation only.
Record source/header hashes, compiler identity, SDK, flags, and profile checksum in a manifest.
Reject missing, changed, or incompatible profiles before compilation. Include the profile checksum in the object directory key.
Verify rejection paths and run core and embedding checks on the profile-use build.
Compare held-out results with both O1 and plain O2 to separate optimization-level effects from profile effects.


Provide separate profile-generation and profile-use configurations with distinct output directories.
Train on representative workloads and evaluate on separate workloads.
Handle missing, stale, or incompatible profiles explicitly. Keep ordinary release builds independent of profiles.

**Proof:** Complete an instrumented build, training run, profile merge, and optimized rebuild with the installed LLVM tools.
Run regression tests and compare held-out benchmark results against the selected release baseline.

**Commit:** `Add optional profile-guided optimization`

## Profiling conclusion

Complete and commit each item before starting the next item.

### Item 14 — Profile and optimize one demonstrated bottleneck

**Status:** Complete: profiling-report option.

All 12 native profiles have checked workload results. No specific optimization has a demonstrated benefit.
[Report and next experiments](benchmarks/results/2026-11-05-profiles.md) preserve raw profiles and a graph.
Interpreter edits require a separate concrete proposal and approval.

Use the installed macOS `sample` tool because `xctrace` is unavailable. Install no tools.
Collect two three-second profiles for each synthetic workload on the ordinary O1 baseline.
Keep the same checked results, increase workload duration, and retain raw call trees and binary identity.
Separate inclusive call-tree counts from leaf samples; do not treat sampling counts as speedup measurements.
Review the dominant functions in source before proposing a narrowly scoped change.


Collect native profiles from representative workloads.
Select an internal change only after identifying a dominant cost in evaluation, allocation, traversal, or symbol lookup.
Present the measured hotspot and proposed change for approval before editing interpreter internals.
If no useful optimization is supported, commit the profiling report and recommendations instead.
Further independent optimizations require new plan items and separate commits.

**Proof:** Preserve program results, pass normal and sanitizer regression suites, and demonstrate a repeatable performance benefit.
Report regressions and tradeoffs, including memory use and maintenance cost.

**Commit:** `Optimize the measured interpreter bottleneck`, or `Document interpreter profiling results`

## Benchmark workloads (item 12)

User decision on 2026-11-04: use synthetic benchmarks. No real user programs are available yet.
The archived newlisp.org Docs page lists manuals, translations, videos, and one script (`gc.txt`).
`gc.txt` counts Google search hits over the network and is not a repeatable benchmark.
Code Patterns and the manual are already in `doc/`; their examples may supply synthetic workload shapes.
Report all benchmark results as synthetic.

## Review after the Opus handoff

Reviewed commits `59612b5`, `40e4e8a`, `e99fdd8`, and `0313669` against the source and working agreement.
No additional code defect was found in those changes.
Forced rebuilds avoid relying on the previous objects or whole-second timestamps:

```sh
make -B -f makefile_darwin_arm64 core-check MODE=baseline
make -B -f makefile_darwin_arm64 core-check MODE=debug
make -B -f makefile_darwin_arm64 core-check MODE=asan
make -B -f makefile_darwin_arm64 core-check MODE=ubsan
```

All four commands exit zero. ASan and UBSan report no diagnostics in the core suite.
A temporary independent test compares 300 signed divisions, with operands up to 100 decimal digits, against Python integer results.
Both sanitizer builds match every quotient and remainder. The Python reference truncates quotients toward zero, as newLISP does.
Review logs are in `/tmp/newlisp-opus-review/` and are local temporary artifacts.
These results do not cover other architectures or tests outside the core suite.

The review updates documentation only. The agent instruction file remains unchanged.
Next action: Select a follow-up experiment from the native profiling report; no interpreter change is approved.

## README badge update

The user requested badge links for this fork before publication.
The README now links its build badge to this repository's Apple Silicon workflow and branch.
Repository, issues, pull requests, releases, and license links point to this fork.
Inherited upstream service badges are removed instead of assigning unverified service identifiers.
The Debian package remains a labelled upstream resource, not a fork build badge.
Verification: Markdown whitespace checks, local link targets, and owner/branch checks.
