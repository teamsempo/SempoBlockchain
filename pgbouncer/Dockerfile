# --- Modified from https://github.com/edoburu/docker-pgbouncer ---
FROM alpine:3.7
ARG VERSION=1.11.0

RUN \
  # Download
  apk --update add python3 python3-dev autoconf autoconf-doc automake udns udns-dev curl gcc libc-dev libevent libevent-dev libtool make man libressl-dev pkgconfig postgresql-client && \
  curl -o  /tmp/pgbouncer-$VERSION.tar.gz -L https://pgbouncer.github.io/downloads/files/$VERSION/pgbouncer-$VERSION.tar.gz && \
  cd /tmp && \
  # Unpack, compile
  tar xvfz /tmp/pgbouncer-$VERSION.tar.gz && \
  cd pgbouncer-$VERSION && \
  ./configure --prefix=/usr --with-udns && \
  make && \
  # Manual install
  cp pgbouncer /usr/bin && \
  mkdir -p /etc/pgbouncer /var/log/pgbouncer /var/run/pgbouncer && \
  chown -R postgres /var/run/pgbouncer /etc/pgbouncer

# Prepare and use config.py
ADD ./pgbouncer/requirements.txt /requirements.txt
ADD ./pgbouncer/generate_pgbouncer_config.py /generate_pgbouncer_config.py
COPY ./config.py config_files/* /

RUN pip3 install -r requirements.txt

ADD ./pgbouncer/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]
CMD ["/usr/bin/pgbouncer", "/etc/pgbouncer/pgbouncer.ini"]
