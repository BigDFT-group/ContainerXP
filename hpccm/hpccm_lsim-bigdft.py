doc="""
LSim bigdft build + runtime 

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
from hpccm.templates.git import git
#######
## Build bigdft - Once without avx opitimizations, once with
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
Stage0 += shell(commands=['cp /usr/local/cuda/lib64/stubs/libcuda.so /usr/local/lib/libcuda.so.1'])
Stage0 += shell(commands=['cp /usr/local/cuda/lib64/stubs/libnvidia-ml.so /usr/local/lib/libnvidia-ml.so.1'])

Stage0 += shell(commands=['mkdir /docker',
                          'chmod -R 777 /docker',
                          'mkdir /opt/bigdft/build/avx2',
                          'chmod -R 777 /opt/bigdft/build/avx2',
                          'mkdir /opt/bigdft/build/noavx',
                          'chmod -R 777 /opt/bigdft/build/noavx'])
                          
Stage0 += raw(docker='USER lsim')
Stage0 += environment(variables={"LD_LIBRARY_PATH": "/usr/local/lib:/usr/local/cuda/lib64:${LD_LIBRARY_PATH}"})
Stage0 += environment(variables={"LIBRARY_PATH": "/usr/local/cuda/lib64:${LIBRARY_PATH}"})
Stage0 += environment(variables={"PYTHON": "python"})

Stage0 += shell(commands=[git().clone_step(repository='https://github.com/BigDFT-group/ContainerXP.git', directory='/docker')])

mpi = USERARG.get('mpi', 'ompi')
use_mkl = USERARG.get('mkl', 'yes')
Stage0 += workdir(directory='/opt/bigdft/build/noavx')

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

Stage0 += shell(commands=['sed -i "s/__shfl_down(/__shfl_down_sync(0xFFFFFFFF,/g" ../../psolver/src/cufft.cu']) 

if use_mkl == "yes":
  Stage0 += environment(variables={"MKLROOT": "/usr/local/anaconda/"})

  Stage0 += environment(variables={"LD_LIBRARY_PATH": "/usr/local/mpi/lib:/usr/local/mpi/lib64:/usr/local/anaconda/lib/:/lib/x86_64-linux-gnu:/usr/lib/x86_64-linux-gnu:${LD_LIBRARY_PATH}",
"LIBRARY_PATH": "/usr/local/mpi/lib:/usr/local/mpi/lib64:/lib/x86_64-linux-gnu:/usr/lib/x86_64-linux-gnu:/usr/local/anaconda/lib/:${LIBRARY_PATH}",
"CPATH": "/usr/local/anaconda/include/:${CPATH}",
"PKG_CONFIG_PATH": "/usr/local/anaconda/lib/pkgconfig:${PKG_CONFIG_PATH}"})

Stage0 += shell(commands=['echo "prefix=\'/usr/local/bigdft\' " > ./buildrc',
                          'cat /docker/hpccm/rcfiles/container.rc >> buildrc',
                         '../../Installer.py autogen -y',
                         '../../Installer.py build -y -v'])
#test success
Stage0 += shell(commands=['ls /usr/local/bigdft/bin/bigdft'])

#AVX 2 build
Stage0 += workdir(directory='/opt/bigdft/build/avx2')

Stage0 += environment(variables={"BIGDFT_OPTFLAGS": "-march=core-avx2"})

Stage0 += shell(commands=['../../Installer.py build -y -v -f /docker/hpccm/rcfiles/container.rc',
                          'ls install/bin/bigdft',
                          'cp -r install/lib /usr/local/bigdft/lib/haswell'])

#AVX 512 build
Stage0 += workdir(directory='/opt/bigdft/build/')
Stage0 += environment(variables={"BIGDFT_OPTFLAGS": "-march=skylake-avx512"})

Stage0 += shell(commands=['../Installer.py build -y -v -f /docker/hpccm/rcfiles/container.rc',
                          'ls install/bin/bigdft',
                          'cp -r install/lib /usr/local/bigdft/lib/haswell/avx512_1'])

Stage0 += workdir(directory='/home/lsim')

#######
## Runtime image
#######
cuda_version = USERARG.get('cuda', '10.0')
if cuda_version == "8.0":
  ubuntu_version = "16.04"
else:
  ubuntu_version = USERARG.get('ubuntu', '16.04')
image = 'nvidia/cuda:{}-runtime-ubuntu{}'.format(cuda_version,ubuntu_version)
Stage1.name = 'runtime'
Stage1.baseimage(image)

Stage1 += comment("Runtime stage", reformat=False)

Stage1 += copy(_from="bigdft_build", src="/usr/local/anaconda", dest="/usr/local/anaconda")

Stage1 += environment(variables={"LD_LIBRARY_PATH": "/usr/local/anaconda/lib/:${LD_LIBRARY_PATH}"})
Stage1 += environment(variables={"LIBRARY_PATH": "/usr/local/anaconda:${LIBRARY_PATH}"})
Stage1 += environment(variables={"PATH": "/usr/local/anaconda/bin/:${PATH}"})

## Compiler runtime (use upstream)
Stage1 += gnu().runtime()
tc = gnu().toolchain
tc.CUDA_HOME = '/usr/local/cuda'
Stage1 += environment(variables={'DEBIAN_FRONTEND': 'noninteractive'})
Stage1 += shell(commands=["apt-get update", "apt-get dist-upgrade -y"])
Stage1 += apt_get(ospackages=['ocl-icd-libopencl1', 'libopenbabel4v5',
                              'opensm', 'flex', 'libblas3', 'liblapack3',
                              'build-essential', 'libpcre3', 'openssh-client', 'libxnvctrl0'])


if mpi == "ompi":
  ## normal OFED 
  Stage1 += ofed().runtime(_from='mpi')
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
  Stage1 += mlnx_ofed().runtime(_from='mpi')
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

## FFTW
Stage1 += fftw(version='3.3.7', toolchain=tc).runtime(_from='bigdft_build')

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

  Stage1 += copy(_from="bigdft_build", src=mklroot+"libmkl_gf_lp64.so" , dest=mklroot_out+"libmkl_gf_lp64.so")
  Stage1 += copy(_from="bigdft_build", src=mklroot+"libmkl_gnu_thread.so" , dest=mklroot_out+"libmkl_gnu_thread.so")
  Stage1 += copy(_from="bigdft_build", src=mklroot+"libmkl_core.so" , dest=mklroot_out+"libmkl_core.so")
  Stage1 += copy(_from="bigdft_build", src=mklroot+"libmkl_avx2.so" , dest=mklroot_out+"libmkl_avx2.so")
  Stage1 += copy(_from="bigdft_build", src=mklroot+"libmkl_def.so" , dest=mklroot_out+"libmkl_def.so")
  Stage1 += copy(_from="bigdft_build", src=mklroot+"libiomp5.so" , dest=mklroot_out+"libiomp5.so")

Stage1 += environment(variables={"XDG_CACHE_HOME": "/root/.cache/"})
Stage1 += shell(commands=['MPLBACKEND=Agg python -c "import matplotlib.pyplot"'])

Stage1 += raw(docker='EXPOSE 8888')

Stage1 += raw(docker='CMD jupyter-notebook --ip=0.0.0.0 --allow-root --NotebookApp.token=bigdft --no-browser', singularity='%runscript\n jupyter-notebook --ip=0.0.0.0 --allow-root --NotebookApp.token=bigdft --no-browser')

Stage1 += shell(commands=['apt-get remove -y --purge build-essential', 
                          'apt-get clean', 
                          'apt-get autoremove -y', 
                          'rm -rf /var/lib/apt/lists/'])


#As of 14/03/18, shifter has a bug with non-ascii characters in files
Stage1 += shell(commands=["rm -rf $(find / | perl -ne 'print if /[^[:ascii:]]/')"])

#update ldconfig as /usr/local/lib may not be in the path
Stage1 += shell(commands=['echo "/usr/local/bigdft/lib" > /etc/ld.so.conf.d/bigdft.conf',
                          'echo "/usr/local/anaconda/lib" >> /etc/ld.so.conf.d/conda.conf',
                          'ldconfig'])
                          
Stage1 += shell(commands=['useradd -ms /bin/bash bigdft'])
Stage1 += raw(docker='USER bigdft')
#Stage1 += shell(commands=['echo ". /opt/intel/intelpython2/bin/activate" >> ~/.bashrc '])
Stage1 += environment(variables={"MKLROOT": "/usr/local/anaconda"})

Stage1 += environment(variables={"LD_LIBRARY_PATH": "/usr/local/anaconda/lib:${LD_LIBRARY_PATH}",
"LIBRARY_PATH": "/usr/local/anaconda/lib:${LIBRARY_PATH}",
"CPATH": "/usr/local/anaconda/include:${CPATH}",
"PKG_CONFIG_PATH": "/usr/local/anaconda/lib/pkgconfig:${PKG_CONFIG_PATH}"})

Stage1 += environment(variables={"PATH": "/usr/local/mpi/bin:/usr/local/bigdft/bin:${PATH}",
"LD_LIBRARY_PATH": "/usr/local/mpi/lib:/usr/local/mpi/lib64:/usr/local/bigdft/lib:${LD_LIBRARY_PATH}",
"PYTHONPATH": "/usr/local/bigdft/lib/python3.7/site-packages:${PYTHONPATH}",
"PKG_CONFIG_PATH": "/usr/local/bigdft/lib/pkgconfig:${PKG_CONFIG_PATH}",
"CHESS_ROOT": "/usr/local/bigdft/bin",
"BIGDFT_ROOT": "/usr/local/bigdft/bin",
"GI_TYPELIB_PATH": "/usr/local/bigdft/lib/girepository-1.0:${GI_TYPELIB_PATH}"})

Stage1 += environment(variables={"XDG_CACHE_HOME": "/home/bigdft/.cache/"})
Stage1 += shell(commands=['MPLBACKEND=Agg python -c "import matplotlib.pyplot"'])

