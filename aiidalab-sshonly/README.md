## Setup

initial run :

`./run_aiidalab.sh 8888 ${aiidalab_home_folder}`


To complete irene setup:

- Copy the ssh private key inside ${aiidalab_home_folder}/.ssh/ folder (as root) and change its ownership to aiida user.

 `sudo cp ~/.ssh/id_rsa ${aiidalab_home_folder}/.ssh/`\
`sudo chown 1000:1000 ${aiidalab_home_folder}/.ssh/id_rsa`

- Setup connection:

	`docker ps` to get the id of the running container
	`docker exec --user aiida -ti ${container_id} bash`

	inside the container:

`verdi computer configure sshonly irene_yaml`

		* User name [aiida]: ireneaccount
		* port Nr [22]:
		* Look for keys [True]:
		* SSH key file []: /home/aiida/.ssh/id_rsa (or other name)
		* Connection timeout in s [60]:
		* Allow ssh agent [True]:
		* If bouncing is needed :
		* SSH proxy command []: ssh -i /home/aiida/.ssh/id_rsa account@proxy -W irene-amd-fr.ccc.cea.fr:22
		* Compress file transfers [True]:
		* GSS auth [False]:
		* GSS kex [False]:
		* GSS deleg_creds [False]:
		* GSS host [irene-amd-fr.ccc.cea.fr]:
		* Load system host keys [True]:
		* Key policy (RejectPolicy, WarningPolicy, AutoAddPolicy) [RejectPolicy]: AutoAddPolicy
		* Connection cooldown time (s) [30.0]: