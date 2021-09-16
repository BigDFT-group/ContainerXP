doc="""
LSim SDK image

Contents:
  Ubuntu {}""".format(USERARG.get('ubuntu', '16.04'))+"""
  CUDA {}""".format(USERARG.get('cuda', '10.0'))+"""
  Target architecture {}""".format(USERARG.get('target_arch', 'x86_64'))+"""
  for architecture
  MKL on x86_64, ARMPL on aarch64
  GNU compilers (upstream) and ARM compilers on aarch64
  Python 3 (intel on x86_64)
  jupyter notebook and jupyter lab
  v_sim-dev in the optional target

  This recipe was generated with command line :
$ hpccm.py --recipe hpccm_lsim-mpi.py --userarg cuda={}""".format(USERARG.get('cuda', '10.0'))+""" \
ubuntu={}""".format(USERARG.get('ubuntu', '16.04'))+""" \
mpi={}""".format(USERARG.get('mpi', 'ompi'))+""" \
target_arch={}""".format(USERARG.get('target_arch', 'x86_64'))
#######
## SDK stage
#######
from distutils.version import LooseVersion, StrictVersion

# Set the image tag based on the specified version (default to 10.0)
cuda_version = USERARG.get('cuda', '10.0')
if cuda_version == "8.0":
  ubuntu_version = "16.04"
  distro = 'ubuntu16'
else:
  ubuntu_version = USERARG.get('ubuntu', '18.04')

if ubuntu_version == "18.04" or ubuntu_version == "18.04-rc":
  distro = 'ubuntu18'
elif ubuntu_version == "20.04":
  distro = 'ubuntu20'
else:
  distro = 'ubuntu'

target_arch = USERARG.get('target_arch', 'x86_64')
repo="nvidia/cuda"
image = '{}:{}-devel-ubuntu{}'.format(repo,cuda_version,ubuntu_version)

Stage0 += comment(doc, reformat=False)
Stage0.name = 'sdk'
Stage0.baseimage(image,_distro=distro)
Stage0 += comment("SDK stage", reformat=False)

import hpccm.config
hpccm.config.set_cpu_architecture(target_arch)
hpccm.config.set_cpu_target(target_arch)
hpccm.config.g_linux_version=ubuntu_version

# GNU compilers
gnu = gnu()
Stage0 += gnu

# Setup the toolchain.  Use the GNU compiler toolchain as the basis.
tc = gnu.toolchain
tc.CUDA_HOME = '/usr/local/cuda'

if "arm" in target_arch:
  Stage0 += arm_allinea_studio(eula=True, microarchitectures=['generic', 'thunderx2t99', 'generic-sve'])
  #TODO: find a way to not depend on versions here...
  Stage0 += environment(variables={"LD_LIBRARY_PATH": "/opt/arm/armpl-20.3.0_Generic-AArch64_Ubuntu-16.04_gcc_aarch64-linux/lib:${LD_LIBRARY_PATH}",
                                   "LIBRARY_PATH": "/opt/arm/armpl-20.3.0_Generic-AArch64_Ubuntu-16.04_gcc_aarch64-linux/lib:${LIBRARY_PATH}", 
                                   "ARMPL": "/opt/arm/armpl-20.3.0_Generic-AArch64_Ubuntu-16.04_gcc_aarch64-linux"})

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
        'libnetcdf-dev','libgirepository1.0-dev','cpio', 'libgtk-3-dev']
Stage0 += apt_get(ospackages=ospack)
ospack=['ninja-build locales libmount-dev']
Stage0 += apt_get(ospackages=ospack)

#SHELL ["/bin/bash", "-c"]
Stage0 += raw(docker='SHELL ["/bin/bash", "-c"]')

if target_arch == "x86_64":
  Stage0 += environment(variables={'SHELL': '/bin/bash',
                                  "PATH":  '/usr/local/anaconda/bin:$PATH' })


  #conda install
  Stage0 += conda(version='4.9.2', python_subversion='py37', channels=['conda-forge', 'nvidia', 'intel'], eula=True,
               packages=[ 'jupyterlab', 'ipython', 'ipykernel', 
                          'intelpython3_core=2020.4',
                          'six', 'matplotlib', 'mkl-devel',
                          'nbval', 'cython', 'sphinx', 'sphinx_bootstrap_theme', 
                          'watchdog', 'sphinx_rtd_theme', 'flake8', 'ncurses'])
  #overcome multiple issues with anaconda ...
  Stage0 += shell(commands=['ln -s /usr/local/anaconda/bin/python3-config /usr/local/anaconda/bin/python-config',
                          'pip install pygobject',
                          'groupadd conda',
                          'chgrp -R conda /usr/local/anaconda/',
                          'chmod -R 770 /usr/local/anaconda/'])

  #Intel python forgets to provideo ncurses https://community.intel.com/t5/Intel-Distribution-for-Python/curses-missing-on-python-3-7/m-p/1201384#M1509
  #Temporarily steal the files from conda-forge package, and use them instead, as it's used in bigdft-tool.
  Stage0 += shell(commands=['mkdir curses',
                          'cd curses',
                          'wget https://anaconda.org/conda-forge/python/3.7.8/download/linux-64/python-3.7.8-h6f2ec95_1_cpython.tar.bz2',
                          'tar xjf python-3.7.8-h6f2ec95_1_cpython.tar.bz2',
                          'cp ./lib/python3.7/lib-dynload/_curses* /usr/local/anaconda/lib/python3.7/lib-dynload/',
                          'cd ..',
                          'rm -rf curses'])

  #update LIBRARY_PATH as well to allow building against these libs :
  Stage0 += environment(variables={"LIBRARY_PATH": "/usr/lib/x86_64-linux-gnu/:/usr/local/anaconda/lib/:${LIBRARY_PATH}"})

