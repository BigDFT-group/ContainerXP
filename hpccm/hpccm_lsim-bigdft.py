doc="""
LSim bigdft build + runtime 

Contents:
  Ubuntu {}""".format(USERARG.get('ubuntu', '16.04'))+"""
  CUDA {}""".format(USERARG.get('cuda', '10.0'))+"""
  MKL
  GNU compilers (upstream)
  Python 3 (intel)
  jupyter notebook and jupyter lab
  v_sim-dev in the optional target

  This recipe was generated with command line :
$ hpccm.py --recipe hpccm_lsim-mpi.py --userarg cuda={}""".format(USERARG.get('cuda', '10.0'))+""" ubuntu={}""".format(USERARG.get('ubuntu', '16.04'))+""" mpi={}""".format(USERARG.get('mpi', 'ompi'))
from hpccm.templates.git import git
from distutils.version import LooseVersion, StrictVersion

#######
## Build bigdft
#######
image = format(USERARG.get('tag', 'bigdft/sdk:latest'))

Stage0 += comment(doc, reformat=False)
Stage0.name = 'bigdft_build'
Stage0.baseimage(image)

Stage0 += raw(docker='USER root')
Stage0 += workdir(directory='/opt/')
Stage0 += shell(commands=['rm -rf /opt/bigdft'])
#Stage0 += shell(commands=['bzr branch -Ossl.cert_reqs=none lp:bigdft'])
Stage0 += shell(commands=['git clone https://gitlab.com/l_sim/bigdft-suite.git ./bigdft'])
Stage0 += shell(commands=['chown -R lsim:lsim /opt/bigdft','chmod -R 777 /opt/bigdft', 'mkdir /usr/local/bigdft', 'chmod -R 777 /usr/local/bigdft'])

Stage0 += workdir(directory='/opt/bigdft/build')
Stage0 += shell(commands=['chmod -R 777 /opt/bigdft/build'])

Stage0 += shell(commands=['mkdir /docker',
                          'chmod -R 777 /docker'])
                          
Stage0 += raw(docker='USER lsim')
Stage0 += environment(variables={"LD_LIBRARY_PATH": "/usr/local/lib:/usr/local/cuda/lib64:${LD_LIBRARY_PATH}"})
Stage0 += environment(variables={"LIBRARY_PATH": "/usr/local/cuda/lib64:${LIBRARY_PATH}"})
Stage0 += environment(variables={"PYTHON": "python"})

Stage0 += shell(commands=[git().clone_step(repository='https://github.com/BigDFT-group/ContainerXP.git', directory='/docker')])
Stage0 += copy(src="./hpccm/rcfiles/container.rc", dest="/tmp/container.rc")


mpi = USERARG.get('mpi', 'ompi')

target_arch = USERARG.get('target_arch', 'x86_64')
import hpccm.config
hpccm.config.set_cpu_architecture(target_arch)

use_mkl = USERARG.get('mkl', 'yes') if target_arch == "x86_64" else "no"

#due to a bug in mvapich <= 2.3.2, aligned_alloc causes segfaults. Default to posix_memalign
#if mpi in ["mvapich2", "mvapich"]:
#  Stage0 += shell(commands=['sed -i "s/AC_CHECK_FUNCS(\[aligned_alloc\])//g" ../../futile/configure.ac'])

#hardcoded compilation for all supported cuda architectures as of cuda 11, as JIT is not supported everywhere yet (windows wsl)
cuda_version=USERARG.get('cuda', '10').split(".",1)[0]
cuda_gencodes = """-arch=sm_50 -gencode=arch=compute_35,code=sm_35 -gencode=arch=compute_37,code=sm_37 -gencode=arch=compute_50,code=sm_50 -gencode=arch=compute_52,code=sm_52 -gencode=arch=compute_60,code=sm_60 -gencode=arch=compute_61,code=sm_61 -gencode=arch=compute_70,code=sm_70"""
if cuda_version  == "10":
  cuda_gencodes += """ -gencode=arch=compute_75,code=sm_75 -gencode=arch=compute_75,code=compute_75"""
elif cuda_version  == "11":
  cuda_gencodes += """ -gencode=arch=compute_75,code=sm_75 -gencode=arch=compute_80,code=sm_80 -gencode=arch=compute_80,code=compute_80"""

Stage0 += environment(variables={"CUDA_GENCODES": '"'+cuda_gencodes+'"'})

#when using arch>30, shfl_down is deprecated
Stage0 += workdir(directory='/opt/bigdft/build/')

Stage0 += shell(commands=['sed -i "s/__shfl_down(/__shfl_down_sync(0xFFFFFFFF,/g" ../psolver/src/cufft.cu']) 


