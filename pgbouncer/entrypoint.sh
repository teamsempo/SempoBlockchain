#!/bin/sh
# Based on https://raw.githubusercontent.com/brainsam/pgbouncer/master/entrypoint.sh
echo "Running test file"
python3 generate_pgbouncer_config.py
echo "Generated sempo pgboucner file. Starting pgbouncer"
exec "$@"
