FROM postgis/postgis:14-3.4

RUN apt-get update && apt-get install -y --no-install-recommends \
    postgresql-14-pgrouting \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*
