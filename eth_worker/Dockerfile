FROM python:3.6-slim-stretch

RUN apt update && apt -y install gcc libssl-dev

COPY ./eth_worker/requirements.txt /

RUN pip install -r requirements.txt

COPY ./eth_worker /eth_worker
COPY ./config.py /
COPY ./eth_worker/_docker_worker_script.sh /
COPY ./eth_worker/_beat_starter.sh /

WORKDIR /

EXPOSE 80

RUN chmod +x /_docker_worker_script.sh
RUN chmod +x /_beat_starter.sh

CMD ["/_docker_worker_script.sh"]
