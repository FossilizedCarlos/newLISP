# Apple Silicon implementation status

Status: Approved implementation items 1–18, including 9a and 9b, are complete.
The user approved items 15–18 after the follow-up review.
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
Current next action: Review the final verification record below. No further interpreter change is approved.

## README badge update

The user requested badge links for this fork before publication.
The README now links its build badge to this repository's Apple Silicon workflow and branch.
Repository, issues, pull requests, releases, and license links point to this fork.
Inherited upstream service badges are removed instead of assigning unverified service identifiers.
The Debian package remains a labelled upstream resource, not a fork build badge.
Verification: Markdown whitespace checks, local link targets, and owner/branch checks.


## Follow-up code review — completed work

Review scope: native build rules, FFI preparation and calls, PGO profile handling, and measurement helpers.
This is a targeted review, not a complete audit of the interpreter.
Items 1–14 remain complete. The user approved items 15–18 for separate implementation and verification.
Implement and commit each approved item separately, in this order.

### Item 15 — Check structure argument buffer lengths

**Priority:** High. **Status:** Complete; reproduced under ASan.

`executeLibFFI` copies `ffiType->size` bytes from a Lisp string without checking its length.
With the existing fixture, the following call reads 12 bytes from a one-byte allocation:

```lisp
(struct 'clock "char" "int" "short int")
(import FIXTURE "addClock" "clock" "clock")
(addClock "")
```

ASan reports a heap-buffer-overflow in `executeLibFFI` through `memcpy`.
The first probe used unsupported `short`; the corrected `short int` declaration reproduces the memory fault.
The diagnostic is saved locally at `/tmp/newlisp-review-struct-asan.log`.

Reject string arguments whose payload is smaller than the required native structure before copying.
Preserve support for sufficiently large buffers and document raw-pointer caller obligations.

**Proof:** Add empty, one-byte-short, exact-size, larger, and embedded-NUL cases using the existing native fixture.
The short-buffer regression must fail before the fix and report a Lisp error after it.
Run FFI and core/embedding checks in baseline, ASan, and UBSan modes.

**Commit:** `Validate FFI structure argument lengths`

**Completion:** Structure-string arguments are length-checked before copying. Empty, short, exact-size, larger, and embedded-NUL cases pass. Forced baseline, ASan, and UBSan core and embedding suites pass. Raw-pointer storage remains a caller obligation.

### Item 16 — Reject truncated FFI signatures

**Priority:** Medium. **Status:** Complete; reproduced on the baseline binary.

`ffiPreparation` stops at `MAX_TYPE_ARGS` without rejecting remaining declaration tokens.
Importing `labs` with 32 `long` arguments followed by `NOT_A_TYPE` succeeds; the invalid trailing token is ignored.
The review imports this deliberately invalid signature without calling the native function.
A silently shortened signature can use the wrong ABI if later called.

Validate the complete declaration. Reject excess arguments rather than truncating them.
Keep variadic-marker checks active at the argument limit and preserve supported zero-argument syntax.

**Proof:** Test 31, 32, and 33 arguments, invalid trailing tokens, and markers around the limit.
Verify existing fixed and variadic fixtures under baseline and sanitizers.

**Commit:** `Reject oversized FFI signatures`

**Completion:** FFI preparation now rejects excess arguments and validates trailing declaration tokens. Boundary and variadic-marker regressions use fresh import contexts. Baseline, ASan, and UBSan FFI suites pass. Two initial harness failures were corrected as recorded in the plan.

### Item 17 — Reject unknown native build modes

**Priority:** Medium. **Status:** Complete; reproduced through make.

`MODE=assn` returns a build path successfully and falls through to O1 without sanitizer flags.
A misspelled sanitizer mode can therefore produce an ordinary binary without an error.

Validate MODE against the supported baseline, debug, sanitizer, release, and PGO names.
Report the supported values when a mode is unknown. Preserve explicit compiler/flag overrides.

**Proof:** Unknown and misspelled modes must fail before dependency probing or compilation.
Check each supported mode and confirm sanitizer flags remain present in compile and link commands.

**Commit:** `Validate native build mode names`

**Completion:** Unknown, empty, and multiple MODE values stop before dependency or profile checks. All nine supported modes retain compile and link flags. Explicit compiler and flag overrides pass. Run python3 build-support/test-native-build.py: three tests pass in isolated directories. PGO validation uses a fixture; no profile training or native compilation runs.

### Item 18 — Allow cleanup without a valid PGO profile

**Priority:** Low. **Status:** Complete; reproduced with a dry run.

`make -n -f makefile_darwin_arm64 clean MODE=pgo-use PROFILE=/tmp/newlisp-review-absent.profdata` fails at profile validation.
The profile check runs during makefile parsing, before the clean target can run.
No cleanup command was executed during this review.

Skip profile validation for a clean-only invocation. Keep validation for build and mixed clean/build requests.

**Proof:** Dry-run clean must work with missing, corrupt, or stale profiles.
Build requests and mixed goals must still reject those profiles.
Verify ordinary cleanup in an isolated generated-output directory.

**Commit:** `Allow PGO cleanup without profile data`

Item 16 verification adjustment: two harness attempts failed (protected `count`, then cached imports).
Revised verification uses a fresh context per signature and explicit declarations; native calls are never made with these signatures.

