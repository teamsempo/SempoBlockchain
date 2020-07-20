FROM redis:alpine
RUN echo never > /sys/kernel/mm/transparent_hugepage/enabled
COPY redis.conf /usr/local/etc/redis/redis.conf
CMD [ "redis-server", "/usr/local/etc/redis/redis.conf" ]