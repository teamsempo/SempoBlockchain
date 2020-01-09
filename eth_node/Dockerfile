FROM ubuntu:latest

RUN apt update \
  && apt -y install curl sudo

RUN ["/bin/bash", "-c", "bash <(curl https://get.parity.io -kL)"]

COPY ./bootnodes.txt /bootnodes.txt
COPY ./spec.json /spec.json

CMD ["parity", "--chain", "/spec.json", "--reserved-peers", "/bootnodes.txt", "--jsonrpc-port", "8500"]