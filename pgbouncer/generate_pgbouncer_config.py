print('Starting pgbouncer configuration generation script')
import os
import sys
from pathlib import Path

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import config

from config import (
    DATABASE_NAME,
    DATABASE_HOST,
    DATABASE_PORT,
    DATABASE_USER,
    DATABASE_PASSWORD,
    ETH_DATABASE_NAME,
    BOUNCER_MAX_CLIENT_CONN,
    BOUNCER_DEFAULT_POOL_SIZE,
    BOUNCER_MAX_DB_CONNECTIONS,
    BOUNCER_MAX_USER_CONNECTIONS,
)

# Make pgbouncer folder if not exists
Path('/etc/pgbouncer').mkdir(parents=True, exist_ok=True)

config_string = f"""[databases]
{DATABASE_NAME} = host={DATABASE_HOST} port={DATABASE_PORT} user={DATABASE_USER}
{ETH_DATABASE_NAME} = host={DATABASE_HOST} port={DATABASE_PORT} user={DATABASE_USER}

[pgbouncer]
listen_addr = 0.0.0.0
listen_port = 6543
unix_socket_dir =
user = postgres
auth_file = /etc/pgbouncer/userlist.txt
auth_type = md5
ignore_startup_parameters = extra_float_digits
max_client_conn = {BOUNCER_MAX_CLIENT_CONN}
default_pool_size = {BOUNCER_DEFAULT_POOL_SIZE}
max_db_connections = {BOUNCER_MAX_DB_CONNECTIONS}
max_user_connections = {BOUNCER_MAX_USER_CONNECTIONS}
server_idle_timeout = 0
"""

print(config_string)

# Writes pgbouncer.ini with configs
ini_file = open('/etc/pgbouncer/pgbouncer.ini', 'w')
ini_file.write(config_string)
ini_file.close()

# Writes userlist.txt with configs
pw_file = open('/etc/pgbouncer/userlist.txt', 'w')
pw_file.write(f""""{DATABASE_USER}" "{DATABASE_PASSWORD}"
""")
pw_file.close()
