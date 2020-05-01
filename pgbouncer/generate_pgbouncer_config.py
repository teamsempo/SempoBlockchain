print('Starting pgbouncer configuration generation script')
import datetime
import configparser
import os
import boto3
from pathlib import Path

config_parser = configparser.ConfigParser()
secrets_parser = configparser.ConfigParser()
ENV_DEPLOYMENT_NAME = os.environ.get('DEPLOYMENT_NAME')
session = boto3.Session()
client = session.client('s3')
SECRET_BUCKET = os.environ.get("SECRETS_BUCKET", "sarafu-secrets")
CONFIG_FILENAME = "{}_config.ini".format(ENV_DEPLOYMENT_NAME.lower())
SECRETS_FILENAME = "{}_secrets.ini".format(ENV_DEPLOYMENT_NAME.lower())

config_obj = client.get_object(Bucket=SECRET_BUCKET, Key=CONFIG_FILENAME)
config_read_result = config_obj['Body'].read().decode('utf-8')
config_parser.read_string(config_read_result)

secrets_obj = client.get_object(Bucket=SECRET_BUCKET, Key=SECRETS_FILENAME)
secrets_read_result = secrets_obj['Body'].read().decode('utf-8')
secrets_parser.read_string(secrets_read_result)

DATABASE_USER = secrets_parser['DATABASE'].get('user')
DATABASE_PASSWORD = secrets_parser['DATABASE']['password']
DATABASE_HOST = config_parser['DATABASE']['host']
DATABASE_PORT = config_parser['DATABASE'].get('port') or 5432
DATABASE_NAME = config_parser['DATABASE'].get('database')
ETH_DATABASE_NAME = config_parser['DATABASE'].get('eth_database')
BOUNCER_MAX_CLIENT_CONN = config_parser['BOUNCER'].get('max_client_conn') or 1000
BOUNCER_DEFAULT_POOL_SIZE = config_parser['BOUNCER'].get('default_pool_size') or 100
BOUNCER_MAX_DB_CONNECTIONS = config_parser['BOUNCER'].get('max_db_connections') or 100
BOUNCER_MAX_USER_CONNECTIONS = config_parser['BOUNCER'].get('max_user_connections') or 100

# Make pgbouncer folder if not exists
Path('/etc/pgbouncer').mkdir(parents=True, exist_ok=True)

# Writes pgbouncer.ini with configs
ini_file = open('/etc/pgbouncer/pgbouncer.ini', 'w')
ini_file.write(f"""[databases]
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
""".format(vars))
ini_file.close()

# Writes userlist.txt with configs
pw_file = open('/etc/pgbouncer/userlist.txt', 'w')
pw_file.write(f""""{DATABASE_USER}" "{DATABASE_PASSWORD}"
""")
pw_file.close()
