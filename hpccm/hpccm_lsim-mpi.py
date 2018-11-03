doc="""
LSim SDK image

Contents:
  Ubuntu 16.04
  CUDA
  FFTW version 3.3.7
  MKL
  GNU compilers (upstream)
  Python 2 and 3 (upstream)
  jupyter notebook and jupyter lab
  v_sim-dev in the optional target

  This recipe was generated with command line :
$ hpccm.py --recipe hpccm_bigdft.py --userarg cuda={}""".format(USERARG.get('cuda', '10.0'))+""" ubuntu={}""".format(USERARG.get('ubuntu', '16.04'))+""" mpi = {}""".format(USERARG.get('mpi', 'ompi'))

#######
## SDK stage
#######

# Set the image tag based on the specified version (default to 10.0)
cuda_version = USERARG.get('cuda', '10.0')
ubuntu_version = USERARG.get('ubuntu', '16.04')
image = 'nvidia/cuda:{}-devel-ubuntu{}'.format(cuda_version,ubuntu_version)

Stage0 += comment(doc, reformat=False)
Stage0.name = 'sdk'
Stage0.baseimage(image)
Stage0 += comment("SDK stage", reformat=False)
# Python
python = python(python3=True)
Stage0 += python

# GNU compilers
gnu = gnu()
Stage0 += gnu

# Setup the toolchain.  Use the GNU compiler toolchain as the basis.
tc = gnu.toolchain
tc.CUDA_HOME = '/usr/local/cuda'

# FFTW
fftw = fftw(version='3.3.7', toolchain=tc)
Stage0 += fftw

#BigDFT packages
Stage0 += label(metadata={'maintainer': 'bigdft-developers@lists.launchpad.net'})

#intel python distribution GPG
Stage0 += shell(commands=['wget https://apt.repos.intel.com/intel-gpg-keys/GPG-PUB-KEY-INTEL-SW-PRODUCTS-2019.PUB',
                          'apt-key add GPG-PUB-KEY-INTEL-SW-PRODUCTS-2019.PUB',
                          'wget https://apt.repos.intel.com/setup/intelproducts.list -O /etc/apt/sources.list.d/intelproducts.list',
                          " sh -c 'echo deb https://apt.repos.intel.com/mkl all main > /etc/apt/sources.list.d/intel-mkl.list' ",
                          " sh -c 'echo deb https://apt.repos.intel.com/mkl all main > /etc/apt/sources.list.d/intel-mpi.list' "])

ospack=['autoconf','autotools-dev', 'automake', 'bzr','git','build-essential', 'libblas-dev', 'liblapack-dev',
        'curl', 'python-pip', 'python-dev', 'bison',
        'libz-dev', 'pkg-config', 'python-setuptools',
        'libpcre3-dev','libtool', 'libglib2.0-dev',
        'libltdl-dev', 'gnome-common',
        'python3-pip','python3-setuptools',
        'ocl-icd-libopencl1', 'vim', 'net-tools','intltool',
        'ethtool', 'perl', 'lsb-release', 'iproute2',
        'pciutils', 'libopenbabel-dev', 'libnl-route-3-200', 'kmod',
        'libnuma1', 'lsof', 'linux-headers-generic',
        'python-libxml2', 'graphviz', 'tk', 'tcl','libgtk-3-dev',
        'swig', 'chrpath', 'dpatch', 'flex', 'cmake','gtk-doc-tools',
        'libxml2-dev', 'ssh', 'gdb', 'strace','libglu1-mesa-dev',
        'libnetcdf-dev','libgirepository1.0-dev','cpio','intel-mkl-64bit-2019.0-045']

if ubuntu_version=='18.04':
    ospack += ['python-gobject-2-dev']
else:
    ospack += ['python-gobject-dev']

Stage0 += apt_get(ospackages=ospack)

#SHELL ["/bin/bash", "-c"]
Stage0 += raw(docker='SHELL ["/bin/bash", "-c"]')
Stage0 += environment(variables={'SHELL': '/bin/bash'})

#upgrade pip to avoid annoying message
Stage0 += shell(commands=['pip3 install --upgrade pip','pip2 install --upgrade pip'])
#wheel
Stage0 += shell(commands=['pip3 install wheel','pip2 install wheel'])

#install numpy and linalg
Stage0 += shell(commands=['pip3 install intel-scipy','pip2 install intel-scipy'])
#install matplotlib and ase and nglview
Stage0 += shell(commands=['pip3 install matplotlib nglview','pip2 install matplotlib==2.1.1 ase'])

