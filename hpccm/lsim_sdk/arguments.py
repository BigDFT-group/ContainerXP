import argparse
import hpccm
from distutils.version import StrictVersion
from hpccm.primitives import *
import logging


def arguments():
  parser = argparse.ArgumentParser(description='BigDFT SDK')
  parser.add_argument('--cuda', type=str, default='no',
                      help='CUDA version (default: no)')
  parser.add_argument('--format', type=str, default='docker',
                      choices=['docker', 'singularity'],
                      help='Container specification format (default: docker)')
  parser.add_argument('--oneapi', type=str, default='no',
                      help='OneAPI (default: no)')
  parser.add_argument('--system', type=str, default='ubuntu',
                      choices=['ubuntu', 'centos'],
                      help='Base system (default: ubuntu). Accepted values : ubuntu, centos')
  parser.add_argument('--system_version', type=str, default= None,
                      help='Base system version (optional)')
  parser.add_argument('--target_arch', type=str, default='x86_64',
                      choices=['x86_64', 'arm', 'ppc64le'],
                      help='Target architecture (default: x86_64)')
  parser.add_argument('--jupyter', type=str, default='no',
                      help='Include jupyter server (default: no)')
  parser.add_argument('--blas', type=str, default='default',
                      choices=['default', 'mkl', 'openblas', 'arm'],
                      help='BLAS/LAPACK flavour (default: default)')
  parser.add_argument('--python', type=str, default='default',
                      choices=['default', 'intel'],
                      help='Python flavour (default: default)')
  parser.add_argument('--toolchain', type=str, default=None,
                      choices=['gnu', 'intel', 'llvm', 'arm', 'ibm'],
                      help='Compilation toolchain flavour (default: , or intel for oneapi image)')
  parser.add_argument('--toolchain_version', type=str, default=None,
                      help='Compilation toolchain version (optional)')
  parser.add_argument('--intel_license', type=str, default=None,
                      help='Intel license file or server (optional, only for intel toolchain without oneapi)')
  parser.add_argument('--mpi', type=str, default='ompi',
                      choices=['ompi', 'intel', 'mvapich'],
                      help='MPI library flavour (default: ompi (OpenMPI))')
  parser.add_argument('--mpi_version', type=str,
                      help='MPI library version (optional)')
  parser.add_argument('--binary', type=str, default='yes',
                      help='For other architectures than x86_64, install binary packages to save time (default yes) instead of cross compiling (slow)')
  args = parser.parse_args()
  #hints for hpccm
  if args.system == 'ubuntu':
    if args.system_version == "18.04":
      distro = 'ubuntu18'
    elif args.system_version is not None and args.system_version >= StrictVersion('20.04'):
      distro = 'ubuntu20'
    else:
      distro = 'ubuntu'
      args.system_version="18.04"
  elif args.system == 'centos':
      if args.system_version is None:
        args.system_version = "8"
      distro = args.system + args.system_version
  else:
      distro = None
      logging.warning('Unable to determine the Linux distribution, this may trigger issues in the build')

  #set default toolchain if none is provided (gnu, or intel from oneapi)
  if args.toolchain == None:
    if args.oneapi == 'no':
      args.toolchain = 'gnu'
    else:
      args.toolchain = 'intel'

  if args.target_arch != 'ppc64le' and args.toolchain == 'ibm':
    logging.error('IBM toolchain is only available for ppc64le targets')
  if args.target_arch != 'arm' and ( args.toolchain == 'arm' or args.blas == 'arm'):
    logging.error('ARM compilers and linear algebra libraries are only available for arm platforms')
  if args.target_arch != 'x86_64' and  args.toolchain == 'intel':
    logging.error('Intel compilers are only available for x86_64 targets')
  if args.target_arch != 'x86_64' and  args.oneapi != 'no':
    logging.error('OneAPI is only available for x86_64 targets')
  if args.target_arch != 'x86_64' and  args.blas == 'mkl':
    logging.error('MKL is only available for x86_64 targets')
  if args.target_arch != 'x86_64' and  args.python == 'intel':
    logging.error('Intel Python is only available for x86_64 targets')
  if args.target_arch != 'x86_64' and  args.mpi == 'intel':
    logging.error('Intel MPI is only available for x86_64 targets')

  hpccm.config.set_cpu_architecture(args.target_arch)
  hpccm.config.set_cpu_target(args.target_arch)
  hpccm.config.g_linux_version=args.system_version
  hpccm.config.set_linux_distro(distro)
  hpccm.config.set_container_format(args.format)
  return args, distro

def doc(args, type):
  doc = "LSim SDK image - "
  if type == "sdk":
    doc += "Base : system and main dependencies"
  elif type == "toolchain":
    doc += "Toolchain : Base + Compilers, Python, Linear algebra"
  elif type == "mpi":
    doc += "MPI : Base + Toolchain + MPI library"
  else:
    logging.error('Unknown type in doc :'+ type)
  doc+= """
  Contents:
  System """+args.system + (""" Version """+ args.system_version) if args.system_version is not None else "" +"""
  CUDA """+args.cuda+"""
  OneAPI """+args.oneapi+"""
  Target architecture """+args.target_arch+"""

  This recipe was generated with command line :
$ python hpccm_lsim_"""+type+""".py"""
  if args.system != "ubuntu":
    doc+= " --system="""+args.system
  if args.system_version is not None:
    doc+= " --system_version="""+ args.system_version
  if args.cuda != "no":
    doc+= " --cuda="""+ args.cuda
  if args.oneapi != "no":
    doc+= " --oneapi="""+ args.oneapi
  if args.python != "default":
    doc+= " --python="""+ args.python
  if args.target_arch != "x86_64":
    doc+= " --target_arch="""+args.target_arch
  if args.blas != "default":
    doc+= " --blas="""+args.blas
  if args.jupyter != "no":
    doc+= " --jupyter="""+args.jupyter
  if args.mpi != "ompi":
    doc+= " --mpi="""+args.mpi
  if args.mpi_version is not None:
    doc+= " --mpi_version="""+args.mpi_version

  return doc

def footer(stage):
  stage += raw(docker='USER lsim')
  stage += environment(variables={"XDG_CACHE_HOME": "/home/lsim/.cache/"})
  stage += workdir(directory='/home/lsim')
  stage += shell(commands=['MPLBACKEND=Agg python -c "import matplotlib.pyplot"'])
  return stage
