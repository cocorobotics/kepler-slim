# Contributing to kepler-slim

kepler-slim is an open-source **fork** of [kepler.gl](https://github.com/keplergl/kepler.gl).
Please keep contributions in the right place.

## Core kepler.gl features and bug fixes → upstream

This fork intentionally does **not** accept new core features. Anything that belongs in
kepler.gl itself — new layers, reducers, components, schema changes, core bug fixes — should be
contributed to the upstream project, where it will be reviewed and released:

- **Repository:** https://github.com/keplergl/kepler.gl
- Follow upstream's contribution process (DCO sign-off, commit conventions, tests).

Upstream changes are periodically merged down into this fork.

## Fork-specific changes → here

Open a pull request in this repository only for things specific to the slim fork:

- the slim build configuration (`esbuild/umd-slim.config.mjs`, the `build:umd:slim` script)
- release / CI automation (`.github/workflows/`)
- embedding docs and examples (`examples/hex-slim-embed/`, `SLIMMING.md`)
- this fork's README and docs

### How changes land

- `master` is protected — every change goes through a pull request.
- The **PR build check** must pass (it builds the slim bundle from your branch).
- PRs are reviewed and merged by the maintainers (the `coco-git-admin` team / `CODEOWNERS`).
- On merge, a new slim release is published automatically and the `LATEST` build URL is updated.

See [DEVELOPERS.md](./DEVELOPERS.md) for local build setup and
[SLIMMING.md](../SLIMMING.md) for how the slim build is produced.

## Code of Conduct

Help us keep this project open and inclusive — please read and follow our
[Code of Conduct](./CODE_OF_CONDUCT.md).