Stage0 += shell(commands=['pip3 install jupyter jupyterlab'])
Stage0 += shell(commands=['pip2 install ipython==5.5 ipykernel==4.10'])
#Stage0 += shell(commands=['python2 -m ipykernel install'])

Stage0 += raw(docker='EXPOSE 8888')

#install OpenCL icd file
Stage0 += shell(commands=['mkdir -p /etc/OpenCL/vendors',
                          'echo "libnvidia-opencl.so.1" > /etc/OpenCL/vendors/nvidia.icd'])

Stage0 += environment(variables={'NVIDIA_VISIBLE_DEVICES': 'all'})
Stage0 += environment(variables={'NVIDIA_DRIVER_CAPABILITIES': 'compute,utility'})

Stage0 += raw(docker='CMD jupyter lab --ip=0.0.0.0 --allow-root --NotebookApp.token=bigdft --no-browser', singularity='%runscript\n jupyter lab --ip=0.0.0.0 --allow-root --NotebookApp.token=bigdft --no-browser')

Stage0 += shell(commands=['useradd -ms /bin/bash lsim'])

Stage0 += raw(docker='USER lsim')

Stage0 += environment(variables={"XDG_CACHE_HOME": "/home/lsim/.cache/"})
Stage0 += workdir(directory='/home/lsim')
Stage0 += shell(commands=['MPLBACKEND=Agg python -c "import matplotlib.pyplot"'])

# v_sim build stage
Stage1.name = 'mpi'
Stage1.baseimage(image='sdk')
Stage1 += comment("mpi", reformat=False)

Stage1 += raw(docker='USER root')

# Mellanox OFED
ofed = mlnx_ofed(version='3.4-1.0.0.0')
Stage1 += ofed

# MPI libraries : default ompi, v 3.0.0
mpi = USERARG.get('mpi', 'ompi')

if mpi == "ompi":
  mpi_version = USERARG.get('mpi_version', '3.0.0')
  mpi_lib = openmpi(infiniband=False, version=mpi_version, prefix="/usr/local/mpi")
elif mpi in ["mvapich2", "mvapich"]:
  mpi_version = USERARG.get('mpi_version', '2.3b')
  mpi_lib = mvapich2(version=mpi_version, toolchain=tc, prefix="/usr/local/mpi")
elif mpi == 'impi':
  mpi_lib = intel_mpi(eula=True) #apt_get(ospackages=[intel-mpi])

Stage1 += mpi_lib

#update ldconfig as /usr/local/lib may not be in the path
Stage1 += shell(commands=['echo "/usr/local/mpi/lib" > /etc/ld.so.conf.d/mpi.conf',
                          'echo "/bigdft/lib" > /etc/ld.so.conf.d/bigdft.conf',
                          'ldconfig'])

Stage1 += environment(variables={"MV2_USE_GPUDIRECT_GDRCOPY": "0",
                                 "MV2_SMP_USE_CMA": "0",
                                 "MV2_ENABLE_AFFINITY": "0",
                                 "MV2_CPU_BINDING_POLICY": "scatter",
                                 "MV2_CPU_BINDING_LEVEL": "socket"})

Stage1 += raw(docker='USER lsim')

#Stage1 += workdir(directory='/opt/')
#Stage1 += shell(commands=['rm -rf /opt/v_sim-dev','mkdir -p /opt/v_sim-dev'])
#Stage1 += apt_get(ospackages=['libyaml-dev'])
#Stage1 += workdir(directory='/opt/')
#Stage1 += shell(commands=['git clone https://gitlab.com/l_sim/v_sim.git v_sim-dev'])
#Stage1 += workdir(directory='/opt/v_sim-dev')
#Stage1 += shell(commands=['sh autogen.sh'])
#
#cm = hpccm.ConfigureMake(opts=['--with-abinit', '--with-archives', '--with-openbabel', '--with-cube', '--without-strict-cflags'])
#command= []
#command.append( cm.configure_step())
#command.append( cm.build_step())
#command.append( cm.install_step())
#Stage1 += shell(commands=command)
#Stage1 += environment(variables={"PATH": "/opt/v_sim-dev/bin/:${PATH}"})
#Stage1 += raw(docker='USER lsim')
#Stage1 += workdir(directory='/home/lsim')
