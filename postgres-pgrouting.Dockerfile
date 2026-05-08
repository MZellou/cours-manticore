FROM postgis/postgis:18-3.6-alpine

ARG HTTP_PROXY
ARG HTTPS_PROXY
ARG NO_PROXY
ENV http_proxy=${HTTP_PROXY} https_proxy=${HTTPS_PROXY} no_proxy=${NO_PROXY}

# pgRouting + pgvector
RUN apk add --no-cache curl ca-certificates \
    && apk add --no-cache --repository https://dl-cdn.alpinelinux.org/alpine/edge/testing \
      postgresql18-pgrouting \
    || (echo "pgRouting not in edge/testing, building from source..." \
        && apk add --no-cache --virtual .build-deps git build-base postgresql-dev \
        && git clone --depth 1 --branch main https://github.com/pgRouting/pgrouting.git /tmp/pgrouting \
        && mkdir -p /tmp/pgrouting/build && cd /tmp/pgrouting/build \
        && cmake .. -DPOSTGRESQL_PG_CONFIG=/usr/local/bin/pg_config \
        && make -j$(nproc) && make install \
        && cd / && rm -rf /tmp/pgrouting \
        && apk del .build-deps) \
    && apk add --no-cache git build-base llvm19-dev clang19 \
    && git clone --depth 1 --branch v0.8.2 https://github.com/pgvector/pgvector.git /tmp/pgvector \
    && cd /tmp/pgvector \
    && make USE_PGXS=1 \
    && make USE_PGXS=1 install \
    && rm -rf /tmp/pgvector \
    && apk del git build-base llvm19-dev clang19
