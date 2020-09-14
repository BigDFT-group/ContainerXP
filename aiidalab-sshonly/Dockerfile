FROM aiidalab/aiidalab-docker-stack:latest

# protect against pip uninstalling conda packages to put older ones instead...
RUN pip install --no-dependencies aiida-sshonly
RUN reentry scan

RUN conda install -c conda-forge biopython

#test installing irene computer from yaml
COPY irene.yml /opt/irene.yml
COPY my_init/setup_computer.sh /etc/my_init.d/50_setup-computer.sh