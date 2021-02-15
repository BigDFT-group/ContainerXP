#
# This Dockerfile installs a basic BigDFT build
#

#build stage : heavy image, will be discarded after build
FROM debian:buster-slim
LABEL maintainer bigdft-developers@lists.launchpad.net

WORKDIR /opt/bigdft

#install needed dependencies
RUN apt-get update && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
    autoconf autotools-dev automake git build-essential \
    libblas-dev liblapack-dev curl wget gfortran libyaml-dev \
    python3-numpy python3-yaml libopenmpi-dev python3-setuptools \
    python3-pytest python3-pip cython pkg-config binutils

SHELL ["/bin/bash", "-c"]
ENV SHELL /bin/bash

#jhbuild is allergic to root
RUN useradd -ms /bin/bash bigdft
RUN mkdir /usr/local/bigdft && \
    chmod -R 777 /usr/local/bigdft
USER bigdft
WORKDIR /home/bigdft
ENV PYTHON python3
RUN git clone --depth 1 --branch 1.9.1 https://gitlab.com/l_sim/bigdft-suite.git
RUN cd bigdft-suite && \
    mkdir build && \
    cd build && \
    echo "prefix='/usr/local/bigdft' " > ./buildrc && cat ../rcfiles/ubuntu_MPI.rc >> buildrc && sed -i 's/-m64//' ./buildrc
WORKDIR /home/bigdft/bigdft-suite/build
RUN python3 ../Installer.py autogen -y && \
	python3 ../Installer.py build -y -v

RUN strip /usr/local/bigdft/bin/bigdft

FROM debian:buster-slim as runtime
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    libblas3 liblapack3 libyaml-0-2 \
    openmpi-bin libgfortran5 libgomp1
ENV OMPI_MCA_btl_base_warn_component_unused=0 \
    OMPI_MCA_btl_vader_single_copy_mechanism=none \
    OMPI_MCA_rmaps_base_mapping_policy=slot \
    OMPI_MCA_hwloc_base_binding_policy=none \
    OMPI_MCA_mpi_leave_pinned=true \
    OMPI_MCA_rmaps_base_oversubscribe=true
COPY --from=0 /usr/local/bigdft/bin/bigdft /usr/local/bin/bigdft
CMD /usr/local/bin/bigdft
RUN useradd -ms /bin/bash bigdft
USER bigdft
