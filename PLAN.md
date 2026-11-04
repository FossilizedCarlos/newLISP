# Apple Silicon implementation status

Status: Approved on 2026-11-04. Implementation in progress.

The [detailed plan](Updating%20newLISP%20for%20Apple%20Silicon.md) defines each item and its verification.
Complete and commit each item before starting the next item.

- Planning commit: `ea0f278`.
- Ignore rules: `2554046`; checked for whitespace errors and tracked-file matches.
- Item 1: `5ec957a`. Complete. Baseline `make` exits 2 at the unavailable legacy callback API. Runtime checks are blocked.
- Item 5: Complete. Native build, 1,000 callback calls, repeat registration, `qa-dot`, and `qa-libffi` pass.
  A temporary injected closure-preparation failure returns an error and permits successful registration on retry.
  Its first test script used unsupported `(env name nil)`; changing the test to an empty value resolves that harness error.
  Published callbacks retain interpreter lifetime. Cleanup releases unpublished closure allocations on failure.
  Sanitizer verification follows in item 7. Other platforms were not executed.
- Items 2–4 and 6–14: Pending.

One baseline setup command used a Python tar option unavailable in the installed Python.
The corrected extraction command succeeded. The baseline compilation failure is a recorded source defect.

Next action: Commit item 5, then implement item 2, the isolated native ARM64 build.
