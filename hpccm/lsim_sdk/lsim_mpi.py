#!/usr/bin/env python

from __future__ import print_function
from distutils.version import LooseVersion, StrictVersion
import logging

import hpccm
import hpccm.config
from arguments import arguments, doc, footer
from hpccm.building_blocks import *
from hpccm.primitives import *

def mpi(tc):
  args, distro = arguments()

  tdoc = doc(args, "toolchain")
  Stage0 = hpccm.Stage()
  Stage0.name = 'mpi'
  Stage0.baseimage(image='toolchain',_distro=distro)
  Stage0 += comment("mpi", reformat=False)

  Stage0 += raw(docker='USER root')

  # MPI libraries : default ompi, v 4.0.0
  if args.mpi == "ompi":
    #normal OFED 
    Stage0 += ofed()
    if args.mpi_version is None:
      args.mpi_version = "4.1.1"
    if args.target_arch == "x86_64" or args.binary=="no":
      mpi_lib = openmpi(infiniband=True, pmix='internal', version=args.mpi_version , cuda = (args.cuda != 'no'), prefix="/usr/local/mpi", toolchain=tc)
      Stage0 += environment(variables={"OMPI_MCA_btl_vader_single_copy_mechanism": "none",
                                      "OMPI_MCA_rmaps_base_mapping_policy":"slot",
                                      "OMPI_MCA_hwloc_base_binding_policy":"none",
                                      "OMPI_MCA_btl_openib_cuda_async_recv":"false",
                                      "OMPI_MCA_mpi_leave_pinned":"true",
                                      "OMPI_MCA_opal_warn_on_missing_libcuda":"false",
                                      "OMPI_MCA_rmaps_base_oversubscribe":"true",
                                      "PATH": "/usr/local/mpi/bin/:${PATH}",
                                      "LD_LIBRARY_PATH": "/usr/local/mpi/lib:/usr/local/mpi/lib64:${LD_LIBRARY_PATH}"})
    else:
      mpi_lib = packages(apt=['libopenmpi-dev'], yum=['openmpi-devel'], powertools=True, epel=True)
  elif args.mpi in ["mvapich2", "mvapich"]:
    # Mellanox OFED
    ofed_version='5.0'
    Stage0 += mlnx_ofed(version='5.0-2.1.8.0', oslabel='ubuntu18.04')
    if args.cuda != 'no':
      if args.mpi_version is None:
        args.mpi_version = "2.3.6"
      Stage0 += gdrcopy()
      if args.cuda == "8.0":
        gnu_version="5.4.0"
      elif args.cuda == "11.0" and args.mpi_version is not None and args.mpi_version >= StrictVersion("2.3.4"):
        gnu_version="9.3.0"
      elif args.cuda >= StrictVersion("11.2") and args.mpi_version is not None and args.mpi_version >= StrictVersion("2.3.6"):
        gnu_version="7.3.0"
      else:
        gnu_version="4.8.5"
      if args.mpi_version >= StrictVersion("2.3.4"):
        release = 1
      else:
        release = 2
      #Issue on mvapich gdr 2.3.6 as hpccm can't find it on the website.
      if(args.mpi_version == "2.3.6"):
        Stage0 += packages (apt=['cpio', 'libnuma1', 'libpciaccess0', 'openssh-client', 'rpm2cpio', 'libgfortran4'], 
                            yum=['libpciaccess', 'numactl-libs', 'openssh-clients', 'libgfortran'], powertools=True, epel=True)
        _commands=[
          'mkdir -p /var/tmp && wget -q -nc --no-check-certificate -P /var/tmp http://mvapich.cse.ohio-state.edu/download/mvapich/gdr/2.3.6/mofed'+ofed_version+'/mvapich2-gdr-cuda11.2.mofed'+ofed_version+'.gnu'+gnu_version+'-2.3.6-1.el7.'+args.target_arch+'.rpm',        
          'cd / ']
        if args.system == 'centos':
          _commands+='rpm --install --nodeps /var/tmp/mvapich2-gdr*.rpm'
        else:
          _commands+='rpm2cpio /var/tmp/mvapich2-gdr-*.rpm | cpio -id',
        _commands+=['(test -f /usr/bin/bash || ln -s /bin/bash /usr/bin/bash) ',
          'ln -s /usr/local/cuda/lib64/stubs/nvidia-ml.so /usr/local/cuda/lib64/stubs/nvidia-ml.so.1',
          'rm -rf /var/tmp/mvapich2-*.rpm']
        mpi_lib = shell(commands=_commands)
      else:
        mpi_lib = mvapich2_gdr(version=args.mpi_version, prefix="/usr/local/mpi",mlnx_ofed_version=ofed_version, cuda_version=args.cuda, release=release, gnu_version=gnu_version)
      Stage0 += packages(apt=['libxnvctrl-dev libibmad5'], yum=['libxnvctrl-devel infiniband-diags'], powertools=True, epel=True)
    else:
      mpi_lib = mvapich2(version=args.mpi_version, prefix="/usr/local/mpi", toolchain=tc)
      Stage0 += packages(apt=['libibmad5'], yum=['infiniband-diags'], powertools=True, epel=True)


    Stage0 += environment(variables={"PATH": "/usr/local/mpi/bin/:${PATH}",
                                  "LD_LIBRARY_PATH": "/usr/local/lib/:/usr/local/mpi/lib:/usr/local/mpi/lib64:${LD_LIBRARY_PATH}",
                                  "MV2_USE_GPUDIRECT_GDRCOPY": "0",
                                  "MV2_SMP_USE_CMA": "0",
                                  "MV2_ENABLE_AFFINITY": "0",
                                  "MV2_CPU_BINDING_POLICY": "scatter",
                                  "MV2_CPU_BINDING_LEVEL": "socket"})
  elif args.mpi == 'intel':
    mpi_lib = intel_mpi(eula=True) #apt_get(ospackages=[intel-mpi])

  Stage0 += mpi_lib

  #Workaround missing install on mvapich_gdr in hpccm
  if args.mpi in ["mvapich2", "mvapich"] and args.cuda != 'no':
    Stage0 += shell(commands=['mkdir /usr/local/mpi/',
                              'cp -r /opt/mvapich2/gdr/{}/no-mpittool/no-openacc/cuda**/mofed{}/mpirun/gnu{}/* /usr/local/mpi'.format(args.mpi_version,ofed_version,gnu_version)])

  #update ldconfig as /usr/local/lib may not be in the path
  Stage0 += shell(commands=['echo "/usr/local/mpi/lib" > /etc/ld.so.conf.d/mpi.conf',
                            'echo "/usr/local/mpi/lib64" >> /etc/ld.so.conf.d/mpi.conf',
                            'echo "/usr/local/anaconda/lib" >> /etc/ld.so.conf.d/anaconda.conf',
                            'echo "/bigdft/lib" > /etc/ld.so.conf.d/bigdft.conf',
                            'ldconfig'])
  if args.cuda != 'no':
    Stage0 += shell(commands=['cp /usr/local/cuda/lib64/stubs/libcuda.so /usr/local/lib/libcuda.so.1'])
    Stage0 += shell(commands=['cp /usr/local/cuda/lib64/stubs/libnvidia-ml.so /usr/local/lib/libnvidia-ml.so.1'])

  Stage0 += raw(docker='USER lsim')
  return Stage0

if __name__ == '__main__':
  from lsim_sdk import sdk
  print(sdk()) 
  from lsim_toolchain import toolchain
  stage, tc = toolchain()
  print(stage)
  print(footer(mpi(tc)))