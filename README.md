<a href="https://withsempo.com">
    <img width="200" src="app/server/static/media/sempo_logo_teal.png" alt="Sempo Logo" />
</a>

---

[![CircleCI](https://circleci.com/gh/teamsempo/SempoBlockchain.svg?style=shield)](https://circleci.com/gh/teamsempo/SempoBlockchain)
[![GitHub](https://img.shields.io/github/license/teamsempo/sempoblockchain)](LICENSE)
[![Codecov](https://img.shields.io/codecov/c/github/teamsempo/SempoBlockchain)](https://codecov.io/gh/teamsempo/SempoBlockchain)

Sempo Admin Dashboard and crypto financial inclusion infrastructure with USSD, Android and NFC Payments

## To run locally:

### Install Requirements

**Postgres**

We use [postgres](https://www.postgresql.org/) for regular (non-blockchain) data persistance.

If you plan on using the quick setup script, be sure to install the [PSQL](https://www.postgresql.org/docs/current/app-psql.html) terminal application as well

**Redis**
[Redis](https://redis.io/) is used for passing tasks to an asynchronous worker queue

**Local Test Blockchain**

You can use your preferred implementation of the Ethereum Blockchain to test things locally. Our setup scripts use the v6.4.1 [Ganache-CLI](https://github.com/trufflesuite/ganache-cli)

```
npm install -g ganache-cli@6.4.1
```

**Python**

Download and install python 3.6 and its respective pip and virtualenv (**python 3.7 will break things**). Then:

```
python3 -m venv venv
source venv/bin/activate
./install.sh
```

**Front-End**

Our frontend uses react.

```
cd app
npm install
```

To build and watch for changes:

```
npm run dev
```

### Create config files

The platform uses three kinds of config files:

- deployment specific config: things that aren't sensitive, and change on a per deployment basis
- deployment specific secrets: things that ARE sensitive, and change on a per deployment basis
- common secrets: things that ARE sensitive, and can be the same between all deployments

There's already a reasonable set of local configs in `config_files/local_config.ini`
To create some suitable secrets quickly:

```
cd config files
python generate_secrets.py
```

### Quick Setup Script

(Requires PSQL to run)

For quick setup, run `quick_setup_script.sh` with `MASTER_WALLET_PK` set as an environment variable to the master private key found in `/config_files/secret/local_secrets.ini/`.

```
quick_setup_script.sh [activation path for your python env]
```

The script will:

- Reset your local Sempo state
- Launch Ganache and Redis
- Create an adminstrator account with email `admin@acme.org` and password `C0rrectH0rse`
- Create a reserve token and bonded token
  When the script has finished running\*, you can start your own app and worker processes (see next section) and continue on.
  \*This can be a little hard to identify because ganache continues to run, but a good indicator is if `Bringing Ganache to foreground` is echo'd in the console

### Run the app in a Virtual Env

```
cd app
python ./run.py
```

### Launch the worker

Transaction on the blockchain are made using asynchronous workers that consume a celery task-queue.

```
cd eth_worker
celery -A eth_manager worker --loglevel=INFO --concurrency=8 --pool=eventlet -Q=celery,processor
```

## Details and Other Options

### Enable the Blockchain Simulator

If you wish to forego installing ganache and redis, you can enable a simulator mode. What this does is bypass the eth*worker and any queued jobs, and instead returns dummy responses to any functions relying on eth_worker. \_Be warned, this will make your database fall out of sync with any ganache instance you have set up so use this with care*, but it is very useful in eliminating dependencies when working on any features in the API or frontend. It also allows you to run `contract_setup_script.py` without additional dependencies.

To enable simulator mode, open `/config_files/local_config.ini` and add the line `enable_simulator_mode = true` under the `[APP]` heading.

### Ganache Detailed Setup

Transaction on the blockchain are made using asynchronous workers that consume a celery task-queue. If you are using ganache, the following command will launch ganache in a compatible manner.

```
ganache-cli -l 80000000 -i 42 --db './ganacheDB' \
--account=[YOUR PRIVATE KEY],10000000000000000000000000"
```

Here:

- the -l 80000000 argument increases the gas-limit, which is required for token-exchange deployments.
- the --db argument persists your data to a local folder. This can be a little flaky, so if you get any strange errors, try deleting the contents of the `ganacheDB` directory and retrying.
- the --account argument creates an account with LOTS of test ether, to stop you running out too quickly. Note that you'll need to provide the 'master wallet' private key that's found within your config files.

The bash script gacnache_cli.sh can be used to run this quickly. Be sure to set the MASTER_WALLET_PK environment variable beforehand.

If it's not already, you will also need to set your local config to match:

```
[ETHEREUM]
http_provider           = http://127.0.0.1:8545
```

### Blockchain Workers

In order for the workers to run, you'll need to launch redis and celery. On production we run multiple workers to handle different tasks, but locally you can just launch one worker to run everything.

First launch the redis server, which acts as a message-broker for celery tasks. In terminal run:

```
redis-server
```

If you get some message about `Creating Server TCP listening socket *:6379: bind: Address already in use`, this is probably just because redis is already running (did you use the quick setup script). You can probably carry on!

Start celery:

```
cd eth_worker
celery -A eth_manager worker --loglevel=INFO --concurrency=8 --pool=eventlet -Q=celery,processor
```

You can also add a runtime configuration with the `script path` set as the path to your virtual env `[path-to-your-python-env]/bin/celery`.

Set the `parameters` to the run line above.

Lastly, if you want to run full blockchain tests, set the environment variable `FORCE_BLOCKCHAIN_TESTS` to `True`

### Database Migration:

Migrate differs slightly for the main app (uses flask-migrate version of alembic) versus the ethereum worker (uses pure alembic).

For more commands, see Alembic documentation: https://alembic.sqlalchemy.org/en/latest/

**For main app:**

First, setup your database `sempo_blockchain_local`, using the username and password from the local config file.

Next, to update your database to the latest migration file:

```
cd app
python manage.py db upgrade
```

To create a new migration:

Make the modifications to the model file to reflect the database changes.

```
python manage.py db migrate
```

Remember to commit the file!

Sometimes, branches split and you will have multiple heads:

```
python manage.py db merge heads
```

**For ethereum worker:**

First, setup your database `eth_worker`, using the username and password from the local config file.

Next, to update your database to the latest migration file:

```
cd eth_worker
alembic upgrade head
```

To create a migrations file (remember to commit the file!):

```
alembic revision --autogenerate
```

### Vendor App

- Pull the below repo and follow steps
  https://github.com/enjeyw/SempoVendorMobile

(if you have installed the prod vendor app, ensure you clear data and uninstall before installing from dev)

### USSD Interface

To run and test the USSD interface locally there are two options.

- Run `ussd.py` with the necessary environment variables
- Setup ngrok and use Africa's Talking or another USSD simulator

## Testing

Ensure your test_config.ini and test_secrets.ini files are up to date. Test secrets can be generated using the previous python script, and supplying `test` as the filename:

```
cd config files
python generate_secrets.py test
```

Create the test databases:

```
create database eth_worker_test;
create database sempo_blockchain_test;
```

Ensure redis-server is running (this is not ideal but necessary atm).

Then run `python invoke_tests.py`, or if that doesn't work, set it up as a runnable in PyCharm: Run -> Edit Configurations -> Add New Configuration (Python) -> set script path as `SempoBlockchain/invoke_tests.py`

## Seed Data

(Currently broken!!)
You can quickly create seed data for a local machine, including exchanges and blockchain transactions:

1. Clear all data out of ur databases by running /app/migrations/clear_seed_dev.py
2. Launch Redis, ganache & Celery as per above.
3. Create new data by running seed_dev.py No guarantees for anything if you try and run this more than once
   without clearing your databases!

## Sempo Specific Setup

We use [Mozilla Sops](https://github.com/mozilla/sops/) for sharing low-risk dev keys and secrets.

If you're working on a sempo-specfic deployment, contact nick or tristan to gain decryption access. You will be given an
AWS account - set up your credentials locally using [AWS CLI](https://docs.aws.amazon.com/cli/latest/userguide/install-cliv2.html), setting the profile name to `sempo` inside the [credentials file](https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-files.html).

Once you've been authorised, you can access config settings by first creating a directory called `config_files` in the root folder, and running `_SOPS_load.py` inside `.sempoconfig` (note that you have to be in the `.sempoconfig` directory.
This will extract all keys into the config_files folder. To encrypt them again for sharing on git, run
`_SOPS_save.py`.

Not that SOPS doesn't handle merge conflicts currently - if you try and merge an encrypted file, it will break in a bad way!

Instead, if you need to merge in two config files, you need to save the old config, load the new one and merge them by hand.
