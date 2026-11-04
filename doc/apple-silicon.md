# Native Apple Silicon builds

Run `make` on an ARM64 Mac, or select `make arm64` explicitly.
The build requires the installed Apple command-line tools and compatible Readline and libffi libraries.
It does not install software.

The default compiler comes from `xcrun --find clang`.
The SDK comes from `SDKROOT`, or from `xcrun --sdk macosx --show-sdk-path`.
The SDK Readline compatibility library is sufficient; GNU Readline is not required.
Dependency discovery checks supplied flags and SDK headers first, then available package metadata and installed Homebrew prefixes.
A compile and link probe checks the ARM64 dependencies and closure API.

The build accepts `CC`, `CPPFLAGS`, `CFLAGS`, `LDFLAGS`, and `LDLIBS` overrides.
For example:

```sh
make arm64 CFLAGS='-O0 -g' CPPFLAGS='-DMY_BUILD=1'
```

Objects and dependency files reside under `build/arm64/<mode>/<configuration-hash>`.
Changing the compiler, SDK, or flags selects a separate configuration.
The final executable is also copied to `./newlisp` for compatibility with existing QA scripts.
The build retains debug symbols and enables 64-bit cells, UTF-8, Readline, and FFI.
The initial optimization level remains `-O1` until benchmark evidence supports a release default.

On native ARM64 macOS, `make clean` removes the ARM64 build directory and known top-level generated outputs.
Other platforms retain their existing build paths. They have not been executed during this work.

Check architecture and features with:

```sh
file newlisp
lipo -archs newlisp
otool -L newlisp
./newlisp -v
./newlisp qa-dot
```

Run portable FFI and callback fixtures with:

```sh
make -f makefile_darwin_arm64 ffi-check
```

The fixture uses the selected compiler, SDK, architecture, and flags. Its library and logs reside in the configuration directory.
The QA driver rejects nonzero exit status, legacy failure messages, and missing completion markers.

The FFI storage regression covers a 24-byte structure return and a 20-argument call.
Return storage follows the size, alignment, and register-width requirements in the [libffi calling documentation](https://www.chiark.greenend.org.uk/doc/libffi-dev/html/The-Basics.html).

## Native FFI signatures

Use typed imports for native functions. The declared types must match the C prototype.
For a variadic function, place `"..."` after the fixed argument types:

```lisp
(import "libc.dylib" "sprintf" "int" "char*" "char*" "..." "int" "double")
```

Each imported signature declares the full argument list for that call shape.
Use another context when you need a different signature for the same native symbol.
The marker requires at least one fixed argument and is valid only for imported functions.
After the marker, use promoted C types: `int` for narrow integers and `double` for `float`.
Unpromoted variadic types are rejected. Fixed-signature imports remain unchanged.
The implementation uses `ffi_prep_cif_var` for marked signatures.

A native symbol does not expose its C signature. The interpreter cannot detect a missing variadic marker automatically.
Calling a variadic function through an unmarked import remains invalid.

On Apple Silicon, legacy untyped imports support only machine-word integer and pointer signatures, with at most 14 arguments.
They now use libffi rather than non-prototype C calls.
Floating arguments and excess arguments produce errors. Migrate these calls to typed imports.
Untyped imports cannot infer narrow stack argument layouts, floating returns, structures, or variadic boundaries.
Use typed imports for those functions. Aggregate callback returns still require a separate audit; do not rely on them.

## Debug and sanitizer checks

```sh
make -f makefile_darwin_arm64 core-check MODE=debug
make -f makefile_darwin_arm64 core-check MODE=asan
make -f makefile_darwin_arm64 core-check MODE=ubsan
```

Each mode has separate objects. Sanitizer flags reach the executable and fixture library.
UBSan stops on the first diagnostic. Logs remain under the selected configuration directory.
`core-check` includes FFI, general primitives, dictionaries, XML, JSON, references, memory allocation, exceptions, floats, objects, and integers.
The general primitive suite uses local sockets and subprocesses.
Dedicated external-network, interactive, signal, process, and benchmark tests remain outside this core target.
Other operating systems and Intel macOS have not been executed.
The QA driver accepts the existing JSON test's misspelled completion marker but still rejects its failure marker.

Initial sanitizer findings:

- UBSan: signed overflow in `nl-math.c`, general primitive QA.
- ASan: stack-buffer underflow in `readStreamLine`, `nl-filesys.c`, general primitive QA.

These are source defects, not passing checks. Items 8 and 9 address them.
A temporary deliberate heap overflow confirmed that ASan reports a fault and returns a failing status.

## Integer boundaries

Fixed-width addition, subtraction, multiplication, negation, and increment/decrement use explicit unsigned arithmetic for wrapping results.
The minimum signed integer remains unchanged when negated or divided by `-1`; its remainder modulo `-1` is zero.
Its fixed-width absolute value also wraps to the same bit pattern.
Shift counts must be between 0 and 63. Other counts produce a range error, consistent with the documented valid range.
Right shift explicitly extends the sign bit.
Floating conversion saturates at the representable signed bounds, including the rounded upper-bound double.
NaN conversion remains zero.

The integer boundary, floating, and 10,000-case bigint tests pass under UBSan.
The full UBSan run then reaches the separately tracked line-reading defect.

## Input and memory faults

`read-line` no longer reads before its buffer for an empty line or a line that begins with a NUL byte.
A line that begins with a NUL byte is still truncated at that byte.
`t-test` no longer reads past the second sample when independent samples have different lengths. Results are unchanged.

`xml-parse` no longer reads past the document or a close-tag literal for empty elements and unterminated tags.
A comment whose `-->` overlaps its opening `<!--`, such as `<!-->`, is reported as a missing closing tag.

Debug and UBSan core QA pass. ASan core QA stops at bigint quotient storage in `divModBigint`.
