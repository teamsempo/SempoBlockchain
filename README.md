[![CircleCI](https://circleci.com/gh/teamsempo/SempoBlockchain.svg?style=svg)](https://circleci.com/gh/teamsempo/SempoBlockchain)

# Sempo

Sempo Admin Dashboard, SMS/WhatsApp API and crypto payments infrastructure

Includes:
- Generic spreadsheet upload
- SMS API via Twilio
- ERC20 (Dai) token mirroring
- Vendor android app API

## To run locally machine:

### Install _All_ Python Requirements
Download and install python 3.6 and its respective pip and virtualenv (python 3.7 will break things). Then:
```
python3 -m venv venv
source venv/bin/activate
./install.sh
```

### Install Front-End Requirements
```
cd app
```
```
npm install
```

### Run the web app in a Virtual Env
```
cd app
python ./run.py
```

```
npm run dev
```

### To use SMS API
- Go to root dir
```
cd ..
```
- Run ngrok
```
./ngrok http 9000
```

- Login to Twilio:
https://www.twilio.com/login

- Navigate to the phone number section of Twilio and find the below number
```
+61 428 639 172
```
- Click to edit, scroll to `Messaging` and find `A MESSAGE COMES IN` box
- Add your ngrok server (e.g. `https://a833f3af.ngrok.io/api/sms/`) and save

### Blockchain
Transaction on the blockchain are made using asynchronous workers that consume a celery task-queue.
This means that a lot of development can be done without actually connecting to a blockchain. Likewise, tests have
blockchain endpoints mocked by default.

If you do need to develop with a connection to an actual chain, the best option is to use a [ganache-cli](https://github.com/trufflesuite/ganache-cli)
test-chain running locally, as there are a couple of transaction types (like deploying new token exhanges)
that burn through gas at a rate that makes getting test-eth from a faucet a bit irritating.

Once ganache is installed, run

```
ganache-cli -l 80000000 -i 42 --db './ganacheDB' \
--account="0xc0d863808bc05e06a481622f9e8c1a6c3474320d71736afa3aff7f668284d804,10000000000000000000000000"
```

Here:
- the -l 80000000 argument increases the gas-limit, which is required for token-exchange deployments.
- the --db argument persists your data to a local folder
- the --account argument creates an account with LOTS of test ether, to stop you running out too quickly

gacnache_cli.sh can be used to run this quickly.

You will also need to set your local config to match:
```
[ETHEREUM]
http_provider           = http://127.0.0.1:8545
```


Next you'll need to launch redis and celery. The following settings will work 90% of the time, but can be a _little_
bit flaky because they force all tasks into one worker queue. This is a little annoying to address without running
everything inside docker.

In terminal run:
```
redis-server
```

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

## Testing

Ensure your test_config.ini is up to date.

Create the test databases:
```
create database eth_worker_test;
create database sempo_blockchain_test;
```

Ensure redis-server is running (this is not ideal but necessary atm).

Then run `python invoke_tests.py`, or if that doesn't work, set it up as a runnable in PyCharm: Run -> Edit Configurations -> Add New Configuration (Python) -> set script path as `SempoBlockchain/invoke_tests.py`


## Seed Data
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

