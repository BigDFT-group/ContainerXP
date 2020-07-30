doc="""
LSim SDK image

Contents:
  Ubuntu {}""".format(USERARG.get('ubuntu', '16.04'))+"""
  CUDA {}""".format(USERARG.get('cuda', '10.0'))+"""
  FFTW version 3.3.7
  MKL
  GNU compilers (upstream)
  Python 3 (intel)
  jupyter notebook and jupyter lab
  v_sim-dev in the optional target

  This recipe was generated with command line :
$ hpccm.py --recipe hpccm_lsim-mpi.py --userarg cuda={}""".format(USERARG.get('cuda', '10.0'))+""" ubuntu={}""".format(USERARG.get('ubuntu', '16.04'))+""" mpi={}""".format(USERARG.get('mpi', 'ompi'))
#######
## SDK stage
#######

# Set the image tag based on the specified version (default to 10.0)
cuda_version = USERARG.get('cuda', '10.0')
if cuda_version == "8.0":
  ubuntu_version = "16.04"
  distro = 'ubuntu16'
else:
  ubuntu_version = USERARG.get('ubuntu', '18.04')

if ubuntu_version == "18.04" or ubuntu_version == "18.04-rc":
  distro = 'ubuntu18'
else:
  distro = 'ubuntu'

image = 'nvidia/cuda:{}-devel-ubuntu{}'.format(cuda_version,ubuntu_version)

Stage0 += comment(doc, reformat=False)
Stage0.name = 'sdk'
Stage0.baseimage(image,_distro=distro)
Stage0 += comment("SDK stage", reformat=False)

# GNU compilers
gnu = gnu()
Stage0 += gnu

# Setup the toolchain.  Use the GNU compiler toolchain as the basis.
tc = gnu.toolchain
tc.CUDA_HOME = '/usr/local/cuda'

# FFTW
fftw = fftw(version='3.3.8',baseurl="http://fftw.org/", toolchain=tc)
Stage0 += fftw

#BigDFT packages
Stage0 += label(metadata={'maintainer': 'bigdft-developers@lists.launchpad.net'})
Stage0 += environment(variables={'DEBIAN_FRONTEND': 'noninteractive'})

ospack=['autoconf','autotools-dev', 'automake','git','build-essential', 'libblas-dev', 'liblapack-dev',
        'curl', 'bison',
        'libz-dev', 'pkg-config']
Stage0 += apt_get(ospackages=ospack)
ospack=['libpcre3-dev','libtool',
        'libltdl-dev', 'gnome-common',
        'ocl-icd-libopencl1', 'vim', 'net-tools','intltool']
Stage0 += apt_get(ospackages=ospack)
ospack=['ethtool', 'perl', 'lsb-release', 'iproute2',
        'pciutils', 'libopenbabel-dev', 'libnl-route-3-200', 'kmod',
        'libnuma1', 'lsof', 'linux-headers-generic', 
        'graphviz', 'tk', 'tcl']
Stage0 += apt_get(ospackages=ospack)
ospack=['swig', 'chrpath', 'dpatch', 'flex', 'cmake','gtk-doc-tools',
        'libxml2-dev', 'ssh', 'gdb', 'strace','libglu1-mesa-dev',
        'libnetcdf-dev','libgirepository1.0-dev','cpio']
Stage0 += apt_get(ospackages=ospack)
ospack=['ninja-build locales libmount-dev']
Stage0 += apt_get(ospackages=ospack)

#SHELL ["/bin/bash", "-c"]
Stage0 += raw(docker='SHELL ["/bin/bash", "-c"]')
Stage0 += environment(variables={'SHELL': '/bin/bash',
                                  "PATH":  '/usr/local/anaconda/bin:$PATH' })


#conda install
Stage0 += conda(version='py37_4.8.3', channels=['conda-forge', 'nvidia', 'intel'], eula=True,
               packages=[ 'jupyterlab', 'ipython', 'ipykernel', 
                          'intelpython3_core','numpy', 'scipy', 'setuptools', 
                          'six', 'yaml', 'matplotlib', 'mkl-devel',
                          'nbval', 'cython', 'sphinx', 'sphinx_bootstrap_theme', 
                          'watchdog', 'sphinx_rtd_theme', 'flake8'])
#overcome multiple issues with anaconda ...
Stage0 += shell(commands=['ln -s /usr/local/anaconda/bin/python3-config /usr/local/anaconda/bin/python-config',
                          'mv /usr/local/anaconda/include/iconv.h /usr/local/anaconda/include/iconv_save.h',
                          'pip install pygobject',
                          'groupadd conda',
                          'chgrp -R conda /usr/local/anaconda/',
                          'chmod -R 770 /usr/local/anaconda/'])

Stage0 += raw(docker='EXPOSE 8888')

#install OpenCL icd file
Stage0 += shell(commands=['mkdir -p /etc/OpenCL/vendors',
                          'echo "libnvidia-opencl.so.1" > /etc/OpenCL/vendors/nvidia.icd'])

