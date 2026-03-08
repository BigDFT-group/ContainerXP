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
- `Dockerfile-ground` (`FROM ${BASE_IMAGE}`)
- `Dockerfile-ide-llm` (`FROM ${BASE_IMAGE}`)
- `Dockerfile-nvidia` (`FROM ${BASEIMAGE}`)
- `Dockerfile-oneapi-25.2` (`FROM $BASEIMAGE`)
- `Dockerfile-oneapi-25.2-ground` (`FROM ubuntu:${UBUNTULTS}.04`)

## Dockerfile-ground Flavours

`Dockerfile-ground` is now the single source for ground image profiles.

### Canonical flavour names

- `ubuntu-system`
- `ubuntu-intelpython`
- `hpckit-intelpython`

### Flavour matrix

| Flavour | `BASE_IMAGE` | `PROFILE` | oneAPI apt | Intel GPU repo | CUDA repo/toolkit | Toolchain install | Intel Python | Intel PyPI stack |
|---|---|---|---|---|---|---|---|---|
| `ubuntu-system` | `ubuntu:24.04` | `ubuntu-system` | off | off | off | off (uses distro minimum deps) | off | off |
| `ubuntu-intelpython` | `ubuntu:24.04` | `ubuntu-intelpython` | on | on | on | on | on | off |
| `hpckit-intelpython` | `intel/oneapi-hpckit` | `hpckit-intelpython` | off | off | off | off | on | off |

### Build commands (copy/paste)

1. `ubuntu-system`

```bash
docker build -f Dockerfile-ground \
  --build-arg PROFILE=ubuntu-system \
  --build-arg BASE_IMAGE=ubuntu:24.04 \
  -t bigdft/ground:ubuntu-system .
```

2. `ubuntu-intelpython`

```bash
docker build -f Dockerfile-ground \
  --build-arg PROFILE=ubuntu-intelpython \
  --build-arg BASE_IMAGE=ubuntu:24.04 \
  -t bigdft/ground:ubuntu-intelpython .
```

3. `hpckit-intelpython`

```bash
docker build -f Dockerfile-ground \
  --build-arg PROFILE=hpckit-intelpython \
  --build-arg BASE_IMAGE=intel/oneapi-hpckit \
  -t bigdft/ground:hpckit-intelpython .
```

### Common optional overrides

Use these to specialize a flavour without creating a new Dockerfile.

```bash
# Ubuntu/oneAPI/CUDA selection
--build-arg UBUNTULTS=24
--build-arg UBUNTU_CODENAME=noble
--build-arg ONEAPI_VERSION=2025.2
--build-arg CUDATOOLKIT=12-5

# Explicit feature toggles (0/1)
--build-arg ENABLE_ONEAPI_APT=1
--build-arg ENABLE_INTEL_GPU_REPO=1
--build-arg ENABLE_CUDA=1
--build-arg ENABLE_TOOLCHAIN_INSTALL=1
--build-arg INSTALL_INTEL_PYTHON=0
--build-arg INSTALL_INTEL_PYPI_STACK=1

# Intel Python package pinning
--build-arg INTELPYTHON_PACKAGE_NAME=2025.1.0_196
--build-arg INTEL_DOWNLOAD_SHA=5c0778a5-6bf6-4286-a1b0-db6ea9dd899c
```

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

## Host GPU Prerequisites (for CUDA-enabled containers)

These steps are host-side requirements to run Docker containers with `--gpus ...`.

### 1) Install an NVIDIA driver on the host

- Install one NVIDIA driver branch and matching utils on your machine.
- Prefer the distribution-recommended driver for your GPU.
- Keep `nvidia-driver-XXX` and `nvidia-utils-XXX` on the same version.

Ubuntu helper:

```bash
ubuntu-drivers devices
```

### 2) Verify host GPU runtime

```bash
nvidia-smi
```

If `nvidia-smi` does not work, fix host driver installation before testing Docker GPU.

### 3) Install NVIDIA Container Toolkit (Docker runtime integration)

```bash
curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | \
  sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg

curl -s -L https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list | \
  sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | \
  sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list

sudo apt update
sudo apt install -y nvidia-container-toolkit
sudo nvidia-ctk runtime configure --runtime=docker
sudo systemctl restart docker
```

### 4) Verify Docker GPU access

```bash
docker run --rm --gpus all nvidia/cuda:12.5.0-base-ubuntu24.04 nvidia-smi
```

### 5) Choose `CUDATOOLKIT` for image builds

- Read CUDA runtime from host `nvidia-smi` output.
- Set Docker build arg as `X-Y` for CUDA `X.Y`.
  - Example: CUDA `12.5` -> `--build-arg CUDATOOLKIT=12-5`
  - Example: CUDA `12.6` -> `--build-arg CUDATOOLKIT=12-6`

## Notes

- Stage/option documentation comments added at the top of each Dockerfile were preserved during the move.
- Graph files (`dot.viz`, `dot.png`) are currently left at top level for reference.
