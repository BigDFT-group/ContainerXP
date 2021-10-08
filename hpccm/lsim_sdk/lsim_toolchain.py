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

  elif args.toolchain == 'arm' and "arm" in args.target_arch:
    if args.toolchain_version is None:
      args.toolchain_version = "20.3"
    #override cpu target as "aarch64" is needed, "arm" yielding bad results for optimization flags from archspec
    hpccm.config.set_cpu_target("aarch64")
    arm = arm_allinea_studio(eula=True, microarchitectures=['generic', 'thunderx2t99', 'generic-sve'], version=args.toolchain_version)
    Stage0 += arm
    tc = arm.toolchain
    if args.system == "ubuntu":
      system="Ubuntu-16.04"
    else:
      system="RHEL-"+args.system_version
    Stage0 += environment(variables={'PATH': '/opt/arm/arm-linux-compiler-'+args.toolchain_version+'_Generic-AArch64_'+system+'_aarch64-linux/bin/:${PATH}'})

  elif args.toolchain == 'intel':
    if args.oneapi == 'no':
      intel_license = args.intel_license
      if intel_license is None:
        logging.error("Intel license file or server must be provided to support intel toolchain, please provide intel_license userarg ore use oneapi base image.")
      intel = intel_psxe(eula=True, license=intel_license)
      Stage0 += intel
      tc = intel.toolchain
    else:
      tc = hpccm.toolchain(CC='icc', CXX='icpc', F77='ifort',
                                   F90='ifort', FC='ifort')

  elif args.toolchain == 'ibm' and args.target_arch == "ppc64le":
    xlf_url='http://public.dhe.ibm.com/software/server/POWER/Linux/xl-compiler/eval/ppc64le'
    xlf_vrm='16.1.1'
    Stage0 += packages(apt_keys=[xlf_url+'/ubuntu/public.gpg'], apt_repositories=['deb '+xlf_url+'/ubuntu/ xenial main'], ospackages=['xlf.'+xlf_vrm, 'xlf-license-community.'+xlf_vrm, 'xlc.'+xlf_vrm, 'xlc-license-community.'+xlf_vrm],
                       yum_keys=[xlf_url+'/rhel7/repodata/repomd.xml.key'], yum_repositories=[xlf_url+'/rhel7/ibm-xl-compiler-eval.repo'])
    Stage0 += shell(commands=[
    '/opt/ibm/xlf/'+xlf_vrm+'/bin/xlf_configure <<< 1 >/dev/null',
    '/opt/ibm/xlC/'+xlf_vrm+'/bin/xlc_configure <<< 1 >/dev/null',
    '/opt/ibm/xlf/'+xlf_vrm+'/bin/xlf_configure -cuda null <<< 1 >/dev/null',
    '/opt/ibm/xlC/'+xlf_vrm+'/bin/xlc_configure -cuda null <<< 1 >/dev/null'])
    Stage0 += environment(variables={ 'PATH': '/opt/ibm/xlf/'+xlf_vrm+'/bin:/opt/ibm/xlC/'+xlf_vrm+'/bin:${PATH}'})
    tc = hpccm.toolchain(CC='xlc', CXX='xlc++', F77='xlf',
                                   F90='xlf', FC='xlf')

  else:
    logging.error("no toolchain found or specified, check your inputs, default should be gnu")

  if args.cuda != "no":
    tc.CUDA_HOME = '/usr/local/cuda'

  if args.blas == 'openblas':
    #build and install with default optims
    if args.target_arch == "x86_64" or args.binary=="no":
      Stage0 += openblas(version="0.3.17", ldconfig=True, toolchain=tc, environment=True)
    else:
      Stage0 += packages(apt=['libopenblas-dev'], yum=['openblas-devel'], powertools=True, epel=True)
    #add AVX2 and AVX512 versions
    if args.target_arch == "x86_64":
      Stage0 += openblas(version="0.3.17", ldconfig=False, toolchain=tc, environment=False, make_opts=['TARGET=HASWELL', 'USE_OPENMP=1', 'CROSS=1'], prefix='/var/tmp/haswell')
      Stage0 += shell(commands=['mkdir -p /usr/local/openblas/lib/haswell',
                              'mv /var/tmp/haswell/lib /usr/local/openblas/lib/haswell',
                              'rm -rf /var/tmp/haswell'])
      Stage0 += openblas(version="0.3.17", ldconfig=False, toolchain=tc, environment=False, make_opts=['TARGET=SKYLAKEX', 'USE_OPENMP=1', 'CROSS=1'], prefix='/var/tmp/avx')
      Stage0 += shell(commands=['mkdir -p /usr/local/openblas/lib/avx512_1',
                              'mv /var/tmp/avx/lib /usr/local/openblas/lib/avx512_1',
                              'rm -rf /var/tmp/avx'])
  elif args.blas == "arm":
    Stage0 += environment(variables={'LD_LIBRARY_PATH': '/opt/arm/armpl-'+args.toolchain_version+'.0_Generic-AArch64_'+system+'_gcc_aarch64-linux/lib:${LD_LIBRARY_PATH}',
                                     'LIBRARY_PATH': '/opt/arm/armpl-'+args.toolchain_version+'.0_Generic-AArch64_'+system+'_gcc_aarch64-linux/lib:${LIBRARY_PATH}', 
                                     'ARMPL': '/opt/arm/armpl-'+args.toolchain_version+'.0_Generic-AArch64_'+system+'_gcc_aarch64-linux'})
  elif args.blas != 'mkl':
    Stage0 += packages(apt= ['libblas-dev', 'liblapack-dev'], yum=['blas-devel', 'lapack-devel'], powertools=True, epel=True)

  return Stage0, tc

if __name__ == '__main__':
  from lsim_sdk import sdk
  print(sdk()) 
  stage, tc = toolchain()
  print(footer(stage))