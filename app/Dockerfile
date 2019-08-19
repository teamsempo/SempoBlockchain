FROM python:3.6-slim-stretch

RUN apt update \
  && apt -y install gcc g++ libffi-dev libstdc++-6-dev python3-dev musl-dev libssl-dev

COPY ./app/requirements.txt /

RUN cd / && pip install -r requirements.txt

RUN apt remove --purge -y gcc g++ libffi-dev libstdc++-6-dev python3-dev musl-dev libssl-dev

ADD ./app/server /src/server
ADD ./app/migrations /src/migrations
ADD ./app/manage.py /src
ADD ./app/RedisQueue.py /src
ADD ./app/_docker_app_script.sh /
#ADD ./config_files /src/config_files
ADD ./config.py /src
ADD ./test /src/test
ADD ./invoke_tests.py /src


WORKDIR /

RUN chmod +x /_docker_app_script.sh

ARG GIT_HASH
ENV GIT_HASH=$GIT_HASH

EXPOSE 9000

CMD ["/_docker_app_script.sh"]
