---
author: "T3 Code using GPT-6 Astra"
title: "Updating newLISP for Apple Silicon"
pubDatetime: 2026-11-04T14:45:49+03:00
description: "A staged plan for native ARM64 builds, FFI correctness, regression tests, and measured performance improvements."
tags:
- codex
- newlisp
---

## Status and build responsibility

The user approved implementation on 2026-11-04. The baseline build has run and failed as recorded below.

I will run `make` and inspect its output under the approved plan. You do not need to run it yourself.
I will also run the regression tests, sanitizer builds, and benchmarks described below.
I will request approval before installing software. Missing dependencies will be reported with the required package and purpose.
I will not run installation targets or publish changes as part of this plan.

The current machine reports ARM64 and Apple Clang 21.0.0 through `xcrun`.
Homebrew is available. `pkg-config` was not found on the current PATH.
Readline and libffi availability, versions, and architectures still require verification.

## Working agreement

Complete each numbered item, verify it, and commit it before starting the next item.
Use a concise commit title and a separate explanation with two `-m` arguments.
Each item below represents one planned implementation commit. Include its tests and documentation in that commit.
Record the commit hash, checks, failures, and remaining work in `PLAN.md`.
After two failed attempts on a step, stop and revise the plan with the user.
Request approval for material scope changes. Do not create empty commits for work that proves unnecessary.
Use Git commits as backups. Keep the original extracted distribution and archive unchanged.

The previously authorized `.gitignore` change was committed separately as `2554046`.

## Findings from the source

- `configure` selects `makefile_darwinLP64_utf8_ffi` for macOS without an architecture-specific branch.
- That makefile assigns `CC = cc`, uses `-m64 -O1`, and strips the executable.
- Build objects reside in the source directory and can be reused across incompatible configurations.
- `nl-import.c` allocates return storage with `sizeof(ffi->cif.rtype->size)`.
- The macOS callback path uses `mmap`, `ffi_prep_closure`, and `mprotect`.
- `qa-libffi` compiles its fixture with `-m32` or `-m64`.
- `make test` filters output through `grep`. It is not sufficient evidence that all tests pass.
- The current `clean` target removes broad filename patterns and changes permissions. Review it before use.

The earlier line-reading report was not supplied. Locate and reproduce the fault before describing it as confirmed.

## Implementation sequence

### 1. Establish a reproducible baseline

Record compiler, SDK, macOS, architecture, dependency versions, and current commit.
Inspect test side effects and execute the current build and applicable QA tests in an isolated temporary source copy.
Capture exact commands, exit status, and reported failures. Do not install missing dependencies automatically.
Add a baseline report with known failures and platform-specific exclusions.

**Proof:** Reproduce the report from recorded commands. Clearly distinguish blocked checks from passing checks.
**Commit:** `Document the Apple Silicon baseline`

### 2. Add the native ARM64 executable build

Add an Apple Silicon makefile and select it through `configure` and `Makefile`.
Default to Apple Clang discovered through `xcrun`. Compile and link with `-arch arm64`.
Preserve `NEWLISP64`, UTF-8, Readline, and FFI support.
Respect explicit `CC`, `CPPFLAGS`, `CFLAGS`, `LDFLAGS`, and `LDLIBS` settings without losing required architecture definitions.
Discover dependencies through supplied flags, available package metadata, SDK probes, and installed package prefixes.
Do not assume `/opt/homebrew` or `/usr/local`. Reject incompatible libraries with a useful diagnostic.
Use separate object directories for architecture and build mode. Track header dependencies.
Preserve Intel and non-macOS selection paths. Limit cleanup to known generated outputs.

**Proof:** Build natively; inspect the executable and dependencies with `file`, `lipo`, and `otool`.
Check UTF-8 and FFI feature flags, flag overrides, missing-library diagnostics, and configuration switching.
Inspect legacy build selection without claiming unexecuted platforms pass.
**Commit:** `Add a native Apple Silicon build`

### 3. Make FFI regression fixtures portable

Update fixture compilation to use the selected compiler, architecture, and dependency flags.
Add deterministic assertions and reliable failure exit codes to the new test entry point.
Cover existing supported scalar types, pointers, mixed integer and floating arguments, and callbacks.
Establish which structure operations the public API supports before adding structure cases.
Keep fixture output in the selected build directory.

