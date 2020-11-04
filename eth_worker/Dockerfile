FROM python:3.8-slim-buster

RUN apt update && apt -y install gcc libssl-dev libffi-dev curl:

COPY ./eth_worker/requirements.txt /
COPY ./test_requirements.txt /

RUN cd / && pip install -r requirements.txt && pip install -r test_requirements.txt

COPY ./eth_worker /

COPY ./config.py /
RUN mkdir /config_files
COPY ./config_files/* /config_files/

COPY ./third_party/celo_eth_account /celo_eth_account


WORKDIR /

EXPOSE 80

RUN chmod +x /_docker_worker_script.sh

CMD ["/_docker_worker_script.sh"]