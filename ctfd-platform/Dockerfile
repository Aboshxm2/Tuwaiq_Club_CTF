FROM ctfd/ctfd:3.8.7

USER root
RUN apt-get update \
    && apt-get install -y --no-install-recommends git zip \
    && rm -rf /var/lib/apt/lists/*
COPY plugins/ctfd-whale/requirements.txt /tmp/whale-requirements.txt
RUN pip install --no-cache-dir -r /tmp/whale-requirements.txt
COPY plugins/ctfd-rounds /opt/CTFd/CTFd/plugins/ctfd-rounds
COPY plugins/ctfd-whale /opt/CTFd/CTFd/plugins/ctfd-whale
COPY plugins/ctfd-registration /opt/CTFd/CTFd/plugins/ctfd-registration
COPY themes/tuwaiq /opt/CTFd/CTFd/themes/tuwaiq

ENV ROUNDS_INSTANCE_DIR=/var/lib/ctfd/instances