**Proof:** Run fixture compilation and the FFI tests natively. Deliberately fail an assertion and confirm a nonzero exit status.
Record existing defects that later steps must resolve.
**Commit:** `Add native ARM64 FFI regression fixtures`

### 4. Correct FFI return storage

Replace the size-field allocation with storage that satisfies libffi return-size, register-width, and alignment requirements.
Handle void returns, narrow integers, floating returns, and supported aggregate returns explicitly.
Check allocation failures and temporary-storage lifetime.

**Proof:** Add regression cases for supported return categories, including values larger than the old allocation where supported.
Run the fixtures with AddressSanitizer and confirm the failing reproducer passes after the fix.
**Commit:** `Fix FFI return storage`

### 5. Modernize macOS callback allocation

Use `ffi_closure_alloc`, `ffi_prep_closure_loc`, and matching `ffi_closure_free` cleanup.
Keep writable and executable addresses distinct.
Audit callback ownership, registration lifetime, replacement, shutdown, and error paths before adding cleanup.
Preserve other platform behavior and avoid freeing callbacks still held by native code.

**Proof:** Execute repeated callback creation and calls on this ARM64 machine.
Exercise supported callback signatures, failure paths, and lifecycle operations under sanitizers.
**Commit:** `Use supported libffi closure allocation on macOS`

### 6. Resolve untyped and variadic ABI behavior

Audit legacy imports and variadic calls against the Apple ARM64 ABI and public newLISP documentation.
Use `ffi_prep_cif_var` where a known variadic signature requires it.
Do not infer a missing native signature from values alone.
For unsupported forms, propose explicit diagnostics and a migration path before changing public behavior.
Add supported structure argument and return tests; document unsupported forms without expanding the API implicitly.

**Proof:** Compare C fixture results with newLISP calls for fixed and variadic signatures, mixed types, and supported structures.
Confirm unsupported calls fail predictably rather than corrupting state.
**Commit:** `Define and verify Apple Silicon FFI call behavior`

### 7. Add debug and sanitizer build modes

Add separate debug, AddressSanitizer, and UndefinedBehaviorSanitizer configurations with symbols and useful stack traces.
Keep their objects separate from release objects. Retain a conservative optimization level during correctness work.
Add a test driver that checks exit status and failure markers without hiding errors through output filtering.
Document network, interactive, and platform-specific tests separately.

**Proof:** Confirm sanitizer flags reach compilation and linking. Verify a controlled temporary fault produces a failing check.
Run applicable existing QA and FFI regressions; record all remaining diagnostics.
**Commit:** `Add sanitizer builds and reliable QA execution`

### 8. Correct integer arithmetic edge cases

Reproduce signed overflow, invalid shifts, division boundaries, and conversion faults found by the audit.
Confirm intended newLISP semantics from documentation and existing tests before changing arithmetic.
Use defined C operations for required wrapping behavior. Do not suppress sanitizer findings as a substitute for a fix.

**Proof:** Test minimum and maximum integers, zero divisors, boundary shift counts, and conversions.
Run the arithmetic cases under UBSan and the complete applicable QA suite.
**Commit:** `Define integer boundary behavior`

### 9. Correct input and memory portability faults

Investigate the reported line-reading issue with empty lines, EOF, long lines, and buffer boundaries.
Audit pointer conversions, alignment, aliasing, and memory access on exercised paths.
Fix reproduced faults with focused regression cases.
If unrelated faults require several independent changes, propose additional plan items before implementation.

**Proof:** Reproduce each fault before its fix and rerun the same case afterward.
Run applicable QA and FFI tests under ASan and UBSan. Record residual risks and unsupported checks.
**Commit:** `Fix reproduced memory portability faults`

### 10. Validate shared-library loading and embedding

Add the corresponding ARM64 shared-library build with isolated objects and consistent dependency discovery.
Add a small C embedding fixture and newLISP shared-library loading tests.
Verify initialization, evaluation, return handling, and shutdown where supported by the existing API.

**Proof:** Inspect library architecture and dependencies. Run the embedding and loading fixtures natively in normal and sanitizer modes.
**Commit:** `Support native ARM64 embedding and library loading`

### 11. Add native ARM64 continuous integration

Select an available native ARM64 runner after checking repository access, runner availability, and cost.
Configure correctness and sanitizer jobs with preserved logs and test reports.
Document any CI dependency installation explicitly; obtain approval before introducing installation commands.
Include existing QA, FFI fixtures, integer and input boundaries, and embedding checks.

