doc="""
BigDFT SDK image

Contents:
  Ubuntu 16.04
  CUDA
  FFTW version 3.3.7
  MKL 
  GNU compilers (upstream)
  Mellanox OFED version 3.4-1.0.0.0
  Python 2 and 3 (upstream)
  MPI (openmpi or mvapich)
  BigDFT SDK
  jupyter notebook
  This recipe was generated with command line :
$ hpccm.py --recipe hpccm_bigdft.py --userarg cuda={}""".format(USERARG.get('cuda', '9.1'))+""" mpi="""+USERARG.get('mpi', 'ompi')+""" mpi_version="""+USERARG.get('mpi_version', '3.0.0')

#######
## SDK stage
#######

# Set the image tag based on the specified version (default to 9.1)
cuda_version = USERARG.get('cuda', '9.1')
image = 'nvidia/cuda:{}-devel'.format(cuda_version)

Stage0 += comment(doc, reformat=False)
Stage0.name = 'sdk'
Stage0.baseimage(image)
Stage0 += comment("SDK stage", reformat=False)
# Python
python = python(python3=False)
Stage0 += python

# GNU compilers
gnu = gnu()
Stage0 += gnu

# Setup the toolchain.  Use the GNU compiler toolchain as the basis.
tc = gnu.toolchain
tc.CUDA_HOME = '/usr/local/cuda'

# Mellanox OFED
ofed = mlnx_ofed(version='3.4-1.0.0.0')
Stage0 += ofed

# MPI libraries : default ompi, v 3.0.0
mpi = USERARG.get('mpi', 'ompi')

if mpi == "ompi":
  mpi_version = USERARG.get('mpi_version', '3.0.0')
  mpi_lib = openmpi(infiniband=False, version=mpi_version)
elif mpi in ["mvapich2", "mvapich"]:
  mpi_version = USERARG.get('mpi_version', '2.3a')
  mpi_lib = mvapich2_gdr(version=mpi_version, toolchain=tc, cuda_version=cuda_version)
  
Stage0 += mpi_lib

# FFTW
fftw = fftw(version='3.3.7', toolchain=tc)
Stage0 += fftw


#BigDFT packages
Stage0 += label(metadata={'maintainer': 'bigdft-developers@lists.launchpad.net'})

Stage0 += apt_get(ospackages=['autoconf','autotools-dev', 'automake', 'bzr',
                              'build-essential', 'libblas-dev', 'liblapack-dev',
                              'curl', 'python-pip', 'python-dev', 'bison', 
                              'libz-dev', 'pkg-config', 'python-setuptools', 
                              'libpcre3-dev','libtool', 'libglib2.0-dev', 'git',
                              'libltdl-dev', 'gnome-common', 'ipython', 
                              'ipython-notebook', 'python-matplotlib', 
                              'ocl-icd-libopencl1', 'vim', 'net-tools', 
                              'ethtool', 'perl', 'lsb-release', 'iproute2', 
                              'pciutils', 'libnl-route-3-200', 'kmod', 
                              'libnuma1', 'lsof', 'linux-headers-generic', 
                              'python-libxml2', 'graphviz', 'tk', 'tcl', 
                              'swig', 'chrpath', 'dpatch', 'flex', 'cmake', 
                              'libxml2-dev', 'ssh', 'gdb', 'strace'])

#SHELL ["/bin/bash", "-c"]
Stage0 += raw(docker='SHELL ["/bin/bash", "-c"]')
Stage0 += environment(variables={'SHELL': '/bin/bash'})
#install jupyter
#upgrade pip to avoid annoying message
Stage0 += shell(commands=['pip install scipy jupyter'])

Stage0 += raw(docker='EXPOSE 8888')


#install OpenCL icd file
Stage0 += shell(commands=['mkdir -p /etc/OpenCL/vendors',
                          'echo "libnvidia-opencl.so.1" > /etc/OpenCL/vendors/nvidia.icd'])

Stage0 += environment(variables={'NVIDIA_VISIBLE_DEVICES': 'all'})
Stage0 += environment(variables={'NVIDIA_DRIVER_CAPABILITIES': 'compute,utility'})


#packages for v_sim
Stage0 += comment("v_sim build", reformat=False)
Stage0 += apt_get(ospackages=['libglu1-mesa-dev', 'libglib2.0-dev', 
                              'libnetcdf-dev', 'libopenbabel-dev', 'intltool', 
                              'libtool', 'gtk-doc-tools', 'libgtk-3-dev', 
                              'python-gobject-dev', 'libyaml-dev', 
                              'libgirepository1.0-dev'])

