FROM python:3.12-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        default-jdk-headless \
    && rm -rf /var/lib/apt/lists/*

RUN useradd -m -u 10001 runner
WORKDIR /runner

COPY execute.py /runner/execute.py

USER runner

ENTRYPOINT ["python", "/runner/execute.py"]
