
# Hpccm nvidia dockerfile recipe generator

Instructions:

 * Install NVidia's hpccm fir `pip install hpccm`
 * Modify the recipe of the dockerfile accordingly
 * Generate the `Dockerfile` with the command:
    `hpccm.py --recipe hpccm_bigdft.py --userarg v_sim-builtin=no > Dockerfile`
 * Prepare the container image with
   `<sudo> docker build --target=<sdk,build,nothing> - < Dockerfile`
