#!/usr/bin/env bash
set +e

cd ../
mkdir ./ganacheDB

ganache-cli -l 80000000 -i 42 \
--account="${MASTER_WALLET_PK},10000000000000000000000000" \
--db './ganacheDB'
