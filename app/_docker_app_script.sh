#!/bin/bash
echo Container mode: $CONTAINER_MODE

cd app
echo upgrading database
python manage.py db upgrade

echo upgrading dataset

python manage.py update_data

