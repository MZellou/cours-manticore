FROM postgis/postgis:14-3.4

ARG HTTP_PROXY
ARG HTTPS_PROXY
ARG NO_PROXY
ENV http_proxy=${HTTP_PROXY} https_proxy=${HTTPS_PROXY} no_proxy=${NO_PROXY}

RUN apt-get update && apt-get install -y --no-install-recommends \
    postgresql-14-pgrouting \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*
