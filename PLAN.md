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
- Item 7: `84c5e8e`. Complete. Named debug, ASan, and UBSan modes compile and link with separate configuration directories.
  Debug core QA passes. The QA driver detects intentional failures and existing sanitizer faults.
  UBSan finds signed overflow in `nl-math.c:368`; ASan finds a read underflow in `nl-filesys.c:666`.
  These defects block clean sanitizer suites and are assigned to items 8 and 9.
- Item 8: `ca16571`. Complete. Integer boundaries, float behavior, and 10,000-case bigint QA pass under UBSan.
  Defined wrapping arithmetic, validated shift counts, handled minimum/-1 division, and corrected float saturation.
  The wider UBSan suite proceeds past arithmetic and stops at the known item 9 line-reading fault.
- Item 9: `59612b5`. Complete. ASan reproduces `read-line` index -1 reads for an empty line and a leading NUL byte.
  Both bounds are checked before the newline and carriage-return tests. NUL truncation behavior is unchanged.
  With that fix, ASan reaches a `t-test` overread in `qa-dot` when the first sample is longer.
  The cross-product loop is bounded by both sample lengths; it is used only for equal-length dependent samples.
  Each regression fails under ASan before its fix and passes after it.
  Debug and UBSan core QA pass. ASan core QA passes through `qa-dot` and stops at the XML parser (item 9a).
  ASan also finds a bigint division fault in `qa-longnum` and `qa-bigint` (item 9b).
- Items 9a and 9b: Approved by the user on 2026-11-04.
- Item 9a: `40e4e8a`. Complete. ASan reproduces XML parser overreads for `<a/>`, `<a`, and `<!--x`.
  Parse-position checks use bounded comparisons. The not-found check precedes the self-closing check.
  A probe found `<!-->` and `<!--->` produce a negative comment length; overlapping terminators are now rejected.
  The regression fails under ASan before the fix and passes after it. Valid parse results are unchanged.
  Debug and UBSan core QA pass. ASan core QA passes `qa-xml`, then stops at `divModBigint` (item 9b).
- Item 9b: Complete. ASan reproduces three `divModBigint` faults with isolated divisions:
  quotient writes past its storage when both operands have the same digit count, `(/ 30000000000000000000L 10000000000000000000L)`;
  a product carry writes past its storage when `ny == nx`, `(/ 999999999L 600000000L)`;
  zero trimming reads past the remainder when it is zero over all digits, `(% big big)`.
  Quotient storage holds `nx - ny + 1` digits, product storage holds `nx + 1` digits, and trimming checks the bound first.
  The regression covers each case and checks `q*y + r = x` and `|r| < |y|` for 2,000 seeded random operand pairs.
  It fails under ASan before the fix and passes after it.
  Default, debug, UBSan, and ASan core QA pass, including 10,000-case bigint QA. No sanitizer diagnostics remain in core QA.
  Residual risk: GNU Make 3.81 compares whole-second timestamps. An edit in the same second as a build is not recompiled.
  Two before/after checks were affected and repeated after deleting the generated object.
- Items 10–14: Pending.

One baseline setup command used a Python tar option unavailable in the installed Python.
The corrected extraction command succeeded. The baseline compilation failure is a recorded source defect.

## Items 9a and 9b

Item 9 permits independent faults only as new plan items. ASan found two; both are approved and complete:

- 9a. Bound XML parser reads. `nl-xml-json.c` uses `memcmp` against the parse position (lines 222, 230, 370, 381),
  reads 3 bytes of a 2-byte close-tag literal (356), and reads `source[closeTag - 1]` before the not-found check (354).
  Reproduced: `(xml-parse "<a/>")`, `(xml-parse "<a")`, and `(xml-parse "<!--x")` abort under ASan; `qa-xml` aborts.
  Proposed fix: bounded string comparisons and the not-found check before the read. Proof: focused regression and `qa-xml` under ASan.
- 9b. Size bigint quotient storage. `divModBigint` writes `q[++sq]` beyond its `nx - ny + 1` entry `alloca` (`nl-math.c:4266`).
  Reproduced by `qa-longnum` and `qa-bigint` under ASan. The quotient digit count needs analysis before a fix.
  Proof: smallest failing division as a regression, 10,000-case bigint QA under ASan and UBSan.

## Benchmark workloads (item 12)

User decision on 2026-11-04: use synthetic benchmarks. No real user programs are available yet.
The archived newlisp.org Docs page lists manuals, translations, videos, and one script (`gc.txt`).
`gc.txt` counts Google search hits over the network and is not a repeatable benchmark.
Code Patterns and the manual are already in `doc/`; their examples may supply synthetic workload shapes.
Report all benchmark results as synthetic.

Next action: Commit item 9b, then validate shared-library loading and embedding (item 10).
