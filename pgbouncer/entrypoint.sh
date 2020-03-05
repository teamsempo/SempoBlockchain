#!/bin/sh
# Based on https://raw.githubusercontent.com/brainsam/pgbouncer/master/entrypoint.sh
set -e
PG_CONFIG_DIR=/etc/pgbouncer
echo "Creating sempo pgbouncer config"
python3 generate_pgbouncer_config.py
exec "$@"
