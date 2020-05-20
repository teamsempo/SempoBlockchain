FROM python:3.6-slim-stretch

RUN apt update && apt -y install gcc libssl-dev libffi-dev curl

COPY ./eth_worker/requirements.txt /
COPY ./test_requirements.txt /

RUN cd / && pip install -r requirements.txt && pip install -r test_requirements.txt

COPY ./eth_worker /
COPY ./config.py config_files/* /
COPY .coveragerc /.coveragerc

WORKDIR /

EXPOSE 80

RUN chmod +x /_docker_worker_script.sh
RUN chmod +x /_beat_starter.sh

CMD ["/_docker_worker_script.sh"]
