# HPCCM Dockerfile Generation

This directory contains HPCCM recipes used to generate BigDFT-related Dockerfiles.

## Status (March 8, 2026)

The top-level recipes were smoke-tested with:

- `hpccm 26.1.0`
- `python 3.12`

Working generation entrypoints:

- `hpccm_lsim-mpi.py`
- `hpccm_lsim-vsim.py`
- `hpccm_lsim-bigdft.py`

## Top-level Recipe Options (`--userarg`)

### `hpccm_lsim-mpi.py`

- `cuda`: CUDA version, e.g. `11.4.2`
- `ubuntu`: Ubuntu version, e.g. `20.04`
- `mpi`: `ompi`, `mvapich2`, `mvapich`, or `impi`
- `mpi_version`: MPI version string
- `target_arch`: architecture value used by the recipe (default `x86_64`)

### `hpccm_lsim-vsim.py`

- `cuda`
- `ubuntu`
- `mpi`
- `mpi_version`
- `tag`: base image used by the v_sim stage, e.g. `bigdft/sdk:latest`

### `hpccm_lsim-bigdft.py`

- `cuda`
- `ubuntu`
- `mpi`
- `mpi_version`
- `target_arch`
- `tag`: base image used for build stage, e.g. `bigdft/sdk_mpi:latest`
- `bigdft`: git branch/tag for BigDFT suite (default `devel`)

## `lsim_sdk` Script Options

The `lsim_sdk/*.py` scripts are executable Python generators (used directly by CI for SDK generation) and expose these CLI options:

- `--system`: `ubuntu` or `centos`
- `--system_version`: base distribution version
- `--cuda`: CUDA version, or `no`
- `--oneapi`: OneAPI selector, or `no`
- `--target_arch`: `x86_64`, `arm`, `ppc64le`
- `--jupyter`: `yes` or `no`
- `--blas`: `default`, `mkl`, `openblas`, `arm`
- `--python`: `default` or `intel`
- `--toolchain`: `gnu`, `intel`, `llvm`, `arm`, `ibm`
- `--toolchain_version`: optional compiler toolchain version
- `--intel_license`: optional (for legacy non-OneAPI Intel compiler path)
- `--mpi`: `ompi`, `intel`, `mvapich`
- `--mpi_version`: optional
- `--binary`: `yes` or `no` (use binary packages on non-x86 targets)
- `--format`: `docker` or `singularity`

## CI Values Currently Used

Values come from [`current_setup.sh`](../current_setup.sh) and matrices in [`sdk.yml`](../.github/workflows/sdk.yml) and [`runtime.yml`](../.github/workflows/runtime.yml).

### Global defaults (`current_setup.sh`)

- `BIGDFT_SYSTEM=centos`
- `BIGDFT_SYSTEM_VERSION=8`
- `BIGDFT_UBUNTU_VERSION=20.04`
- `BIGDFT_CUDA_VERSION=11.4.2`
- `BIGDFT_DEFAULT_MPI_FLAVOUR=ompi`
- `BIGDFT_OPENMPI_VERSION=4.1.1`
- `BIGDFT_MVAPICH2_VERSION=2.3.6`
- `BIGDFT_JUPYTER=yes`

### SDK workflow values (`.github/workflows/sdk.yml`)

- Matrix:
  - `mpi: [ompi]`
  - `arch: [x86_64, arm, ppc64le]`
- Per-arch toolchain profile:
  - `x86_64`: `toolchain=gnu`, `python=intel`, `blas=mkl`, `binary=no`
  - `arm`: `toolchain=arm`, `python=default`, `blas=arm`, `binary=no`
  - `ppc64le`: `toolchain=ibm`, `python=default`, `blas=openblas`, `binary=yes`

### Runtime workflow values (`.github/workflows/runtime.yml`)

- Matrix:
  - `mpi: [ompi]`
  - `arch: [x86_64, arm]`
- Runtime Dockerfile generation uses:
  - `cuda=${BIGDFT_CUDA_VERSION}`
  - `ubuntu=${BIGDFT_UBUNTU_VERSION}`
  - `mpi=ompi`
  - `mpi_version=${BIGDFT_OPENMPI_VERSION}`
  - `target_arch=${matrix.arch}`

## Install HPCCM

Use an isolated virtual environment:

```bash
python3 -m venv /tmp/hpccm-venv
/tmp/hpccm-venv/bin/pip install --upgrade pip
/tmp/hpccm-venv/bin/pip install hpccm
```

Check installation:

```bash
/tmp/hpccm-venv/bin/hpccm --version
```

## Generate Dockerfiles

Examples with Ubuntu 20.04, CUDA 11.4.2, OpenMPI 4.1.1:

```bash
# SDK + MPI recipe (multi-stage)
/tmp/hpccm-venv/bin/hpccm \
  --recipe hpccm_lsim-mpi.py \
  --userarg cuda=11.4.2 ubuntu=20.04 mpi=ompi mpi_version=4.1.1 \
  > Dockerfile_sdk

# v_sim recipe
/tmp/hpccm-venv/bin/hpccm \
  --recipe hpccm_lsim-vsim.py \
  --userarg cuda=11.4.2 ubuntu=20.04 mpi=ompi tag=bigdft/sdk:latest \
  > Dockerfile_vsim

# BigDFT runtime recipe
/tmp/hpccm-venv/bin/hpccm \
  --recipe hpccm_lsim-bigdft.py \
  --userarg cuda=11.4.2 ubuntu=20.04 mpi=ompi mpi_version=4.1.1 tag=bigdft/sdk_mpi:latest bigdft=devel \
  > Dockerfile_runtime
```

Build examples:

```bash
# Build only SDK stage from the multi-stage SDK recipe
docker build --file Dockerfile_sdk --target sdk --tag bigdft/sdk:test .

# Build final stage from a single-stage recipe
docker build --file Dockerfile_runtime --tag bigdft/runtime:test .
```

## Batch Build Script

`build.sh` still orchestrates generation and build of SDK, v_sim, and runtime images.

Example:

```bash
cuda_version="11.4.2" ubuntu_version="20.04" mpi="ompi" mpi_version="4.1.1" tag="bigdft" ./build.sh
```

## About `lsim_sdk/`

Files in `lsim_sdk/` are module-style building blocks, not direct `hpccm --recipe` entrypoints. They are imported and composed by Python code.
