#!/bin/bash
set -em
su -c 'verdi computer show irene ||verdi computer setup --non-interactive  --config /opt/irene.yml' ${SYSTEM_USER}
