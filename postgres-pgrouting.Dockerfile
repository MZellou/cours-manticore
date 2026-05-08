FROM postgis/postgis:17-3.5

ARG HTTP_PROXY
ARG HTTPS_PROXY
ARG NO_PROXY
ENV http_proxy=${HTTP_PROXY} https_proxy=${HTTPS_PROXY} no_proxy=${NO_PROXY}

# pgRouting + pgvector via PGDG apt (already configured in base image)
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       postgresql-17-pgrouting \
       postgresql-17-pgvector \
    && rm -rf /var/lib/apt/lists/*
