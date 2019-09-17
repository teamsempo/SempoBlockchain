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
Download and install python 3.6
```
python3 -m venv venv
source venv/bin/activate
cd app
pip install -r slow_requirements.txt
pip install -r requirements.txt
cd ../eth_worker
pip install -r requirements.txt
cd ../worker
pip install -r requirements.txt
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
In terminal run:
```
redis-server
```

Start celery:
```
cd eth_worker
celery -A eth_trans_manager worker --loglevel=INFO --concurrency=500 --pool=eventlet
```

### Database Migration:

Migrate differs slightly for the main app (uses flask-migrate version of alembic) versus the ethereum worker (uses pure alembic).

For more commands, see Alembic documentation: https://alembic.sqlalchemy.org/en/latest/

####For main app:

First, setup your database `sempo_blockchain_local`, using the username and password from the local config file.

Next, to update your database to the latest migration file:

```
cd app
python manage.py db upgrade
```

To create a migrations file (remember to commit the file!):

```
python manage.py db migrate
```

Sometimes, branches split and you will have multiple heads:

```
python manage.py db merge heads
```

####For ethereum worker:

First, setup your database `eth_worker`, using the username and password from the local config file.

Next, to update your database to the latest migration file:

```
cd eth_worker
alembic migrate head
```

To create a migrations file (remember to commit the file!):

```
alembic revision --autogenerate
```

### Vendor App
- Pull the below repo and follow steps
https://github.com/enjeyw/SempoVendorMobile

(if you have installed the prod vendor app, ensure you clear data and uninstall before installing from dev)

## To setup a production deployment
Follow this guide
https://docs.google.com/document/d/1PLJgCwRvHDdb_goWl0fMy8eFBfNUk2F3GzLHIiPzV0A/edit
