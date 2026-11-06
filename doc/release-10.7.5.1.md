# newLISP 10.7.5.1 — Apple Silicon fork

This is an unofficial newLISP fork. The binary requires Apple Silicon and macOS 27 or later.
The release contains one ARM64 command-line executable. It does not contain an embedding library.

## Changes

- Add a native ARM64 build with UTF-8, Readline, and libffi support.
- Use supported libffi closure allocation and correct native argument and return storage.
- Require an explicit `"..."` marker for variadic typed imports. Use promoted C types after the marker.
- Reject invalid FFI types, argument counts, oversized signatures, and incorrect structure lengths.
- Limit untyped native calls to supported integer and pointer signatures. Use typed imports for other signatures.
- Preserve empty symbol names and bound symbol prefix comparisons.
- Reject short string buffers during nested structure packing and structure unpacking.
- Define integer boundary behavior and correct read-line, t-test, XML, and bigint memory faults.
- Add core, native-call, callback, embedding, AddressSanitizer, and UndefinedBehaviorSanitizer checks.
- Keep `-O1` as the default build. Add optional measured optimization modes and profile-guided optimization.

Performance depends on the program and hardware. This release makes no general speed claim.
Aggregate callback returns, concurrent embedding evaluation, and library unload/reload remain outside the verified scope.
See [Apple Silicon instructions](https://github.com/FossilizedCarlos/newLISP/blob/v10.7.5.1/doc/apple-silicon.md) for native-call rules and optional build modes.

## Version identifiers

The banner, package name, and CGI `SERVER_SOFTWARE` identify fork release `10.7.5.1`.
The numeric language version stays `10705` for compatibility with existing `sys-info` version checks.
The HTTP numeric version fields retain that same compatibility value.
Do not interpret the fork suffix as another digit in the numeric language version.
The inherited reference manual describes the upstream newLISP 10.7.5 language.
Existing newLISP dynamic scoping and value-copying behavior remain unchanged.

## Installation and use

1. Extract `newlisp-10.7.5.1-macos-arm64.tar.gz`.
2. Open the extracted directory in Terminal.
3. Run `./bin/newlisp -v` to check the version.
4. Run `./bin/newlisp` to start the interpreter.
5. Enter `(exit)` to stop the interpreter.

You can copy `bin/newlisp` to a directory on your `PATH`.
The executable uses the macOS system Readline and libffi libraries.
The archive does not include modules or the reference manual. Get them from the matching source tag.

## Build and package

Run `sh build-support/package-release.sh` on an ARM64 Mac with Apple command-line tools.
The script builds with `-O1` and an explicit macOS 27 deployment target.
It runs core and embedding checks before it creates the command-line archive.
The output directory is `build/release`. `SHA256SUMS` gives the archive checksum.
Archive timestamps and owners are normalized. Compiler and SDK differences can change the binary and checksum.

## License and source

See `COPYING` and `License.html` in the archive for license terms.
Matching source: <https://github.com/FossilizedCarlos/newLISP/tree/v10.7.5.1>.
