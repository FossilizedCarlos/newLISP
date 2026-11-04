#!/bin/sh
# Discover existing dependencies. Do not install packages.
set -eu
output=$1
mkdir -p "$(dirname "$output")"
probe_dir=$(mktemp -d "${TMPDIR:-/tmp}/newlisp-deps.XXXXXX")
trap 'rm -rf "$probe_dir"' EXIT HUP INT TERM
cat > "$probe_dir/probe.c" <<'C'
#include <readline/readline.h>
#ifdef NEWLISP_FFI_FLAT_HEADER
#include <ffi.h>
#else
#include <ffi/ffi.h>
#endif
int main(void)
{
    void *code;
    ffi_closure *closure = ffi_closure_alloc(sizeof(ffi_closure), &code);
    if (!closure) return 1;
    ffi_closure_free(closure);
    return readline == 0;
}
C
try_dependencies()
{
    # Flag variables intentionally use shell word splitting, as compiler flags do.
    if $CC $CPPFLAGS $CFLAGS $dep_cppflags -isysroot "$SDKROOT" -arch arm64 "$probe_dir/probe.c" \
        $LDFLAGS $dep_ldflags -arch arm64 $LDLIBS -lreadline -lffi -o "$probe_dir/probe" \
        >> "$probe_dir/probe.log" 2>&1; then
        printf 'DEP_CPPFLAGS := %s\nDEP_LDFLAGS := %s\n' "$dep_cppflags" "$dep_ldflags" > "$output"
        return 0
    fi
    return 1
}
# Explicit user flags and SDK headers take precedence.
dep_cppflags=
dep_ldflags=
if try_dependencies; then exit 0; fi
dep_cppflags=-DNEWLISP_FFI_FLAT_HEADER
if try_dependencies; then exit 0; fi
if command -v pkg-config >/dev/null 2>&1 && pkg-config --exists readline libffi; then
    dep_cppflags="-DNEWLISP_FFI_FLAT_HEADER $(pkg-config --cflags readline libffi)"
    dep_ldflags=$(pkg-config --libs readline libffi)
    if try_dependencies; then exit 0; fi
fi
if command -v brew >/dev/null 2>&1; then
    readline_prefix=$(brew --prefix readline 2>/dev/null || true)
    ffi_prefix=$(brew --prefix libffi 2>/dev/null || true)
    if [ -d "$readline_prefix" ] && [ -d "$ffi_prefix" ]; then
        dep_cppflags="-DNEWLISP_FFI_FLAT_HEADER -I$readline_prefix/include -I$ffi_prefix/include"
        dep_ldflags="-L$readline_prefix/lib -L$ffi_prefix/lib"
        if try_dependencies; then exit 0; fi
    fi
fi
cat "$probe_dir/probe.log" >&2
printf '%s\n' 'Cannot link ARM64 Readline and libffi with the selected compiler and flags.' \
    'Set CPPFLAGS and LDFLAGS for compatible installed libraries. No packages were installed.' >&2
exit 1