else:
  #on arm platforms miniconda is not available. Use system python and libraries
  ospack=[
  'python3', 'cython3', 'python3-flake8', 'python3-ipykernel',
  'python3-ipython', 'python3-pip', 'jupyter-notebook', 'python3-matplotlib',
  'python3-six', 'python3-sphinx', 'python3-sphinx-bootstrap-theme',
  'python3-scipy', 'python3-numpy',
  'python3-sphinx-rtd-theme', 'watchdog']
  Stage0 += apt_get(ospackages=ospack)

  #make python3 and pip3 default
  Stage0 += shell(commands=['ln -s /usr/bin/python3 /usr/local/bin/python',
                          'ln -s /usr/bin/pip3 /usr/local/bin/pip'])

Stage0 += raw(docker='EXPOSE 8888')

#install OpenCL icd file
Stage0 += shell(commands=['mkdir -p /etc/OpenCL/vendors',
                          'echo "libnvidia-opencl.so.1" > /etc/OpenCL/vendors/nvidia.icd'])

Stage0 += environment(variables={'NVIDIA_VISIBLE_DEVICES': 'all'})
Stage0 += environment(variables={'NVIDIA_DRIVER_CAPABILITIES': 'compute,utility'})

Stage0 += raw(docker='CMD jupyter lab --ip=0.0.0.0 --allow-root --NotebookApp.token=bigdft --no-browser', singularity='%runscript\n jupyter lab --ip=0.0.0.0 --allow-root --NotebookApp.token=bigdft --no-browser')

Stage0 += shell(commands=['useradd -ms /bin/bash lsim'])
if target_arch == "x86_64":
  Stage0 += shell(commands=['adduser lsim conda'])

# Set the locale
Stage0 += shell(commands=['sed -i -e "s/# en_US.UTF-8 UTF-8/en_US.UTF-8 UTF-8/" /etc/locale.gen','locale-gen'])



Stage0 += raw(docker='USER lsim')
preload=''
if ubuntu_version >= StrictVersion('20.04') and target_arch == "x86_64":
  preload = "/usr/lib/x86_64-linux-gnu/libtinfo.so.6"

Stage0 += environment(variables={"LANG": "en_US.UTF-8",
                                 "LANGUAGE": "en_US.UTF-8",
                                 "LC_ALL": "en_US.UTF-8",
                                 "LD_PRELOAD": preload
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
  mpi_lib = openmpi(infiniband=True, pmix='internal', version=mpi_version, prefix="/usr/local/mpi")
  Stage1 += environment(variables={"OMPI_MCA_btl_vader_single_copy_mechanism": "none",
                                   "OMPI_MCA_rmaps_base_mapping_policy":"slot",
                                   "OMPI_MCA_hwloc_base_binding_policy":"none",
                                   "OMPI_MCA_btl_openib_cuda_async_recv":"false",
                                   "OMPI_MCA_mpi_leave_pinned":"true",
                                   "OMPI_MCA_opal_warn_on_missing_libcuda":"false",
                                   "OMPI_MCA_rmaps_base_oversubscribe":"true",
                                   "PATH": "/usr/local/mpi/bin/:${PATH}",
                                   "LD_LIBRARY_PATH": "/usr/local/mpi/lib:/usr/local/mpi/lib64:${LD_LIBRARY_PATH}"})
elif mpi in ["mvapich2", "mvapich"]:
  # Mellanox OFED
  ofed_version='5.0'
  Stage1 += mlnx_ofed(version='5.0-2.1.8.0', oslabel='ubuntu18.04')
  gdrcopy=gdrcopy()
  mpi_version = USERARG.get('mpi_version', '2.3')
  if cuda_version == "8.0":
    gnu_version="5.4.0"
  elif cuda_version == "11.0" and mpi_version=="2.3.4":
    gnu_version="9.3.0"
  else:
    gnu_version="4.8.5"
  if mpi_version == "2.3.4" or mpi_version=="2.3.5":
    release = 1
  else:
    release = 2
  mpi_lib= mvapich2_gdr(version=mpi_version, prefix="/usr/local/mpi",mlnx_ofed_version=ofed_version, cuda_version=cuda_version, release=release, gnu_version=gnu_version)
  Stage1 += apt_get(ospackages=['libxnvctrl-dev libibmad5'])

  Stage1 += environment(variables={"PATH": "/usr/local/mpi/bin/:${PATH}",
                                 "LD_LIBRARY_PATH": "/usr/local/lib/:/usr/local/mpi/lib:/usr/local/mpi/lib64:${LD_LIBRARY_PATH}",
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

Stage1 += shell(commands=['cp /usr/local/cuda/lib64/stubs/libcuda.so /usr/local/lib/libcuda.so.1'])
Stage1 += shell(commands=['cp /usr/local/cuda/lib64/stubs/libnvidia-ml.so /usr/local/lib/libnvidia-ml.so.1'])

Stage1 += raw(docker='USER lsim')

