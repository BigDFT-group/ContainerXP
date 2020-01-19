doc="""
LSim v_sim build image

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
$ hpccm.py --recipe hpccm_lsim-vsim.py --userarg cuda={}""".format(USERARG.get('cuda', '10.0'))+""" ubuntu={}""".format(USERARG.get('ubuntu', '16.04'))+""" mpi={}""".format(USERARG.get('mpi', 'ompi'))
from hpccm.templates.git import git
#######
## Build v_sim
#######

tag = format(USERARG.get('tag', 'bigdft'))
image = '{}/sdk'.format(tag)
Stage0 += raw(docker='USER root')
Stage0 += comment(doc, reformat=False)
Stage0.name = 'vsim'
Stage0.baseimage(image)
Stage0 += comment("SDK stage", reformat=False)
Stage0 += workdir(directory='/opt/')
Stage0 += shell(commands=['rm -rf /opt/v_sim-dev','mkdir -p /opt/v_sim-dev'])
Stage0 += apt_get(ospackages=['libyaml-dev'])
Stage0 += workdir(directory='/opt/')
Stage0 += shell(commands=['git clone https://gitlab.com/l_sim/v_sim.git v_sim-dev'])
Stage0 += workdir(directory='/opt/v_sim-dev')
Stage0 += shell(commands=['sh autogen.sh'])

cm = hpccm.ConfigureMake(opts=['--with-abinit', '--with-archives', '--with-openbabel', '--with-cube', '--without-strict-cflags'])
command= []
command.append( cm.configure_step())
command.append( cm.build_step())
command.append( cm.install_step())
Stage0 += shell(commands=command)
Stage0 += raw(docker='USER lsim')
Stage0 += environment(variables={"PATH": "/opt/v_sim-dev/bin/:${PATH}"})

