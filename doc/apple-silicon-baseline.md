# Apple Silicon baseline

Date: 2026-11-04. Source commit: `2554046`.

## Environment

- Architecture: ARM64.
- macOS: 27.0.1, build 26A434.
- Compiler: Apple Clang 21.0.0, clang-2100.3.34.2.
- SDK: `/Library/Developer/CommandLineTools/SDKs/MacOSX.sdk`.
- SDK Readline compatibility headers and library are present.
- SDK libffi headers and library are present.
- Homebrew is present. Separate Readline, libffi, and pkgconf packages are not installed.
- No software was installed for this baseline.

## Reproduction

Run these commands from the repository. They build a temporary copy and leave the working tree unchanged.

```sh
baseline_dir=$(mktemp -d "${TMPDIR:-/tmp}/newlisp-baseline.XXXXXX")
git archive 2554046 | tar -x -C "$baseline_dir"
(cd "$baseline_dir" && make > baseline-build.log 2>&1)
```

`make` exits with status 2. Compilation stops in `nl-import.c` at line 582:

```text
error: call to undeclared function 'ffi_prep_closure'
```

The macOS code uses the legacy closure API. The ARM64 SDK exposes the supported allocation and closure-location API instead.
Other warnings include deprecated non-prototype calls and misleading indentation.

The build does not produce an executable. Runtime QA, callbacks, embedding, and performance checks are therefore blocked.
These checks are not passes. No runtime performance baseline exists yet.

The test scripts can create files, spawn subprocesses, and open local sockets.
Run baseline tests in an isolated source copy once compilation succeeds.
Avoid `make test` as the sole check: its output filter can hide the underlying command status.

## Planning adjustment

Move item 5, callback compatibility, before item 2. The user approved this change.
Validate callback allocation directly before the full regression fixtures become available.
Rerun the callback fixtures after item 3 and sanitizer checks after item 7.

## First working native reference

After callback modernization, the existing makefile builds an ARM64 executable successfully.
`newlisp -v` reports 64-bit, UTF-8, and libffi support.
`qa-dot` and `qa-libffi` report success with exit status zero.
The focused callback fixture passes 1,000 calls and repeated address lookup.
A temporary closure-preparation fault permits a successful retry after cleanup.
Published callbacks remain allocated for the interpreter lifetime, as native callers can retain their addresses.
Sanitizer checks and performance measurements remain pending.