**Proof:** Observe a real native ARM64 CI run and inspect its results.
If a runner is unavailable, record the blocker and do not claim CI verification is complete.
**Commit:** `Add native Apple Silicon regression CI`

### 12. Measure and select release optimization

Add reproducible benchmark workloads for evaluation, allocation, lists, symbols, numeric operations, and FFI.
Request representative user programs and expected results before claiming gains for real workloads.
Compare the correctness baseline with `-O2`, `-O3`, and supported LTO configurations.
Use warmups, repeated runs, identical inputs, and recorded hardware and toolchain settings.
Measure elapsed time, variability, and relevant memory use. Preserve symbols for profiling.
Select the default from measured results. Keep `-ffast-math` disabled.

**Proof:** Run the complete applicable regression suite for each candidate and publish commands and measurements.
Reject apparent improvements that are within measurement noise or change results.
**Commit:** `Add measured release build options`

### 13. Add optional profile-guided optimization

Provide separate profile-generation and profile-use configurations with distinct output directories.
Train on representative workloads and evaluate on separate workloads.
Handle missing, stale, or incompatible profiles explicitly. Keep ordinary release builds independent of profiles.

**Proof:** Complete an instrumented build, training run, profile merge, and optimized rebuild with the installed LLVM tools.
Run regression tests and compare held-out benchmark results against the selected release baseline.
**Commit:** `Add optional profile-guided optimization`

### 14. Profile and optimize one demonstrated bottleneck

Collect native profiles from representative workloads.
Select an internal change only after identifying a dominant cost in evaluation, allocation, traversal, or symbol lookup.
Present the measured hotspot and proposed change for approval before editing interpreter internals.
If no useful optimization is supported, commit the profiling report and recommendations instead.
Further independent optimizations require new plan items and separate commits.

**Proof:** Preserve program results, pass normal and sanitizer regression suites, and demonstrate a repeatable performance benefit.
Report regressions and tradeoffs, including memory use and maintenance cost.
**Commit:** `Optimize the measured interpreter bottleneck`, or `Document interpreter profiling results`

## Completion criteria

The executable and shared library run natively on ARM64 with UTF-8 and FFI support.
All applicable regression checks pass in the selected release and sanitizer configurations.
Skipped or unavailable checks remain visible in the report.
CI results, benchmark evidence, dependency requirements, and reproduction commands are documented.
No performance improvement is claimed without measurement. Other architectures are not described as tested unless executed.

## Reference documents

- [Apple architectural differences](https://developer.apple.com/documentation/apple-silicon/addressing-architectural-differences-in-your-macos-code)
- [Clang optimization and profile-guided optimization](https://clang.llvm.org/docs/UsersManual.html#profile-guided-optimization)
- [libffi closure API](https://www.chiark.greenend.org.uk/doc/libffi-dev/html/The-Closure-API.html)

Recheck the applicable documentation and installed headers during implementation.
The closure API requires paired allocation and release, plus separate writable and executable addresses.

## Execution adjustments

### 2026-11-04: Callback compatibility precedes native-build verification

The baseline build fails because the ARM64 SDK does not declare legacy `ffi_prep_closure`.
The user approved moving item 5 before item 2 and authorized documented sequencing changes.
Execution order is now 1, 5, 2, 3, 4, then 6–14.
Item 5 uses a focused callback fixture first. Items 3 and 7 extend its regression and sanitizer verification.
See [the baseline report](doc/apple-silicon-baseline.md) for the reproduction and blocked checks.

### 2026-11-04: Native configuration recovery after two failed builds

Item 2 stopped after two failed build attempts.
The first attempt invoked the resolved Clang binary without an explicit SDK path, so SDK headers were unavailable.
The second attempt used the stale copy in `makefile_build`, which did not contain the SDK correction.

Revised item 2: select an explicit SDK and generate a forwarding include instead of copying the native makefile.
Make configuration depend on the native makefile. Verify regeneration before rebuilding.
This prevents stale build rules after source changes. The user authorized documented plan adjustments.
No runtime behavior or public API changes are added by this recovery.

### 2026-11-04: Include argument-vector storage in item 4

The FFI storage audit found a 16-entry argument vector, although prepared signatures permit 32 arguments.
Item 4 now sizes this vector from the prepared argument count.
A 20-argument regression accompanies the large-structure return test.
ASan reproduced the original return-buffer overflow before the fix.
The corrected FFI suite, callback fixture, and storage regressions pass under ASan.
