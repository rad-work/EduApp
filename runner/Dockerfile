FROM python:3.12-slim

RUN useradd -m -u 10001 runner
WORKDIR /runner

COPY execute.py /runner/execute.py

USER runner

ENTRYPOINT ["python", "/runner/execute.py"]
