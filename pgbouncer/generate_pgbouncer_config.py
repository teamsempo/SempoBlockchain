import config
from pathlib import Path

# Make pgbouncer folder if not exists
Path('/etc/pgbouncer').mkdir(parents=True, exist_ok=True)

# Writes pgbouncer.ini with configs
ini_file = open('/etc/pgbouncer/pgbouncer.ini', 'w')
ini_file.write(f"""[databases]
{config.DATABASE_NAME} = host={config.DATABASE_HOST} port={config.DATABASE_PORT} user={config.DATABASE_USER}
{config.ETH_DATABASE_NAME} = host={config.ETH_DATABASE_NAME} port={config.DATABASE_PORT} user={config.DATABASE_USER}

[pgbouncer]
listen_addr = 0.0.0.0
listen_port = 6543
unix_socket_dir =
user = {config.DATABASE_USER}
auth_file = /etc/pgbouncer/userlist.txt
auth_type = md5
ignore_startup_parameters = extra_float_digits
pool_mode = transaction
max_client_conn = 10000
default_pool_size = 100
max_db_connections = 100
max_user_connections = 100
# Log settings
admin_users = {config.DATABASE_USER}
""".format(vars))
ini_file.close()

# Writes userlist.txt with configs
pw_file = open('/etc/pgbouncer/userlist.txt', 'w')
pw_file.write(f""""{config.DATABASE_USER}" "{config.DATABASE_PASSWORD}"
""")
pw_file.close()