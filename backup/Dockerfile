FROM postgres:16-alpine

RUN apk add --no-cache dcron

COPY backup.sh /backup.sh
COPY entrypoint.sh /entrypoint.sh

RUN chmod +x /backup.sh /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