if use_mkl == "yes":
  Stage0 += environment(variables={"MKLROOT": "/usr/local/anaconda/"})

  Stage0 += environment(variables={"LD_LIBRARY_PATH": "/usr/local/mpi/lib:/usr/local/mpi/lib64:/usr/local/anaconda/lib/:/lib/x86_64-linux-gnu:/usr/lib/x86_64-linux-gnu:${LD_LIBRARY_PATH}",
"LIBRARY_PATH": "/usr/local/mpi/lib:/usr/local/mpi/lib64:/lib/x86_64-linux-gnu:/usr/lib/x86_64-linux-gnu:/usr/local/anaconda/lib/:${LIBRARY_PATH}",
"CPATH": "/usr/local/anaconda/include/:${CPATH}",
"PKG_CONFIG_PATH": "/usr/local/anaconda/lib/pkgconfig:${PKG_CONFIG_PATH}"})
if "arm" in target_arch:
  Stage0 += environment(variables={"LD_LIBRARY_PATH": "/opt/arm/armpl-20.3.0_Generic-AArch64_Ubuntu-16.04_gcc_aarch64-linux/lib:${LD_LIBRARY_PATH}",
                                   "LIBRARY_PATH": "/opt/arm/armpl-20.3.0_Generic-AArch64_Ubuntu-16.04_gcc_aarch64-linux/lib:${LIBRARY_PATH}", 
                                   "ARMPL": "/opt/arm/armpl-20.3.0_Generic-AArch64_Ubuntu-16.04_gcc_aarch64-linux"})
  arches = ["-march=armv8-a"]
  folders = ["arm"]
else:
  arches = [None, "-march=core-avx2", "-march=skylake-avx512"]
  folders = ["native", "haswell", "haswell/avx512_1"]


for i in range(len(arches)):
  directory = '/opt/bigdft/build/'+folders[i]
  Stage0 += raw(docker='USER root')
  Stage0 += workdir(directory=directory)
  Stage0 += shell(commands=['chown -R lsim:lsim .','chmod -R 777 .'])
  Stage0 += raw(docker='USER lsim')

  if arches[i] is not None:
    Stage0 += environment(variables={"BIGDFT_OPTFLAGS": arches[i]})

  if i == 0:
    #first will be fully installed, hence prefix is needed, with autogen
    Stage0 += shell(commands=['echo "prefix=\'/usr/local/bigdft\' " > ./buildrc',
                            'cat /tmp/container.rc >> buildrc',
                            '/opt/bigdft/Installer.py autogen -y',
                            '/opt/bigdft/Installer.py build -y -v',
                            'ls /usr/local/bigdft/bin/bigdft'])
  else:
    #others are not installed, so just use rcfile directly
    Stage0 += shell(commands=['/opt/bigdft/Installer.py build -y -v -f /tmp/container.rc',
                          'ls install/bin/bigdft',
                          'cp -r install/lib /usr/local/bigdft/lib/'+folders[i]])

Stage0 += workdir(directory='/home/lsim')

#######
## Runtime image
#######
cuda_version = USERARG.get('cuda', '10.0')
if cuda_version == "8.0":
  ubuntu_version = "16.04"
else:
  ubuntu_version = USERARG.get('ubuntu', '16.04')

repo = "nvidia/cuda"
if "arm" in target_arch:
  repo+="-arm64"

image = '{}:{}-runtime-ubuntu{}'.format(repo,cuda_version,ubuntu_version)
Stage1.name = 'runtime'
Stage1.baseimage(image)

Stage1 += comment("Runtime stage", reformat=False)

target_arch = USERARG.get('target_arch', 'x86_64')
import hpccm.config
hpccm.config.set_cpu_architecture(target_arch)

if "arm" not in target_arch:
  Stage1 += copy(_from="bigdft_build", src="/usr/local/anaconda", dest="/usr/local/anaconda")
  Stage1 += environment(variables={"LD_LIBRARY_PATH": "/usr/local/anaconda/lib/:${LD_LIBRARY_PATH}"})
  Stage1 += environment(variables={"LIBRARY_PATH": "/usr/local/anaconda:${LIBRARY_PATH}"})
  Stage1 += environment(variables={"PATH": "/usr/local/anaconda/bin/:${PATH}"})

## Compiler runtime (use upstream)
Stage1 += gnu().runtime()
tc = gnu().toolchain
tc.CUDA_HOME = '/usr/local/cuda'
Stage1 += environment(variables={'DEBIAN_FRONTEND': 'noninteractive'})

if "arm" in target_arch:
  #on arm platforms miniconda is not available. Use system python and libraries
  ospack=[
  'python3', 'cython3', 'python3-flake8', 'python3-ipykernel',
  'python3-ipython', 'python3-pip', 'jupyter-notebook', 'python3-matplotlib',
  'python3-six', 'python3-sphinx', 'python3-sphinx-bootstrap-theme',
  'python3-scipy', 'python3-numpy',
  'python3-sphinx-rtd-theme', 'watchdog']
  Stage1 += apt_get(ospackages=ospack)

  #make python3 and pip3 default
  Stage1 += shell(commands=['ln -s /usr/bin/python3 /usr/local/bin/python',
                          'ln -s /usr/bin/pip3 /usr/local/bin/pip'])