Stage0 += workdir(directory='/opt/v_sim-dev')

#hack around to get the string
command= []
command.append(hpccm.wget().download_step(url='http://inac.cea.fr/L_Sim/V_Sim/download/v_sim-dev.tar.bz2', directory='/opt/v_sim-dev'))

command.append(hpccm.tar().untar_step(tarball='v_sim-dev.tar.bz2'))

cm = hpccm.ConfigureMake(opts=['--with-abinit', '--with-archives', '--with-openbabel', '--with-cube', '--without-strict-cflags'])
command.append( cm.configure_step(directory='v_sim*/'))
command.append( cm.build_step())
command.append( cm.install_step())
Stage0 += shell(commands=command)


Stage0 += comment("MKL install", reformat=False)

Stage0 += apt_get(ospackages=['cpio'])
Stage0 += workdir(directory='/opt/mkl')
command= []
command.append(hpccm.wget().download_step(url='http://registrationcenter-download.intel.com/akdlm/irc_nas/tec/12414/l_mkl_2018.1.163.tgz', directory='/opt/mkl'))
command.append(hpccm.tar().untar_step(tarball='l_mkl_2018.1.163.tgz'))
Stage0 += shell(commands=command)
command=['cd l_mkl_2018.1.163',
                hpccm.sed().sed_step(file='silent.cfg',
                patterns=[r's/ACCEPT_EULA=decline/ACCEPT_EULA=accept/g',
                          r's/ARCH_SELECTED=ALL/ARCH_SELECTED=INTEL64/g',
                          r's/COMPONENTS=DEFAULTS/COMPONENTS=;intel-comp-l-all-vars__noarch;intel-comp-nomcu-vars__noarch;intel-openmp__x86_64;intel-mkl-common__noarch;intel-mkl-installer-license__noarch;intel-mkl-core__x86_64;intel-mkl-core-rt__x86_64;intel-mkl-doc__noarch;intel-mkl-doc-ps__noarch;intel-mkl-gnu__x86_64;intel-mkl-gnu-rt__x86_64;intel-mkl-common-ps__noarch;intel-mkl-core-ps__x86_64;intel-mkl-common-c__noarch;intel-mkl-core-c__x86_64;intel-mkl-common-c-ps__noarch;intel-mkl-gnu-c__x86_64;intel-mkl-common-f__noarch;intel-mkl-core-f__x86_64;intel-mkl-gnu-f-rt__x86_64;intel-mkl-gnu-f__x86_64;intel-mkl-f95-common__noarch;intel-mkl-f__x86_64;intel-mkl-psxe__noarch;intel-psxe-common__noarch;intel-psxe-common-doc__noarch;intel-compxe-pset/g']),
"./install.sh -s silent.cfg",
"cd ..",
"rm -rf *",
"rm -rf /opt/intel/.*.log /opt/intel/compilers_and_libraries_2018.1.163/licensing",
"echo '/opt/intel/mkl/lib/intel64' >> /etc/ld.so.conf.d/intel.conf",
"echo '/opt/intel/compiler/lib/intel64' >> /etc/ld.so.conf.d/intel.conf",
"ldconfig",
"echo 'source /opt/intel/mkl/bin/mklvars.sh intel64' >> /etc/bash.bashrc "]
Stage0 += shell(commands=command)



Stage0 += environment(variables={"MKLROOT": "/opt/intel/compilers_and_libraries_2018.1.163/linux/mkl"})

Stage0 += environment(variables={"LD_LIBRARY_PATH": "/opt/intel/compilers_and_libraries_2018.1.163/linux/tbb/lib/intel64_lin/gcc4.7:/opt/intel/compilers_and_libraries_2018.1.163/linux/compiler/lib/intel64_lin:/opt/intel/compilers_and_libraries_2018.1.163/linux/mkl/lib/intel64_lin:${LD_LIBRARY_PATH}",
"LIBRARY_PATH": "/opt/intel/compilers_and_libraries_2018.1.163/linux/tbb/lib/intel64_lin/gcc4.7:/opt/intel/compilers_and_libraries_2018.1.163/linux/compiler/lib/intel64_lin:/opt/intel/compilers_and_libraries_2018.1.163/linux/mkl/lib/intel64_lin:${LIBRARY_PATH}",
"NLSPATH": "/opt/intel/compilers_and_libraries_2018.1.163/linux/mkl/lib/intel64_lin/locale/%l_%t/%N",
"CPATH": "/opt/intel/compilers_and_libraries_2018.1.163/linux/mkl/include:${CPATH}",
"PKG_CONFIG_PATH": "/opt/intel/compilers_and_libraries_2018.1.163/linux/mkl/bin/pkgconfig:${PKG_CONFIG_PATH}"})

