# Container eXPeriences Project

This project collects the files related to the containers associated to BigDFT project.
Dockerfiles as well as Bench files will be associated to this project such that the container experience
can be maintained and tested.

Some of the files of this projects:

 * `install_docker_ce.sh` is a facility script that can be used to install the docker community edition on your local workstation. Run it not being sudo, it will then prompt for the superuser password.

 *  `bigdftmk` is a script that triggers the execution of the docker image. With this script it should be easy to mount the source directory
    of the bigdft suite and to create binaries that are then compiled with user's permission. The script contains a number of facilities
    which would create the dockerline to be executed. One can encapsulate this script in other commands for automation.

 * `latexmk` is a script that make possible the compilation of a beamer presentation by using the BigDFT layout. By running `latexmk -s <inputfile>` the bigdft/latex container is employed to compile the inputfile. A `-o <outdir>` option can be included to redirect the temporary latex files to another directory.
