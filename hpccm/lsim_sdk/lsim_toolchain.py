#!/usr/bin/env python

from __future__ import print_function
from distutils.version import LooseVersion, StrictVersion
import logging

import hpccm
import hpccm.config
from arguments import arguments, doc, footer
from hpccm.building_blocks import *
from hpccm.primitives import *

def toolchain():
  Stage0 = hpccm.Stage()

  args, distro = arguments()

  tdoc = doc(args, "toolchain")

  Stage0 += comment(tdoc, reformat=False)
  Stage0.name = 'toolchain'
  test = hpccm.config.g_cpu_arch
  Stage0.baseimage(image='sdk',_distro=distro)
  hpccm.config.set_cpu_architecture(args.target_arch)

  Stage0 += comment("Toolchain stage", reformat=False)
  tc = None
  if args.toolchain == 'gnu':
    # GNU compilers
    tgnu = gnu(version=args.toolchain_version, ldconfig=True)
    # gcc is usually already present and update-alternatives will fail
    if args.system == 'centos' and args.toolchain_version is not None:
      Stage0 += environment(variables={
        "PATH": "/opt/rh/gcc-toolset-"+args.toolchain_version+"/root/usr/bin:${PATH}}",
        "LD_LIBRARY_PATH":"/opt/rh/gcc-toolset-"+args.toolchain_version+"/root/lib/gcc/"+args.target_arch+"-redhat-linux/"+args.toolchain_version+"/:${LD_LIBRARY_PATH}",
        "LIBRARY_PATH":"/opt/rh/gcc-toolset-"+args.toolchain_version+"/root/lib/gcc/"+args.target_arch+"-redhat-linux/"+args.toolchain_version+"/:${LIBRARY_PATH}"
      })

    Stage0 += tgnu
    tc = tgnu.toolchain
  elif args.toolchain == 'llvm':
  
    tllvm = llvm(version=args.toolchain_version, ldconfig=True)
    Stage0 += tllvm
    tc = tllvm.toolchain
    Stage0 += packages(ospackages=['gfortran'], powertools=True, epel=True)
    tc.FC = 'gfortran'
    """ elif toolchain == 'intel' and oneapi == 'no':
      intel_license = USERARG.get('intel_license', None)
      if intel_license is None:
        logging.error("Intel license file or server must be provided to support intel toolchain, please provide intel_license userarg.")
      intel = intel_psxe(eula=True, license=intel_license)
      Stage0 += intel
      tc = intel.toolchain """
  elif args.toolchain == 'arm' and "arm" in args.target_arch:
    if args.toolchain_version is None:
      args.toolchain_version = "20.3"
    arm = arm_allinea_studio(eula=True, microarchitectures=['generic', 'thunderx2t99', 'generic-sve'], version=args.toolchain_version)
    Stage0 += arm
    tc = arm.toolchain
  elif args.toolchain == 'intel' or args.oneapi != 'no':
    tc = hpccm.toolchain(CC='icc', CXX='icpc', F77='ifort',
                                   F90='ifort', FC='ifort')
  
  if args.cuda != "no":
    tc.CUDA_HOME = '/usr/local/cuda'

  if args.blas != 'mkl' and args.blas !='openblas':
    apt_packages = ['libblas-dev', 'liblapack-dev']
    yum_packages = ['blas-devel', 'lapack-devel']
    Stage0 += packages(apt=apt_packages, yum=yum_packages, powertools=True, epel=True)
  elif args.blas == 'openblas':
    #build and install with default optims
    Stage0+=openblas(version="0.3.17", ldconfig=True, toolchain=tc, environment=True)
    #add AVX2 and AVX512 versions
    if args.target_arch == "x86_64":
      Stage0+=openblas(version="0.3.17", ldconfig=False, toolchain=tc, environment=False, make_opts=['TARGET=HASWELL', 'USE_OPENMP=1', 'CROSS=1'], prefix='/var/tmp/haswell')
      Stage0+=shell(commands=['mkdir -p /usr/local/openblas/lib/haswell',
                              'mv /var/tmp/haswell/lib /usr/local/openblas/lib/haswell',
                              'rm -rf /var/tmp/haswell'])
      Stage0+=openblas(version="0.3.17", ldconfig=False, toolchain=tc, environment=False, make_opts=['TARGET=SKYLAKEX', 'USE_OPENMP=1', 'CROSS=1'], prefix='/var/tmp/avx')
      Stage0+=shell(commands=['mkdir -p /usr/local/openblas/lib/avx512_1',
                              'mv /var/tmp/avx/lib /usr/local/openblas/lib/avx512_1',
                              'rm -rf /var/tmp/avx'])
  return Stage0, tc

if __name__ == '__main__':
  from lsim_sdk import sdk
  print(sdk()) 
  stage, tc = toolchain()
  print(footer(stage))