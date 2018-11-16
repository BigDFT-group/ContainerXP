#!/bin/bash
set -e

: ${cuda_version:="10.0"}
: ${ubuntu_version="18.04"}
: ${mpi="ompi"}
: ${mpi_version="2.3"}
if [ $mpi = "ompi" ]; then
: ${mpi_version="4.0.0"}
fi
: ${tag="bigdft"}

suffix=ubuntu${ubuntu_version}_cuda${cuda_version}_${mpi}${mpi_version}

hpccm.py --recipe hpccm_lsim-mpi.py --userarg cuda=${cuda_version} ubuntu=${ubuntu_version} mpi=${mpi} mpi_version=${mpi_version} tag=${tag} > Dockerfile_sdk_${suffix}
docker build --tag ${tag}/sdk --target sdk - < ./Dockerfile_sdk_${suffix}
docker build --tag ${tag}/sdk_mpi - < ./Dockerfile_sdk_${suffix}

hpccm.py --recipe hpccm_lsim-vsim.py --userarg cuda=${cuda_version} ubuntu=${ubuntu_version} mpi=${mpi} mpi_version=${mpi_version} tag=${tag} > ./Dockerfile_vsim_${suffix}
docker build --tag ${tag}/v_sim - < ./Dockerfile_vsim_${suffix}

hpccm.py --recipe hpccm_lsim-bigdft.py --userarg cuda=${cuda_version} ubuntu=${ubuntu_version} mpi=${mpi} mpi_version=${mpi_version} tag=${tag} > ./Dockerfile_bigdft_${suffix}
docker build --tag ${tag}/runtime - < ./Dockerfile_bigdft_${suffix}