Stage0 += environment(variables={"PATH": "/bigdft/bin:${PATH}",
"LD_LIBRARY_PATH": "/bigdft/lib:${LD_LIBRARY_PATH}",
"PYTHONPATH": "/bigdft/lib/python2.7/site-packages:${PYTHONPATH}",
"PKG_CONFIG_PATH": "/bigdft/lib/pkgconfig:${PKG_CONFIG_PATH}",
"CHESS_ROOT": "/bigdft/bin",
"BIGDFT_ROOT": "/bigdft/bin",
"GI_TYPELIB_PATH": "/bigdft/lib/girepository-1.0:${GI_TYPELIB_PATH}"})

#update ldconfig as /usr/local/lib may not be in the path
Stage0 += shell(commands=['echo "/bigdft/lib" > /etc/ld.so.conf.d/bigdft.conf',
                          'ldconfig'])

#clone example files and recipes

Stage0 += shell(commands=[git().clone_step(repository='https://github.com/BigDFT-group/ContainerXP.git', directory='/docker')])


Stage0 += raw(docker='CMD jupyter-notebook --ip=0.0.0.0 --allow-root --NotebookApp.token=bigdft --no-browser', singularity='%runscript\n jupyter-notebook --ip=0.0.0.0 --allow-root --NotebookApp.token=bigdft --no-browser')

Stage0 += shell(commands=['useradd -ms /bin/bash bigdft'])

Stage0 += raw(docker='USER bigdft')

Stage0 += environment(variables={"XDG_CACHE_HOME": "/home/bigdft/.cache/"})
Stage0 += workdir(directory='/opt/bigdft')
Stage0 += shell(commands=['MPLBACKEND=Agg python -c "import matplotlib.pyplot"'])

#######
## Build stage
#######

Stage1.name = 'build'
Stage1.baseimage(image='sdk')

Stage1 += comment("Build stage", reformat=False)

Stage1 += raw(docker='USER root')
Stage1 += workdir(directory='/opt/')
Stage1 += shell(commands=['rm -rf /opt/bigdft'])
Stage1 += shell(commands=['bzr branch -Ossl.cert_reqs=none lp:bigdft'])
Stage1 += shell(commands=['chmod -R 777 /opt/bigdft', 'mkdir /usr/local/bigdft', 'chmod -R 777 /usr/local/bigdft'])

Stage1 += workdir(directory='/opt/bigdft/build')
Stage1 += shell(commands=['chmod -R 777 /opt/bigdft/build'])
Stage1 += shell(commands=['cp /usr/local/cuda/lib64/stubs/libcuda.so /usr/local/lib/libcuda.so.1'])
Stage1 += shell(commands=['cp /usr/local/cuda/lib64/stubs/libnvidia-ml.so /usr/local/lib/libnvidia-ml.so.1'])
Stage1 += raw(docker='USER bigdft')
Stage1 += environment(variables={"LD_LIBRARY_PATH": "/usr/local/lib:${LD_LIBRARY_PATH}"})
Stage1 += shell(commands=['echo "prefix=\'/usr/local/bigdft\' " > ./buildrc', 
                          'cat ../rcfiles/container.rc >> buildrc',
                          'sed -i "s/configuration()\:/configuration\(\)\:\\n    import os\\n    mkl=os.environ[\'MKLROOT\']/g" ./buildrc',
                          'sed -i \'sed -i \'s|"FCFLAGS=-O2 -fPIC -fopenmp"| "FCFLAGS=-march=core-avx2 -I"""+mkl+"""/include -O2 -fPIC -fopenmp" --with-blas=no --with-lapack=no "--with-ext-linalg=-L"""+mkl+"""/lib/intel64 -Wl,--no-as-needed -lmkl_gf_lp64 -lmkl_gnu_thread -lmkl_core -lgomp -lpthread -lm -ldl"|g\' ./buildrc ',
                          'sed -i "s/CFLAGS=-fPIC -O2 -fopenmp/CFLAGS=-march=core-avx2 -fPIC -O2 -fopenmp/g" ./buildrc',
                          'sed -i "s/LIBS=-ldl -lstdc++ -lgfortran/LIBS=-ldl -lstdc++ -lgfortran -lgomp/g" ./buildrc'
                          ])
