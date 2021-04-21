# --- Modified from https://github.com/edoburu/docker-pgbouncer ---
FROM alpine:3.13

RUN \
  # Download
  VERSION=1.11.0 && \
  apk --update add python3 python3-dev autoconf autoconf-doc automake udns udns-dev curl gcc libc-dev libevent libevent-dev libtool make openssl-dev pkgconfig postgresql-client && \
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

# Install requirements
ADD ./pgbouncer/requirements.txt /requirements.txt
RUN pip3 install -r requirements.txt

# Prepare and use config.py
ADD ./pgbouncer/generate_pgbouncer_config.py /generate_pgbouncer_config.py

COPY ./config.py /
RUN mkdir /config_files
COPY ./config_files/* /config_files/


ADD ./pgbouncer/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]
CMD ["/usr/bin/pgbouncer", "/etc/pgbouncer/pgbouncer.ini"]
