#!/bin/sh
# Build and check the command-line release. No software is installed.
set -eu
cd "$(dirname "$0")/.."
[ "$(uname -s)-$(uname -m)" = Darwin-arm64 ] || {
    echo 'An ARM64 Mac is required.' >&2
    exit 1
}
version=10.7.5.1
name=newlisp-$version-macos-arm64
output=build/release
stage=$output/$name
release_make() {
    make -f makefile_darwin_arm64 "$@" MODE=baseline \
        CFLAGS='-O1 -g -mmacosx-version-min=27.0' LDFLAGS='-mmacosx-version-min=27.0'
}
release_make all
# Replace the inode after a changed build to avoid stale macOS signing caches.
binary=$(release_make -s print-binary)
replacement=$(mktemp build/release-binary.XXXXXX)
cp -p "$binary" "$replacement"
mv "$replacement" newlisp
release_make core-check embedding-check
mkdir -p "$stage/bin"
cp newlisp "$stage/bin/newlisp"
cp doc/release-$version.md "$stage/RELEASE-NOTES.md"
cp doc/COPYING doc/License.html "$stage/"
cat > "$stage/README.txt" <<'README'
newLISP 10.7.5.1 — unofficial Apple Silicon fork
Requires Apple Silicon and macOS 27 or later.

Run from this directory:
  ./bin/newlisp -v
  ./bin/newlisp
Enter (exit) to stop the interpreter.
You can copy bin/newlisp to a directory on your PATH.

See RELEASE-NOTES.md for changes, source, and version compatibility.
See COPYING and License.html for license terms.
README
"$stage/bin/newlisp" -v
"$stage/bin/newlisp" -n -e '(begin (println (+ 20 22)) (exit))'
# Normalize archive metadata. Do not change the compiled executable.
python3 - "$output" "$name" <<'PY'
import gzip
import pathlib
import sys
import tarfile
output, name = pathlib.Path(sys.argv[1]), sys.argv[2]
with (output / (name + '.tar.gz')).open('wb') as raw:
    with gzip.GzipFile(filename='', mode='wb', fileobj=raw, mtime=0) as compressed:
        with tarfile.open(fileobj=compressed, mode='w', format=tarfile.PAX_FORMAT) as archive:
            for path in sorted((output / name).rglob('*')):
                info = archive.gettarinfo(str(path), str(path.relative_to(output)))
                info.uid = info.gid = info.mtime = 0
                info.uname = info.gname = ''
                info.pax_headers = {}
                if path.is_file():
                    with path.open('rb') as data:
                        archive.addfile(info, data)
                else:
                    archive.addfile(info)
PY
(cd "$output" && shasum -a 256 "$name.tar.gz" > SHA256SUMS)
cat "$output/SHA256SUMS"
