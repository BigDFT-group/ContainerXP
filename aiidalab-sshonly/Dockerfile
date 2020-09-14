FROM aiidalab/aiidalab-docker-stack:latest

# protect against pip uninstalling conda packages to put older ones instead...
RUN pip install --no-dependencies aiida-sshonly
RUN reentry scan

RUN conda install -c conda-forge biopython

#test installing irene computer from yaml
RUN git clone https://github.com/BigDFT-Group/ContainerXP.git
RUN verdi computer setup --config ContainerXP/aiidalab-sshonly/irene.yml