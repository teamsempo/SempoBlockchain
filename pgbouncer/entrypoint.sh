#!/bin/sh

# Based on https://raw.githubusercontent.com/brainsam/pgbouncer/master/entrypoint.sh
echo "Running pgbouncer config generator"
python3 -u generate_pgbouncer_config.py
echo "Generated sempo pgboucner file. Starting pgbouncer"

echo "config contents:"
cat /etc/pgbouncer/pgbouncer.ini