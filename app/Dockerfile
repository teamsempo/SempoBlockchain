FROM python:3.8-slim-buster

RUN apt update \
  && apt -y install gcc g++ libffi-dev libstdc++-8-dev python3-dev musl-dev libssl-dev curl

COPY ./app/requirements.txt /
COPY ./test_requirements.txt /

RUN cd / && pip install -r requirements.txt && pip install -r test_requirements.txt

RUN apt remove --purge -y gcc g++ libffi-dev libstdc++-8-dev python3-dev musl-dev libssl-dev

#RUN apt -y install libcairo2 libpango-1.0-0 libpangocairo-1.0-0 libgdk-pixbuf2.0-0 libffi-dev shared-mime-info 

COPY ./config.py /src/
RUN mkdir /src/config_files
COPY ./config_files/* /src/config_files/
COPY ./app/server /src/server
COPY ./app/migrations /src/migrations
COPY ./app/manage.py /src
COPY ./app/run.py /src
COPY ./app/_docker_app_script.sh /
COPY ./app/test_app /src/test_app
COPY ./app/.coveragerc /src

WORKDIR /

RUN chmod +x /_docker_app_script.sh

ARG GIT_HASH
ENV GIT_HASH=$GIT_HASH

EXPOSE 9000

CMD ["/_docker_app_script.sh"]
