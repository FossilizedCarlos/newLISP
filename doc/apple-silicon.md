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