#                                                    'sed -i "s/LIBS=-ldl -lstdc++ -lgfortran/LIBS=-ldl -lstdc++ -lgfortran -lgomp/g" ./buildrc'
                                                   #'sed -i \'s|"FCFLAGS=-O2 -fPIC -fopenmp"| "FCFLAGS=-march=core-avx2 -I"""+mkl+"""/include -O2 -fPIC -fopenmp" --with-blas=no --with-lapack=no "--with-ext-linalg=-L"""+mkl+"""/lib/intel64 -Wl,--no-as-needed -lmkl_gf_lp64 -lmkl_gnu_thread -lmkl_core -lgomp -lpthread -lm -ldl"|g\' ./buildrc ',
#Stage1 += shell(commands=['echo "prefix=\'/usr/local/bigdft\' " > ./buildrc', 
#                          'cat ../rcfiles/container_mkl.rc >> buildrc'])

Stage1 += shell(commands=['../Installer.py autogen -y'])

Stage1 += shell(commands=['../Installer.py build -y -a babel -v',
                          'ls /usr/local/bigdft/bin/bigdft'])



#######
## Runtime image
#######

image = 'nvidia/cuda:{}-runtime'.format(cuda_version)
stages.append(Stage())
Stage2 = stages[2]
Stage2.baseimage(image)

Stage2 += comment("Runtime stage", reformat=False)

## Python (use upstream)
Stage2 += apt_get(ospackages=['python'])

## Compiler runtime (use upstream)
Stage2 += gnu.runtime()

Stage2 += apt_get(ospackages=['ocl-icd-libopencl1', 
                              'opensm', 'flex', 'libblas3', 'liblapack3',
                              'python-pip', 'python-dev', 'ipython', 
                              'ipython-notebook', 'python-setuptools', 
                              'build-essential', 'libpcre3', 
                              'python-matplotlib', 'ssh'])

## Mellanox OFED
Stage2 += ofed.runtime()

Stage2 += mpi_lib.runtime()

## FFTW
Stage2 += fftw.runtime()

#'pip install --upgrade pip',
Stage2 += shell(commands=['pip install scipy jupyter'])
Stage2 += shell(commands=['mkdir -p /etc/OpenCL/vendors',
                          'echo "libnvidia-opencl.so.1" > /etc/OpenCL/vendors/nvidia.icd'])

Stage2 += environment(variables={'NVIDIA_VISIBLE_DEVICES': 'all'})
Stage2 += environment(variables={'NVIDIA_DRIVER_CAPABILITIES': 'compute,utility'})

Stage2 += copy(_from="sdk", src="/usr/local/cuda/lib64/stubs/libcuda.so", dest="/usr/local/lib/libcuda.so.1")
Stage2 += copy(_from="sdk", src="/usr/local/cuda/lib64/stubs/libnvidia-ml.so", dest="/usr/local/lib/libnvidia-ml.so.1")

#Stage2 += copy(_from="build", src="/opt/intel", dest="/opt/intel")
Stage2 += copy(_from="build", src="/usr/local/bigdft", dest="/usr/local/bigdft")
Stage2 += copy(_from="build", src="/docker", dest="/docker")

mklroot="/opt/intel/compilers_and_libraries_2018.1.163/linux/mkl/lib/intel64_lin/"
mklroot_out="/usr/local/intel/compilers_and_libraries_2018.1.163/linux/mkl/lib/intel64_lin/"

Stage2 += copy(_from="build", src=mklroot+"libmkl_gf_lp64.so" , dest=mklroot_out+"libmkl_gf_lp64.so")
Stage2 += copy(_from="build", src=mklroot+"libmkl_gnu_thread.so" , dest=mklroot_out+"libmkl_gnu_thread.so")
Stage2 += copy(_from="build", src=mklroot+"libmkl_core.so" , dest=mklroot_out+"libmkl_core.so")
Stage2 += copy(_from="build", src=mklroot+"libmkl_avx2.so" , dest=mklroot_out+"libmkl_avx2.so")
Stage2 += copy(_from="build", src=mklroot+"libmkl_def.so" , dest=mklroot_out+"libmkl_def.so")
Stage2 += copy(_from="build", src="/opt/intel/compilers_and_libraries_2018.1.163/linux/compiler/lib/intel64_lin/libiomp5.so" , dest="/usr/local/intel/compilers_and_libraries_2018.1.163/linux/compiler/lib/intel64_lin/libiomp5.so")