**Completion:** Clean-only PGO use skips profile validation. Default, build, and mixed goals still reject missing, corrupt, and stale profiles. Run python3 build-support/test-native-build.py: all four tests pass. Dry-run and actual cleanup pass in temporary directories. Cleanup removes build/arm64 and retains other outputs. The real validator uses a fixed test identity. No native compilation or profile training runs. Makefile changes invalidate existing profile manifests; train again before the next PGO build.


## Final verification — 2026-11-05

Items 15–18 have separate commits:

- Item 15: `476277f` — Validate FFI structure argument lengths.
- Item 16: `ba15632` — Reject oversized FFI signatures.
- Item 17: `8d2f13d` — Validate native build mode names.
- Item 18: `8521f3a` — Allow PGO cleanup without profile data.

[Hosted run 42000977154](https://github.com/FossilizedCarlos/newLISP/actions/runs/42000977154) passes for `8521f3a`.
Baseline, debug, ASan, and UBSan jobs pass core QA, embedding, architecture checks, and log upload.
All four log artifacts are present. GitHub API verification occurred on 2026-11-05.

Fresh local PGO verification also passes after the final makefile changes:

```sh
make -f makefile_darwin_arm64 pgo-train MODE=pgo-generate
make -f makefile_darwin_arm64 core-check embedding-check MODE=pgo-use
python3 build-support/test-pgo.py
python3 build-support/test-native-build.py
make -f makefile_darwin_arm64 all shared MODE=baseline
```

All commands exit zero. PGO training creates a new profile and manifest.
Profile-use core QA and embedding pass. Profile validation checks pass, and all four native build-rule tests pass.
The final command restores the ordinary O1 executable and shared library.
Existing compiler indentation and prototype warnings remain visible in the build logs.

Local logs:

- `/tmp/newlisp-final-pgo-train.log`
- `/tmp/newlisp-final-pgo-use.log`
- `/tmp/newlisp-final-validation.log`
- `/tmp/newlisp-final-baseline-restore.log`

No software was installed. No new benchmark measurements or performance claims are added.
Other architectures, shared-library unload/reload, and concurrent evaluation remain outside the verified scope.
Further interpreter optimization requires a separate proposal and approval.


## Approved memory safety fixes — 2026-11-06

### Item 21 — Bound empty symbol prefix comparisons

**Status:** Complete; verified.

Preserve empty symbol names and unsigned lexical ordering. Read the second prefix byte only for nonempty names at all shared lookup, insertion, and deletion sites.

**Proof:** First reproduce the existing ASan failure. Add empty, one-character, common-prefix, context, lookup, and deletion regressions; run them with forced baseline, ASan, and UBSan builds. Commit this item independently before item 22.

### Item 22 — Validate nested structure string buffers

**Status:** Complete; verified.

Check the available string payload before copying a nested FFI structure. Preserve documented raw integer-address behavior. Inspect related unpack bounds within this scope.

**Proof:** First reproduce the existing ASan failure. Test empty, short, exact, larger, embedded-NUL, multilevel, valid nested packing, and unpack boundaries. Force builds and run full baseline, ASan, and UBSan core and embedding suites after the final fix. Commit independently. No push, tag, release, or private-report changes.

**Execution notes:** Existing baseline accepts both probes; existing ASan aborts with heap-buffer-overflow for both. Logs: `/tmp/newlisp-memory-repro/{baseline,asan}-{symbol,nested}.log`. Existing sanitizer binary provenance is as described in the private review; subsequent checks use forced fresh builds. Items 19 and 20 remain deferred and their preexisting local-only changes are excluded from these commits.

Item 21 verification adjustment: two harness runs failed because `name` is not a newLISP symbol-name function (the first attempted correction misidentified shadowing). Re-plan: use `term`, confirmed in an isolated interpreter probe, then rerun all targeted modes. No source-change failure occurred.

Item 21 completion: guarded second-byte prefix reads preserve empty names and the existing unsigned ordering at find, insert, and delete. Forced `make -B` builds and symbol regression pass in baseline, ASan, and UBSan; logs `/tmp/newlisp-item21-{baseline,asan,ubsan}-{build,test}.log`.

Item 22 bounded unpack adjustment: ASan also reproduces a short string overread through `unpack outer ""` (log `/tmp/newlisp-memory-repro/asan-unpack.log`). `p_unpack` already computes string payload length but bypasses bounds on structure dispatch. Check the complete structure size before that dispatch; recursive unpack then stays inside that validated buffer. Integer addresses retain the existing caller-managed contract.

Item 22 completion: nested string copies reject payloads shorter than the nested structure and release the temporary output before raising the parameter error. Structure unpack dispatch checks its complete known string payload. Exact/larger buffers, embedded NULs, nested/multilevel packing, terminator exclusion, and live integer-address buffers pass. ASan targeted log: `/tmp/newlisp-item22-asan-test.log`.

Final verification: forced `make -B -f makefile_darwin_arm64 core-check embedding-check MODE=<mode>` passes for baseline, ASan, and UBSan. Each log contains 28 success markers and no sanitizer/runtime/failure diagnostic. Logs: `/tmp/newlisp-memory-final-{baseline,asan,ubsan}.log`. Baseline executable and shared library restored with `make ... all shared MODE=baseline` (log `/tmp/newlisp-memory-baseline-restore.log`). Existing compiler indentation/prototype warnings remain. No installations, pushes, tags, release changes, or private-report edits. Raw addresses still require callers to supply valid readable storage; unrelated FFI declaration/callback issues are outside this fix.
