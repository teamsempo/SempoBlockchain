FROM python:3.6-slim-stretch

RUN apt update && apt -y install gcc libssl-dev libffi-dev

COPY ./eth_worker/requirements.txt /

RUN pip install -r requirements.txt

COPY ./ge_worker /
COPY ./config.py config_files* /

WORKDIR /

EXPOSE 80

RUN chmod +x /_start_bonuses_worker.sh
RUN chmod +x /_start_beat_scheduler.sh

