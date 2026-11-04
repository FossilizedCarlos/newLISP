# Apple Silicon implementation status

Status: Approved on 2026-11-04. Implementation in progress.

The [detailed plan](Updating%20newLISP%20for%20Apple%20Silicon.md) defines each item and its verification.
Complete and commit each item before starting the next item.

- Planning commit: `ea0f278`.
- Ignore rules: `2554046`; checked for whitespace errors and tracked-file matches.
- Item 1: Complete. Baseline `make` exits 2 at the unavailable legacy callback API. Runtime checks are blocked.
- Item 5: Next. Move before item 2 with user approval; record the reason in the detailed plan.
- Items 2–4 and 6–14: Pending.

One baseline setup command used a Python tar option unavailable in the installed Python.
The corrected extraction command succeeded. The baseline compilation failure is a recorded source defect.

Next action: Commit the baseline report, then modernize callback allocation and test native callbacks.
