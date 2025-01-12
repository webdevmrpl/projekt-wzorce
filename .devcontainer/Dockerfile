FROM python:3.12.3

RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    make \
    git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /notes
