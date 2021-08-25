FROM tiangolo/uwsgi-nginx-flask:python3.7

RUN apt update \
  && apt -y install gcc g++ libffi-dev libstdc++-8-dev python3-dev musl-dev libssl-dev curl

COPY ./app/requirements.txt /
COPY ./test_requirements.txt /

RUN cd / && pip install -r requirements.txt && pip install -r test_requirements.txt

RUN apt remove --purge -y gcc g++ libffi-dev libstdc++-8-dev python3-dev musl-dev libssl-dev

RUN apt -y install libcairo2 libpango-1.0-0 libpangocairo-1.0-0 libgdk-pixbuf2.0-0 libffi-dev shared-mime-info

COPY ./config.py /app/
RUN mkdir /app/config_files
COPY ./config_files/* /app/config_files/
COPY ./app/server /app/server
COPY ./app/migrations /app/migrations
COPY ./app/manage.py /app
COPY ./app/_docker_app_script.sh /
COPY ./app/test_app /app/test_app
COPY ./app/.coveragerc /app
COPY ./app/uwsgi.ini /app

WORKDIR /

RUN chmod +x /_docker_app_script.sh

ARG GIT_HASH
ENV GIT_HASH=$GIT_HASH
ENV STATIC_URL="content"

EXPOSE 80
EXPOSE 9000
ENTRYPOINT ["/_docker_app_script.sh"]