Stage0 += environment(variables={'NVIDIA_VISIBLE_DEVICES': 'all'})
Stage0 += environment(variables={'NVIDIA_DRIVER_CAPABILITIES': 'compute,utility'})

Stage0 += raw(docker='CMD jupyter lab --ip=0.0.0.0 --allow-root --NotebookApp.token=bigdft --no-browser', singularity='%runscript\n jupyter lab --ip=0.0.0.0 --allow-root --NotebookApp.token=bigdft --no-browser')

Stage0 += shell(commands=['useradd -ms /bin/bash lsim',
                          'adduser lsim conda'])

# Set the locale
Stage0 += shell(commands=['sed -i -e "s/# en_US.UTF-8 UTF-8/en_US.UTF-8 UTF-8/" /etc/locale.gen','locale-gen'])



Stage0 += raw(docker='USER lsim')

Stage0 += environment(variables={"LANG": "en_US.UTF-8",
                                 "LANGUAGE": "en_US.UTF-8",
                                 "LC_ALL": "en_US.UTF-8",
                                  })

Stage0 += environment(variables={"XDG_CACHE_HOME": "/home/lsim/.cache/"})
Stage0 += workdir(directory='/home/lsim')
Stage0 += shell(commands=['MPLBACKEND=Agg python -c "import matplotlib.pyplot"'])

# v_sim build stage
Stage1.name = 'mpi'
Stage1.baseimage(image='sdk',_distro=distro)
Stage1 += comment("mpi", reformat=False)

Stage1 += raw(docker='USER root')

# MPI libraries : default ompi, v 4.0.0
mpi = USERARG.get('mpi', 'ompi')

if mpi == "ompi":
  #normal OFED 
  Stage1 += ofed()
  mpi_version = USERARG.get('mpi_version', '4.0.0')
  mpi_lib = openmpi(infiniband=True, version=mpi_version, prefix="/usr/local/mpi")
  Stage1 += environment(variables={"OMPI_MCA_btl_vader_single_copy_mechanism": "none",
                                   "OMPI_MCA_rmaps_base_mapping_policy":"core",
                                   "OMPI_MCA_hwloc_base_binding_policy":"none",
                                   "OMPI_MCA_btl_openib_cuda_async_recv":"false",
                                   "OMPI_MCA_mpi_leave_pinned":"true",
                                   "OMPI_MCA_opal_warn_on_missing_libcuda":"false",
                                   "PATH": "/usr/local/mpi/bin/:${PATH}",
                                   "LD_LIBRARY_PATH": "/usr/local/mpi/lib:/usr/local/mpi/lib64:${LD_LIBRARY_PATH}"})
elif mpi in ["mvapich2", "mvapich"]:
  # Mellanox OFED
  ofed_version='4.7'
  Stage1 += mlnx_ofed()
  gdrcopy=gdrcopy()
  mpi_version = USERARG.get('mpi_version', '2.3')
  if cuda_version == "8.0":
    gnu_version="5.4.0"
  else:
    gnu_version="4.8.5"
  if mpi_version == "2.3.4":
    release = 1
  else:
    release = 2
  mpi_lib= mvapich2_gdr(version=mpi_version, prefix="/usr/local/mpi",mlnx_ofed_version=ofed_version, cuda_version=cuda_version, release=release)
  Stage1 += apt_get(ospackages=['libxnvctrl-dev libibmad5'])

  Stage1 += environment(variables={"PATH": "/usr/local/mpi/bin/:${PATH}",
                                 "LD_LIBRARY_PATH": "/usr/local/mpi/lib:/usr/local/mpi/lib64:${LD_LIBRARY_PATH}",
                                 "MV2_USE_GPUDIRECT_GDRCOPY": "0",
                                 "MV2_SMP_USE_CMA": "0",
                                 "MV2_ENABLE_AFFINITY": "0",
                                 "MV2_CPU_BINDING_POLICY": "scatter",
                                 "MV2_CPU_BINDING_LEVEL": "socket"})
elif mpi == 'impi':
  mpi_lib = intel_mpi(eula=True) #apt_get(ospackages=[intel-mpi])

Stage1 += mpi_lib

#Workaround missing install on mvapich_gdr in hpccm
if mpi in ["mvapich2", "mvapich"]:
  Stage1 += shell(commands=['mkdir /usr/local/mpi/',
                            'cp -r /opt/mvapich2/gdr/{}/mcast/no-openacc/cuda{}/mofed{}/mpirun/gnu{}/* /usr/local/mpi'.format(mpi_version,cuda_version,ofed_version,gnu_version)])

#update ldconfig as /usr/local/lib may not be in the path
Stage1 += shell(commands=['echo "/usr/local/mpi/lib" > /etc/ld.so.conf.d/mpi.conf',
                          'echo "/usr/local/mpi/lib64" >> /etc/ld.so.conf.d/mpi.conf',
                          'echo "/usr/local/anaconda/lib" >> /etc/ld.so.conf.d/anaconda.conf',
                          'echo "/bigdft/lib" > /etc/ld.so.conf.d/bigdft.conf',
                          'ldconfig'])

Stage1 += raw(docker='USER lsim')