Stage2 += environment(variables={"MKLROOT": "/usr/local/intel/compilers_and_libraries_2018.1.163/linux/mkl"})

Stage2 += environment(variables={"LD_LIBRARY_PATH": "/usr/local/intel/compilers_and_libraries_2018.1.163/linux/compiler/lib/intel64_lin:/usr/local/intel/compilers_and_libraries_2018.1.163/linux/mkl/lib/intel64_lin:${LD_LIBRARY_PATH}",
"LIBRARY_PATH": "/usr/local/intel/compilers_and_libraries_2018.1.163/linux/compiler/lib/intel64_lin:/usr/local/intel/compilers_and_libraries_2018.1.163/linux/mkl/lib/intel64_lin:${LIBRARY_PATH}",
"NLSPATH": "/usr/local/intel/compilers_and_libraries_2018.1.163/linux/mkl/lib/intel64_lin/locale/%l_%t/%N",
"CPATH": "/usr/local/intel/compilers_and_libraries_2018.1.163/linux/mkl/include:${CPATH}",
"PKG_CONFIG_PATH": "/usr/local/intel/compilers_and_libraries_2018.1.163/linux/mkl/bin/pkgconfig:${PKG_CONFIG_PATH}"})

Stage2 += environment(variables={"PATH": "/usr/local/bigdft/bin:${PATH}",
"LD_LIBRARY_PATH": "/usr/local/bigdft/lib:${LD_LIBRARY_PATH}",
"PYTHONPATH": "/usr/local/bigdft/lib/python2.7/site-packages:${PYTHONPATH}",
"PKG_CONFIG_PATH": "/usr/local/bigdft/lib/pkgconfig:${PKG_CONFIG_PATH}",
"CHESS_ROOT": "/usr/local/bigdft/bin",
"BIGDFT_ROOT": "/usr/local/bigdft/bin",
"GI_TYPELIB_PATH": "/usr/local/bigdft/lib/girepository-1.0:${GI_TYPELIB_PATH}"})

Stage2 += environment(variables={"MV2_USE_GPUDIRECT_GDRCOPY": "0",
                                 "MV2_SMP_USE_CMA": "0",
                                 "MV2_ENABLE_AFFINITY": "0",
                                 "MV2_CPU_BINDING_POLICY": "scatter",
                                 "MV2_CPU_BINDING_LEVEL": "socket"})

Stage2 += environment(variables={"XDG_CACHE_HOME": "/root/.cache/"})
Stage2 += shell(commands=['MPLBACKEND=Agg python -c "import matplotlib.pyplot"'])

Stage2 += raw(docker='EXPOSE 8888')

Stage2 += raw(docker='CMD jupyter-notebook --ip=0.0.0.0 --allow-root --NotebookApp.token=bigdft --no-browser', singularity='%runscript\n jupyter-notebook --ip=0.0.0.0 --allow-root --NotebookApp.token=bigdft --no-browser')

Stage2 += shell(commands=['apt-get remove -y --purge build-essential python-setuptools', 
                          'apt-get clean', 
                          'apt-get autoremove -y', 
                          'rm -rf /var/lib/apt/lists/'])


#As of 14/03/18, shifter has a bug with non-ascii characters in files
Stage2 += shell(commands=["rm -rf $(find / | perl -ne 'print if /[^[:ascii:]]/')"])

#update ldconfig as /usr/local/lib may not be in the path
Stage2 += shell(commands=['echo "/usr/local/bigdft/lib" > /etc/ld.so.conf.d/bigdft.conf',
                          'echo "/usr/local/intel/mkl/lib/intel64" >> /etc/ld.so.conf.d/intel.conf',
                          "echo '/usr/local/intel/compiler/lib/intel64' >> /etc/ld.so.conf.d/intel.conf",
                          'ldconfig'])
                          
Stage2 += shell(commands=['useradd -ms /bin/bash bigdft'])
Stage2 += raw(docker='USER bigdft')
Stage2 += environment(variables={"XDG_CACHE_HOME": "/home/bigdft/.cache/"})
Stage2 += shell(commands=['MPLBACKEND=Agg python -c "import matplotlib.pyplot"'])



