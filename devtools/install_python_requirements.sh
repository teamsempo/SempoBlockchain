#!/bin/bash

cd ../app
pip install -r slow_requirements.txt
pip install -r requirements.txt
cd ../eth_worker
pip install -r requirements.txt
cd ../worker
pip install -r requirements.txt
cd ../test
pip install -r requirements.txt
