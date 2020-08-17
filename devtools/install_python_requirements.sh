#!/bin/bash

cd ../app
pip install -r slow_requirements.txt
pip install -r requirements.txt
cd ../eth_worker
pip install -r requirements.txt
cd ../
pip install -r test_requirements.txt
