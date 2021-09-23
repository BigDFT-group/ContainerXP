#!/usr/bin/env python

from __future__ import print_function
import logging

import hpccm
import hpccm.config
from arguments import arguments, doc, footer
from hpccm.building_blocks import *
from hpccm.primitives import *

def sdk():
  args, distro = arguments()

  tdoc=doc(args, 'sdk')

  #######
  ## SDK stage
  #######
  # Set the image tag based on the specified version (default to 10.0)
  mkl = 'no'
  if args.cuda != 'no':
    image = 'nvidia/cuda:{}-devel-{}{}'.format(args.cuda, args.system, args.system_version)
    if args.oneapi != 'no':
      oneapi = 'no'
      logging.warning('For now we can\'t mix CUDA SDK with OneAPI base image. MKL can still be installed later. Ignoring OneAPI at this step')  
  elif args.oneapi != 'no':
    image = 'intel/oneapi-hpckit:devel-{}{}'.format(args.system, args.system_version)
    if args.target_arch != 'x86_64':
      logging.error('OneAPI is only valid for amd64 processors')
  else:
    image = '{}:{}'.format(args.system, args.system_version if args.system_version is not None else 'latest')

  Stage0 = hpccm.Stage()

  Stage0 += comment(tdoc, reformat=False)
  Stage0.name = 'sdk'
  Stage0.baseimage(image,_distro=distro)
  Stage0 += comment('SDK stage', reformat=False)

  Stage0 += label(metadata={'maintainer': 'bigdft-developers@lists.launchpad.net'})
  Stage0 += environment(variables={'DEBIAN_FRONTEND': 'noninteractive'})
  #SHELL ['/bin/bash', '-c']
  Stage0 += raw(docker='SHELL ["/bin/bash", "-c"]')
  Stage0 += shell(commands=['useradd -ms /bin/bash lsim'])

  #BigDFT packages
  #system independent ones
  ospackages=['autoconf', 'automake', 'bison', 'bzip2', 'chrpath', 'cmake', 'cpio', 'curl', 'doxygen', 'ethtool', 'flex',
              'gdb', 'gettext', 'git', 'gnome-common', 'graphviz', 'intltool', 'kmod', 'libtool', 'lsof', 'net-tools', 'ninja-build',
              'patch', 'pciutils', 'perl', 'pkg-config', 'rsync', 'strace', 'swig', 'tcl', 'tk', 'valgrind', 'vim', 'wget']

  apt_packages=ospackages+[
          'autotools-dev', 'libpcre3-dev', 'libltdl-dev', 'lsb-release', 'libz-dev', 'zlib1g-dev', 'libzmq-dev', 'libmount-dev',
          'iproute2', 'libnl-route-3-200', 'libnuma1', 'linux-headers-generic', 'gtk-doc-tools', 'libxml2-dev', 'libglu1-mesa-dev',
          'libnetcdf-dev', 'libgirepository1.0-dev', 'dpatch', 'libgtk-3-dev', 'libmount-dev', 'locales', 'ssh', 'libyaml-dev']
  yum_packages=ospackages+['pcre-devel', 'libtool-ltdl-devel', 'redhat-lsb', 'glibc-devel', 'zlib-devel', 'zeromq-devel', 'libmount-devel', 
          'iproute', 'libnl3-devel', 'numactl-libs', 'kernel-headers', 'gtk-doc', 'libxml2-devel', 'mesa-libGLU-devel', 'netcdf-devel',
          'gobject-introspection-devel',  'gtk3-devel', 'libmount-devel', 'openssh', 'libarchive', 'libyaml-devel']
  #boost from packages except for oneapi or intel python builds.
  if args.target_arch != "x86_64" or not (args.python == 'intel' or args.oneapi != 'no'):
    apt_packages+=['libboost-dev', 'libboost-python-dev']
    yum_packages+=['boost-devel', 'boost-python3-devel']
  
  if args.cuda != 'no':
    apt_packages += ['ocl-icd-libopencl1']
    yum_packages += ['ocl-icd']
    Stage0 += environment(variables={ 'LD_LIBRARY_PATH': '/usr/local/lib:/usr/local/cuda/lib64:${LD_LIBRARY_PATH}',
                                      'LIBRARY_PATH': '/usr/local/cuda/lib64:${LIBRARY_PATH}',
                                      'NVIDIA_VISIBLE_DEVICES': 'all',
                                      'NVIDIA_DRIVER_CAPABILITIES': 'compute,utility'})
    Stage0 += shell(commands=['mkdir -p /etc/OpenCL/vendors',
                              'echo "libnvidia-opencl.so.1" > /etc/OpenCL/vendors/nvidia.icd',
                              'cp /usr/local/cuda/lib64/stubs/libcuda.so /usr/local/lib/libcuda.so.1',
                              'cp /usr/local/cuda/lib64/stubs/libnvidia-ml.so /usr/local/lib/libnvidia-ml.so.1'])

  Stage0 += packages(apt=apt_packages, yum=yum_packages, powertools=True, epel=True, release_stream=True)

  if args.target_arch == 'x86_64':

    conda_packages = [ 'openbabel', 'six', 'matplotlib', 'ipython',
                      'nbval', 'cython', 'sphinx', 'sphinx_bootstrap_theme', 
                      'watchdog', 'sphinx_rtd_theme', 'flake8', 'ncurses', 'pygobject']
    channels=['conda-forge', 'nvidia']
    if args.blas == 'mkl' and args.oneapi == 'no':
      conda_packages += ['mkl-devel']
      Stage0 += environment(variables={'MKLROOT': '/usr/local/anaconda/'})

    if args.python == 'intel' and args.oneapi == 'no':
      conda_packages += ['intelpython3_core']
      channels += ['intel']
    else:
      conda_packages += ['py-boost']

    if args.jupyter == 'yes':
      conda_packages += [ 'jupyterlab', 'ipykernel']
    
    #conda install
    if args.oneapi == 'no':
      Stage0 += conda(version='4.10.3', python_subversion='py37', channels=channels,
                    eula=True, packages=conda_packages)
      conda_path = '/usr/local/anaconda/'
      commands = ['groupadd conda',
                  'usermod -a -G conda lsim',
                  'chgrp -R conda ' + conda_path,
                  'chmod -R 770 ' + conda_path]
    else:
      #use already present conda on oneapi images
      conda_path = '/opt/intel/oneapi/intelpython/latest/'
      commands = ['conda config --add channels ' + ' --add channels '.join(channels),
        'conda install -y '+ ' '.join(conda_packages),
        'conda clean -afy' ]

    if args.python == 'intel':
      commands += ['ln -s ' + conda_path + 'bin/python3-config' + conda_path + '/bin/python-config']
      #Intel python forgets to provide ncurses https://community.intel.com/t5/Intel-Distribution-for-Python/curses-missing-on-python-3-7/m-p/1201384#M1509
      #Temporarily steal the files from conda-forge package, and use them instead, as it's used in bigdft-tool.
      commands += ['mkdir curses',
                  'cd curses',
                  'wget https://anaconda.org/conda-forge/python/3.7.8/download/linux-64/python-3.7.8-h6f2ec95_1_cpython.tar.bz2',
                  'tar xjf python-3.7.8-h6f2ec95_1_cpython.tar.bz2',
                  'cp ./lib/python3.7/lib-dynload/_curses* ' + conda_path + 'lib/python3.7/lib-dynload/',
                  'cd ..',
                  'rm -rf curses']
    Stage0 += shell(commands=commands)

    #update LIBRARY_PATH as well to allow building against these libs :
    Stage0 += environment(variables={'PATH':  conda_path + '/bin:$PATH',
                                     'LIBRARY_PATH': conda_path + 'lib/:${LIBRARY_PATH}'})
    python_path = conda_path

  else:
    #on other platforms miniconda is not available. Use system python and libraries
    ospack=[
    'python3', 'python3-flake8', 'python3-pip', 'python3-matplotlib',
    'python3-six', 'python3-sphinx', 'python3-sphinx-bootstrap-theme',
    'python3-scipy', 'python3-numpy', 'watchdog', 'python3-ipython',
    'python3-flake8']
    yum=ospack+['python3-Cython', 'python3-sphinx_rtd_theme']
    apt=ospack+['cython3', 'python3-sphinx-rtd-theme', 'python-is-python3']
    if args.jupyter == 'yes':
      apt+=['jupyter-notebook', 'python3-ipykernel']
    Stage0 += packages(apt=apt, yum=yum, powertools=True, epel=True)

    #somehow there is no jupyter package for centos 8.
    if args.system == 'centos' and args.jupyter == 'yes':
      #make python3 and pip3 default
      Stage0 += shell(commands=['ln -s /usr/bin/python3 /usr/local/bin/python',
                              'ln -s /usr/bin/pip3 /usr/local/bin/pip',
                              'pip install jupyter ipykernel'])
    python_path = '/usr/'

  #Install boost with the provided python
  if(args.target_arch == 'x86_64' and (args.python == 'intel' or args.oneapi != 'no')):
    Stage0 += shell(commands=[ 'echo "\\\n\
      using python\\\n\
      : \\\n\
      : `which python`\\\n\
      : `dirname '+python_path+'/include/python*/..`\\\n\
      : '+python_path+'/lib\\\n\
      ;\\\n\
  " > /tmp/user-config.jam' ])
    Stage0+= boost(python=args.python != 'no', 
                  bootstrap_opts=['--with-libraries=python,serialization', '--with-python=`which python`', '--without-icu'],
                  b2_opts=['--user-config=/tmp/user-config.jam', 'install', 'threading=multi', 'variant=release', 'link=shared', 'stage', '--with-regex', '--disable-icu', '--with-thread', '--with-serialization', '--with-iostreams', '--with-python', '--with-system', '--with-test', '-q']) 
  
  if (args.jupyter == 'yes'):
    Stage0 += raw(docker='EXPOSE 8888')
    Stage0 += raw(docker='CMD jupyter lab --ip=0.0.0.0 --allow-root --NotebookApp.token=bigdft --no-browser', 
                  singularity='%runscript\n jupyter lab --ip=0.0.0.0 --allow-root --NotebookApp.token=bigdft --no-browser')

  if args.system == 'ubuntu' and args.system_version >= StrictVersion('20.04') and target_arch == "x86_64":
    Stage0 += environment(variables={'LD_PRELOAD': '/usr/lib/x86_64-linux-gnu/libtinfo.so.6'})

  if args.system == 'ubuntu':
    Stage0 += environment(variables={ "LANG": "en_US.UTF-8",
                                      "LANGUAGE": "en_US.UTF-8",
                                      "LC_ALL": "en_US.UTF-8"})
  else:
    Stage0 += environment(variables={ "LANG": "C.UTF-8",
                                      "LANGUAGE": "C.UTF-8",
                                      "LC_ALL": "C.UTF-8",
                                      "PKG_CONFIG_PATH": "/usr/lib64:/usr/share/lib64"})   

  return Stage0

if __name__ == '__main__':
  print(footer(sdk()))
