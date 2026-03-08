# Dockerfiles Layout

This directory has been split to keep active recipes at top level and archive older recipes under `legacy/`.

## Top-Level Policy

Top-level `Dockerfiles/` keeps only:

- Dockerfiles directly referenced by CI workflows.
- Dockerfiles where the base `FROM` image is parameterized via `ARG`.
- `Dockerfile-boast` (kept top-level by project decision).

## Active Dockerfiles (Top Level)

- `Dockerfile` (CI: runtime-lite)
- `Dockerfile-latex` (CI: latex)
- `Dockerfile-stages` (CI: oneapi)
- `Dockerfile-boast` (kept near CI-focused recipes)
- `Dockerfile-LARA` (`FROM ${BASE_IMAGE}`)
- `Dockerfile-LARA-sdk` (`FROM ${BASE_OS_IMAGE}`)
- `Dockerfile-LARA-sdk-2` (`FROM ${BASE_OS_IMAGE}`)
- `Dockerfile-ground` (`FROM ubuntu:${UBUNTULTS}.04`)
- `Dockerfile-ide-llm` (`FROM ${BASE_IMAGE}`)
- `Dockerfile-nvidia` (`FROM ${BASEIMAGE}`)
- `Dockerfile-oneapi-25.2` (`FROM $BASEIMAGE`)
- `Dockerfile-oneapi-25.2-ground` (`FROM ubuntu:${UBUNTULTS}.04`)

## Legacy Dockerfiles

Moved to `Dockerfiles/legacy/`:

- `Dockerfile-minimal`
- `Dockerfile-oneapi`
- `Dockerfile-oneapi-24`
- `Dockerfile-oneapi-25`
- `Dockerfile-oneapi-25.1`
- `Dockerfile-oneapi-25.1-ground`
- `Dockerfile-oneapi-base`
- `Dockerfile-oneapi-base-stages`
- `Dockerfile-oneapi-ground`
- `Dockerfile-oneapi-hpc-ground`
- `Dockerfile-oneapi-multi`
- `Dockerfile-sdk`
- `Dockerfile-sdk-ground`

## Notes

- Stage/option documentation comments added at the top of each Dockerfile were preserved during the move.
- Graph files (`dot.viz`, `dot.png`) are currently left at top level for reference.