if ubuntu_version <= StrictVersion('20.0'):
  openbabel='libopenbabel4v5'
else:
  openbabel='libopenbabel6'
Stage1 += apt_get(ospackages=['ocl-icd-libopencl1', openbabel,
                              'opensm', 'flex', 'libblas3', 'liblapack3',
                              'libpcre3', 'openssh-client', 
                              'libxnvctrl0', 'libglib2.0-0'])


if mpi == "ompi":
  ## normal OFED 
  Stage1 += ofed().runtime(_from='bigdft_build')
  mpi_version = USERARG.get('mpi_version', '3.0.0')
  mpi_lib = openmpi(infiniband=False, version=mpi_version, prefix="/usr/local/mpi")
  Stage1 += mpi_lib.runtime(_from='bigdft_build')
  Stage1 += environment(variables={"OMPI_MCA_btl_vader_single_copy_mechanism": "none",
                                   "OMPI_MCA_rmaps_base_mapping_policy":"slot",
                                   "OMPI_MCA_hwloc_base_binding_policy":"none",
                                   "OMPI_MCA_btl_openib_cuda_async_recv":"false",
                                   "OMPI_MCA_mpi_leave_pinned":"true",
                                   "OMPI_MCA_opal_warn_on_missing_libcuda":"false",
                                   "OMPI_MCA_rmaps_base_oversubscribe":"true"})
elif mpi in ["mvapich2", "mvapich"]:
  ## Mellanox OFED
  ofed_version='5.0'
  Stage1 += mlnx_ofed(version='5.0-2.1.8.0', oslabel='ubuntu18.04').runtime(_from='bigdft_build')
  mpi_version = USERARG.get('mpi_version', '2.3')
  Stage1 += apt_get(ospackages=['libpciaccess-dev', 'libnuma1'])
  Stage1 += copy(_from="bigdft_build", src="/usr/local/mpi", dest="/usr/local/mpi")
#  mpi_lib = mvapich2_gdr(version=mpi_version, toolchain=tc, prefix="/usr/local/mpi", cuda_version=cuda_version)
  Stage1 += environment(variables={"MV2_USE_GPUDIRECT_GDRCOPY": "0",
                                 "MV2_SMP_USE_CMA": "0",
                                 "MV2_ENABLE_AFFINITY": "0",
                                 "MV2_CPU_BINDING_POLICY": "scatter",
                                 "MV2_CPU_BINDING_LEVEL": "socket"})
elif mpi == 'impi':
  mpi_lib = intel_mpi(eula=True) #apt_get(ospackages=[intel-mpi])
  Stage1 += mpi_lib.runtime(_from='bigdft_build')

#'pip install --upgrade pip',
#Stage1 += shell(commands=['pip install scipy jupyter'])
Stage1 += shell(commands=['mkdir -p /etc/OpenCL/vendors',
                          'echo "libnvidia-opencl.so.1" > /etc/OpenCL/vendors/nvidia.icd'])

Stage1 += environment(variables={'NVIDIA_VISIBLE_DEVICES': 'all'})
Stage1 += environment(variables={'NVIDIA_DRIVER_CAPABILITIES': 'compute,utility'})

Stage1 += copy(_from="bigdft_build", src="/usr/local/cuda/lib64/stubs/libcuda.so", dest="/usr/local/lib/libcuda.so.1")
Stage1 += copy(_from="bigdft_build", src="/usr/local/cuda/lib64/stubs/libnvidia-ml.so", dest="/usr/local/lib/libnvidia-ml.so.1")

#Stage1 += copy(_from="bigdft_build", src="/opt/intel", dest="/opt/intel")
Stage1 += copy(_from="bigdft_build", src="/usr/local/bigdft", dest="/usr/local/bigdft")
Stage1 += copy(_from="bigdft_build", src="/docker", dest="/docker")
Stage1 += shell(commands=['chmod -R 777 /docker'])

if use_mkl == "yes":
  mklroot="/usr/local/anaconda/lib/"
  mklroot_out="/usr/local/anaconda/lib/"

  Stage1 += copy(_from="bigdft_build", src=mklroot+"libmkl_gf_lp64.so.1" , dest=mklroot_out+"libmkl_gf_lp64.so")
  Stage1 += copy(_from="bigdft_build", src=mklroot+"libmkl_gnu_thread.so.1" , dest=mklroot_out+"libmkl_gnu_thread.so")
  Stage1 += copy(_from="bigdft_build", src=mklroot+"libmkl_core.so.1" , dest=mklroot_out+"libmkl_core.so")
  Stage1 += copy(_from="bigdft_build", src=mklroot+"libmkl_avx2.so.1" , dest=mklroot_out+"libmkl_avx2.so")
  Stage1 += copy(_from="bigdft_build", src=mklroot+"libmkl_def.so.1" , dest=mklroot_out+"libmkl_def.so")
  Stage1 += copy(_from="bigdft_build", src=mklroot+"libiomp5.so.1" , dest=mklroot_out+"libiomp5.so")

