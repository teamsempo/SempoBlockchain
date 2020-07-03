FROM python:3.6-slim-stretch

RUN apt update \
  && apt -y install gcc g++ libffi-dev libstdc++-6-dev python3-dev musl-dev libssl-dev curl

# GE MIGRATION
# For local OSX try:
# https://stackoverflow.com/questions/49025594/osx-ld-library-not-found-for-lssl
RUN apt -y install mysql-server default-libmysqlclient-dev
# PCRE support for USWGI
# https://stackoverflow.com/questions/21669354/rebuild-uwsgi-with-pcre-support
RUN apt -y install libpcre3 libpcre3-dev


COPY ./app/requirements.txt /
COPY ./test_requirements.txt /

RUN cd / && pip install -r requirements.txt && pip install -r test_requirements.txt

RUN apt remove --purge -y gcc g++ libffi-dev libstdc++-6-dev python3-dev musl-dev libssl-dev


COPY ./config.py /src/
RUN mkdir /src/config_files
COPY ./config_files/* /src/config_files/
COPY ./app/server /src/server
COPY ./app/migrations /src/migrations
COPY ./app/manage.py /src
COPY ./app/_docker_app_script.sh /
COPY ./app/test_app /src/test_app
COPY ./app/.coveragerc /src

WORKDIR /

RUN chmod +x /_docker_app_script.sh

ARG GIT_HASH
ENV GIT_HASH=$GIT_HASH

EXPOSE 9000

USER nobody

CMD ["/_docker_app_script.sh"]
