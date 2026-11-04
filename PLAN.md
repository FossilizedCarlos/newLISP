# Apple Silicon implementation status

Status: Approved on 2026-11-04. Implementation in progress.

The [detailed plan](Updating%20newLISP%20for%20Apple%20Silicon.md) defines each item and its verification.
Complete and commit each item before starting the next item.

- Planning commit: `ea0f278`.
- Ignore rules: `2554046`; checked for whitespace errors and tracked-file matches.
- Item 1: `5ec957a`. Complete. Baseline `make` exits 2 at the unavailable legacy callback API. Runtime checks are blocked.
- Item 5: `0b221eb`. Complete. Native build, 1,000 callback calls, repeat registration, `qa-dot`, and `qa-libffi` pass.
  A temporary injected closure-preparation failure returns an error and permits successful registration on retry.
  Its first test script used unsupported `(env name nil)`; changing the test to an empty value resolves that harness error.
  Published callbacks retain interpreter lifetime. Cleanup releases unpublished closure allocations on failure.
  Sanitizer verification follows in item 7. Other platforms were not executed.
- Item 2: `5695445`. Complete. Two builds failed: missing explicit SDK, then stale copied build rules.
  Build attempts stopped for review. Revised configuration uses a forwarding include and explicit SDK.
  Recovery succeeded. `make`, explicit `make arm64`, compiler/flag overrides, and `qa-dot` pass.
  `file`, `lipo`, and `otool` confirm ARM64 and SDK libraries. Feature reporting includes UTF-8 and libffi.
  Switching configurations restores the baseline with zero recompilations. A missing library correctly blocks the dependency probe.
  Native cleanup is limited to generated outputs. Legacy selection paths were inspected, not executed.
  Item 2 is complete after recovery.
- Item 3: `dfae72a`. Complete. Portable FFI and callback tests pass using configuration-local fixture output.
  Intentional assertion failures and legacy errors with exit zero both produce a failing driver status.
  Corrected fixture C prototypes to match their declared FFI types.
- Item 4: `4b2e1f1`. Complete. ASan reproduces the old return-buffer overflow; the corrected FFI suite passes under ASan.
  Return storage meets the prepared size, register-size minimum, and alignment.
  The argument vector now follows the prepared count. Regressions cover 24-byte returns and 20 arguments.
- Item 6: `aa3fb24`. Complete. Explicit variadic marker approved by the user and implemented.
  Mixed variadic calls, legacy machine-word calls, invalid floating arguments, structures, and existing callbacks pass.
  The complete FFI fixtures pass normally and under ASan. The libc variadic test passes with its declared boundary.
  Added its missing completion marker after the QA driver correctly rejected incomplete success reporting.
  Unknown native signatures cannot be introspected; caller obligations and unsupported aggregate callback returns are documented.
- Item 7: Complete. Named debug, ASan, and UBSan modes compile and link with separate configuration directories.
  Debug core QA passes. The QA driver detects intentional failures and existing sanitizer faults.
  UBSan finds signed overflow in `nl-math.c:368`; ASan finds a read underflow in `nl-filesys.c:666`.
  These defects block clean sanitizer suites and are assigned to items 8 and 9.
- Items 8–14: Pending.

One baseline setup command used a Python tar option unavailable in the installed Python.
The corrected extraction command succeeded. The baseline compilation failure is a recorded source defect.

Next action: Commit item 7, then reproduce and correct integer boundary behavior (item 8).