Stage1 += environment(variables={"XDG_CACHE_HOME": "/root/.cache/"})
Stage1 += shell(commands=['MPLBACKEND=Agg python -c "import matplotlib.pyplot"'])

Stage1 += raw(docker='EXPOSE 8888')

Stage1 += raw(docker='CMD jupyter-notebook --ip=0.0.0.0 --allow-root --NotebookApp.token=bigdft --no-browser', singularity='%runscript\n jupyter-notebook --ip=0.0.0.0 --allow-root --NotebookApp.token=bigdft --no-browser')

if "arm" in target_arch:
  Stage1 += copy(_from="bigdft_build", src="/opt/arm/armpl-20.3.0_Generic-AArch64_Ubuntu-16.04_gcc_aarch64-linux", dest="/opt/arm/armpl-20.3.0_Generic-AArch64_Ubuntu-16.04_gcc_aarch64-linux")
  Stage1 += copy(_from="bigdft_build", src="/opt/arm/armpl-20.3.0_ThunderX2CN99_Ubuntu-16.04_gcc_aarch64-linux", dest="/opt/arm/armpl-20.3.0_ThunderX2CN99_Ubuntu-16.04_gcc_aarch64-linux")
  Stage1 += environment(variables={"LD_LIBRARY_PATH": "/opt/arm/armpl-20.3.0_Generic-AArch64_Ubuntu-16.04_gcc_aarch64-linux/lib:${LD_LIBRARY_PATH}"})
#  Stage1 += arm_allinea_studio(eula=True, microarchitectures=['generic', 'thunderx2t99', 'generic-sve']).runtime(_from='bigdft_build')

#As of 14/03/18, shifter has a bug with non-ascii characters in files
Stage1 += shell(commands=["rm -rf $(find / | perl -ne 'print if /[^[:ascii:]]/')"])

#update ldconfig as /usr/local/lib may not be in the path
Stage1 += shell(commands=['echo "/usr/local/bigdft/lib" > /etc/ld.so.conf.d/bigdft.conf',
                          'echo "/usr/local/anaconda/lib" >> /etc/ld.so.conf.d/conda.conf',
                          'ldconfig'])
                          
Stage1 += shell(commands=['useradd -ms /bin/bash bigdft'])
Stage1 += raw(docker='USER bigdft')
#Stage1 += shell(commands=['echo ". /opt/intel/intelpython2/bin/activate" >> ~/.bashrc '])
if use_mkl == "yes":
  Stage1 += environment(variables={"MKLROOT": "/usr/local/anaconda"})

Stage1 += environment(variables={"LD_LIBRARY_PATH": "/usr/local/anaconda/lib:${LD_LIBRARY_PATH}",
"LIBRARY_PATH": "/usr/local/anaconda/lib:${LIBRARY_PATH}",
"CPATH": "/usr/local/anaconda/include:${CPATH}",
"PKG_CONFIG_PATH": "/usr/local/anaconda/lib/pkgconfig:${PKG_CONFIG_PATH}",
"PATH": "/usr/local/anaconda/bin:${PATH}"})

Stage1 += environment(variables={"PATH": "/usr/local/mpi/bin:/usr/local/bigdft/bin:${PATH}",
"LD_LIBRARY_PATH": "/usr/local/mpi/lib:/usr/local/mpi/lib64:/usr/local/bigdft/lib:${LD_LIBRARY_PATH}",
"PYTHONPATH": "/usr/local/bigdft/lib/python3.6/site-packages:/usr/local/bigdft/lib/python3.7/site-packages::/usr/local/bigdft/lib/python3.8/site-packages:${PYTHONPATH}",
"PKG_CONFIG_PATH": "/usr/local/bigdft/lib/pkgconfig:${PKG_CONFIG_PATH}",
"CHESS_ROOT": "/usr/local/bigdft/bin",
"BIGDFT_ROOT": "/usr/local/bigdft/bin",
"GI_TYPELIB_PATH": "/usr/local/bigdft/lib/girepository-1.0:${GI_TYPELIB_PATH}"})

Stage1 += environment(variables={"XDG_CACHE_HOME": "/home/bigdft/.cache/"})
Stage1 += shell(commands=['MPLBACKEND=Agg python -c "import matplotlib.pyplot"'])

