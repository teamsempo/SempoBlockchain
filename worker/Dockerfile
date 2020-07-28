FROM python:3.6-slim-stretch

RUN apt update && apt -y install gcc libssl-dev

COPY ./worker/requirements.txt /

RUN pip install -r requirements.txt
RUN pip install googlemaps

COPY ./worker /worker
COPY ./config.py /
#ADD ./config_files /config_files
COPY ./worker/_docker_worker_script.sh /
COPY ./worker/_beat_starter.sh /
COPY ./worker/run_beat_if_bitcoin.py /
COPY ./worker/ethereum_filter_test.py /


WORKDIR /

EXPOSE 80

#ENTRYPOINT celery -A worker worker --loglevel=INFO --concurrency=500 --pool=gevent
#CMD ["celery -A worker worker --loglevel=INFO --concurrency=500 --pool=gevent"]

RUN chmod +x /_docker_worker_script.sh
RUN chmod +x /_beat_starter.sh

CMD ["/_docker_worker_script.sh"]

#ENTRYPOINT celery -A worker worker --loglevel=INFO --concurrency=500 --pool=gevent
