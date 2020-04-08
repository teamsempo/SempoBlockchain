FROM python:3.6-slim-stretch

RUN apt update \
  && apt -y install gcc g++ libffi-dev libstdc++-6-dev python3-dev musl-dev libssl-dev

# GE MIGRATION
# For local OSX try:
# https://stackoverflow.com/questions/49025594/osx-ld-library-not-found-for-lssl
RUN apt -y install mysql-server default-libmysqlclient-dev

COPY ./app/requirements.txt /
COPY ./test/requirements.txt /test_requirements.txt

RUN cd / && pip install -r requirements.txt && pip install -r test_requirements.txt

RUN apt remove --purge -y gcc g++ libffi-dev libstdc++-6-dev python3-dev musl-dev libssl-dev


COPY ./config.py ./config_files/* /src/
ADD ./app/server /src/server
ADD ./app/migrations /src/migrations
ADD ./app/manage.py /src
ADD ./app/RedisQueue.py /src
ADD ./app/_docker_app_script.sh /
ADD ./test /src/test
ADD ./invoke_tests.py /src
ADD .coveragerc /src

WORKDIR /

RUN apt -y install curl

RUN chmod +x /_docker_app_script.sh

ARG GIT_HASH
ENV GIT_HASH=$GIT_HASH

EXPOSE 9000

CMD ["/_docker_app_script.sh"]