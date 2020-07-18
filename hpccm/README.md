
# Hpccm nvidia dockerfile recipe generator

Instructions:

 * Install NVidia's hpccm fir `pip install hpccm`
 * Generate and build all images at once :
   `cuda_version="10.2" ubuntu_version="18.04" mpi="mvapich2" mpi_version="2.3.4" tag="bigdft" ./build.sh`
 * Or to generate only SDK
 * Generate the `Dockerfile` with the command:
    `hpccm.py --recipe hpccm-lsim_mpi.py --userarg cuda=10.2 ubuntu=18.04 mpi=mvapich2 mpi_version=2.3.4 > Dockerfile`
 * Prepare the container image with
   `<sudo> docker build --target=<sdk,sdk_mpi,nothing> - < Dockerfile`
