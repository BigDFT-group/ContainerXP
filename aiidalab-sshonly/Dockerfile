FROM aiidalab/aiidalab-docker-stack:latest


#jupyternotify is useful for notebooks submitting batches of asynchronous jobs.
# protect against pip uninstalling conda packages to put older ones instead...
RUN pip install jupyternotify && pip install --upgrade aiida-bigdft && pip install --no-dependencies aiida-sshonly && reentry scan
RUN conda install -c conda-forge biopython && conda install -c omnia pdbfixer 

#test installing irene computer from yaml
COPY irene.yml /opt/irene.yml
COPY my_init/setup_computer.sh /etc/my_init.d/50_setup-computer.sh

ENV PYTHONPATH /home/aiida/local-packages:/home/aiida
