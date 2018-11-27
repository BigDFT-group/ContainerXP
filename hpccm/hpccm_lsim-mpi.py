doc="""
LSim SDK image

Contents:
  Ubuntu {}""".format(USERARG.get('ubuntu', '16.04'))+"""
  CUDA {}""".format(USERARG.get('cuda', '10.0'))+"""
  FFTW version 3.3.7
  MKL
  GNU compilers (upstream)
  Python 2 and 3 (upstream)
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
else:
  ubuntu_version = USERARG.get('ubuntu', '16.04')
image = 'nvidia/cuda:{}-devel-ubuntu{}'.format(cuda_version,ubuntu_version)

Stage0 += comment(doc, reformat=False)
Stage0.name = 'sdk'
Stage0.baseimage(image)
Stage0 += comment("SDK stage", reformat=False)
# Python
#python = python(python3=True)
#Stage0 += python

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

#Update sources.list to use fastest one when building
command= []
command.append(hpccm.wget().download_step(url='http://http.us.debian.org/debian/pool/main/n/netselect/netselect_0.3.ds1-28+b1_`dpkg --print-architecture`.deb', directory='/var/tmp', outfile='netselect.deb'))
command.append("dpkg -i netselect.deb")
command.append("rm netselect.deb")
command.append('sed -r -i -e "s#http://(archive|security)\.ubuntu\.com/ubuntu/?#$(netselect -v -s1 -t20 `wget -q -O- https://launchpad.net/ubuntu/+archivemirrors | grep -P -B8 \"statusUP|statusSIX\" | grep -o -P \"http://[^\\"]*\"`|grep -P -o \'http://.+$\')#g" /etc/apt/sources.list')
Stage0 += shell(commands=command)

#intel python distribution GPG
Stage0 += shell(commands=['wget https://apt.repos.intel.com/intel-gpg-keys/GPG-PUB-KEY-INTEL-SW-PRODUCTS-2019.PUB',
                          'apt-key add GPG-PUB-KEY-INTEL-SW-PRODUCTS-2019.PUB',
                          'wget https://apt.repos.intel.com/setup/intelproducts.list -O /etc/apt/sources.list.d/intelproducts.list',
                          " sh -c 'echo deb https://apt.repos.intel.com/mkl all main > /etc/apt/sources.list.d/intel-mkl.list' ",
                          " sh -c 'echo deb https://apt.repos.intel.com/mkl all main > /etc/apt/sources.list.d/intel-mpi.list' ",
                          " sh -c 'echo deb https://apt.repos.intel.com/intelpython binary/ > /etc/apt/sources.list.d/intelpython.list' "])

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
        'graphviz', 'tk', 'tcl','libgtk-3-dev']
Stage0 += apt_get(ospackages=ospack)
ospack=['swig', 'chrpath', 'dpatch', 'flex', 'cmake','gtk-doc-tools',
        'libxml2-dev', 'ssh', 'gdb', 'strace','libglu1-mesa-dev',
        'libnetcdf-dev','libgirepository1.0-dev','cpio']
Stage0 += apt_get(ospackages=ospack)
ospack=['intel-mkl-64bit-2019.0-045']
Stage0 += apt_get(ospackages=ospack)
ospack=['intelpython2', 'intelpython3']
Stage0 += apt_get(ospackages=ospack)


#SHELL ["/bin/bash", "-c"]
Stage0 += raw(docker='SHELL ["/bin/bash", "-c"]')
Stage0 += environment(variables={'SHELL': '/bin/bash'})

#Stage0 += shell(commands=['echo ". /opt/intel/intelpython2/bin/activate" >> ~/.bashrc '])
Stage0 += environment(variables={"PATH": "/opt/intel/intelpython2/bin/:${PATH}",
                                 "LD_LIBRARY_PATH": "/opt/intel/intelpython2/lib/:/opt/intel/intelpython2/lib/gobject-introspection/:/opt/intel/intelpython2/lib/libfabric:${LD_LIBRARY_PATH}",
                                 "LIBRARY_PATH": "/opt/intel/intelpython2/lib/:/opt/intel/intelpython2/lib/gobject-introspection/:/opt/intel/intelpython2/lib/libfabric:${LIBRARY_PATH}"})

Stage0 += shell(commands=['conda install -c tacaswell bzr', 'conda install -c conda-forge gobject-introspection glib jupyterlab ipython ipykernel pandas', 'conda clean -a'])

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
ofed_version='3.4'
ofed = mlnx_ofed(version='3.4-1.0.0.0')
Stage1 += ofed

# MPI libraries : default ompi, v 3.0.0
mpi = USERARG.get('mpi', 'ompi')

if mpi == "ompi":
  mpi_version = USERARG.get('mpi_version', '3.0.0')
  mpi_lib = openmpi(infiniband=False, version=mpi_version, prefix="/usr/local/mpi")
elif mpi in ["mvapich2", "mvapich"]:
  Stage1 += apt_get(ospackages=['alien'])
  mpi_version = USERARG.get('mpi_version', '2.3')
  if cuda_version == "8.0":
    gnu_version="5.4.0"
  else:
    gnu_version="6.3.0"
  mpi_lib=shell(commands=['curl -O http://mvapich.cse.ohio-state.edu/download/mvapich/gdr/{}/mofed{}/mvapich2-gdr-mcast.cuda{}.mofed{}.gnu{}-2.3-1.el7.x86_64.rpm && alien -c *.rpm '.format(mpi_version,ofed_version,cuda_version,ofed_version,gnu_version),
'mkdir /usr/local/mpi',
'dpkg --install *.deb',
'rm -f *.rpm *.deb',
'cp -r /opt/mvapich2/gdr/{}/mcast/no-openacc/cuda{}/mofed{}/mpirun/gnu{}/* /usr/local/mpi'.format(mpi_version,cuda_version,ofed_version,gnu_version),
'apt-get remove alien -y',
'apt-get clean -y',
'apt-get autoclean -y',
'apt-get autoremove -y'])
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

#update ldconfig as /usr/local/lib may not be in the path
Stage1 += shell(commands=['echo "/usr/local/mpi/lib" > /etc/ld.so.conf.d/mpi.conf',
                          'echo "/usr/local/mpi/lib64" >> /etc/ld.so.conf.d/mpi.conf',
                          'echo "/bigdft/lib" > /etc/ld.so.conf.d/bigdft.conf',
                          'ldconfig'])



