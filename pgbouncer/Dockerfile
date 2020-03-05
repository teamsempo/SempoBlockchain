# --- Modified from https://github.com/edoburu/docker-pgbouncer ---
# Adds Python, uses config.py

FROM alpine:3.7
ARG VERSION=1.11.0

# Inspiration from https://github.com/gmr/alpine-pgbouncer/blob/master/Dockerfile
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
  # entrypoint installs the configuation, allow to write as postgres user
  cp etc/pgbouncer.ini /etc/pgbouncer/pgbouncer.ini.example && \
  cp etc/userlist.txt /etc/pgbouncer/userlist.txt.example && \
  chown -R postgres /var/run/pgbouncer /etc/pgbouncer

# Prepare and use config.py
COPY ./pgbouncer/requirements.txt ./pgbouncer/generate_pgbouncer_config.py /
COPY ./config.py config_files/* /
RUN pip3 install -r requirements.txt

RUN \
  # Cleanup
  cd /tmp && \
  rm -rf /tmp/pgbouncer*  && \
  apk del --purge autoconf autoconf-doc automake udns-dev curl gcc libc-dev libevent-dev libtool make man libressl-dev pkgconfig
ADD ./pgbouncer/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
USER postgres
EXPOSE 5432
ENTRYPOINT ["/entrypoint.sh"]
CMD ["/usr/bin/pgbouncer", "/etc/pgbouncer/pgbouncer.ini"]
#COPY pgbouncer.ini userlist.txt /etc/pgbouncer/
