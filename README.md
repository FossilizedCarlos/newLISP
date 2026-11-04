# newLISP Apple Silicon fork

[![Apple Silicon regression](https://github.com/FossilizedCarlos/newLISP/actions/workflows/apple-silicon.yml/badge.svg?branch=apple-silicon)](https://github.com/FossilizedCarlos/newLISP/actions/workflows/apple-silicon.yml)

This unofficial fork maintains newLISP 10.7.5 with native Apple Silicon builds and portability fixes.
The original source distribution is available from [SourceForge](https://sourceforge.net/projects/newlisp/files/).

## Build and test

On an ARM64 Mac with Apple command-line tools installed:

```sh
make
make -f makefile_darwin_arm64 core-check embedding-check
```

See [Apple Silicon build instructions](doc/apple-silicon.md) for dependencies, sanitizer modes, and shared-library use.
See [PLAN.md](PLAN.md) for completed work and remaining tasks.

## Repository

- [Source and branches](https://github.com/FossilizedCarlos/newLISP): `apple-silicon` is the default development branch.
- [GitHub Actions](https://github.com/FossilizedCarlos/newLISP/actions/workflows/apple-silicon.yml): native ARM64 build and regression checks.
- [Issues](https://github.com/FossilizedCarlos/newLISP/issues): bug reports and feature requests for this fork.
- [Pull requests](https://github.com/FossilizedCarlos/newLISP/pulls): proposed changes to this fork.
- [Releases](https://github.com/FossilizedCarlos/newLISP/releases): published releases, when available.

The `master` and `develop` branches retain the imported repository history.
The inherited Travis CI and AppVeyor configuration files remain in the source tree.
This fork does not advertise upstream Travis CI, AppVeyor, Codecov, or Gitter integrations as its own.

## Upstream resources

- [newLISP](http://www.newlisp.org/)
- [newLISP Forum](http://www.newlispfanclub.alh.net/)
- [Debian stable package](https://packages.debian.org/stable/newlisp): the distribution package, not a build of this fork.

## License

newLISP and Nuevatec are trademarks of Lutz Mueller.
See [COPYING](doc/COPYING) and [license information](doc/License.html) for the license terms.
