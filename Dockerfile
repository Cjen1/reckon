FROM cjen1/reckon-mininet:latest as base

RUN apt-get update && apt-get install --no-install-recommends -yy -qq \
    build-essential \
    software-properties-common

RUN ln /usr/bin/ovs-testcontroller /usr/bin/controller

# Build dependencies
RUN apt-get update && apt-get install --no-install-recommends -yy -qq \
    autoconf \
    automake \
    libtool \
    curl \
    g++ \
    unzip \
    python-is-python3

RUN apt-get update && apt-get install -yy -qq \
    openjdk-11-jdk

# Runtime dependencies
RUN python -m pip install --upgrade wheel setuptools
ADD requirements.txt requirements.txt
RUN python -m pip install -r requirements.txt
RUN apt-get update && apt-get install --no-install-recommends -yy -qq psmisc iptables

# Test dependencies
RUN apt-get update && apt-get install --no-install-recommends -yy -qq \
    tmux \
    screen \
    strace \
    linux-tools-common \
    tcpdump \
    lsof \
    vim \
    netcat \
    locales-all \
    git

# Add ocons dependencies
RUN bash -c "sh <(curl -L https://nixos.org/nix/install) --daemon"
RUN bash -c "echo 'experimental-features = nix-command flakes' > /etc/nix/nix.conf"

# Build ocons impl and client
# Required for silly reasons that ocaml has difficulty 
RUN git init . 
ADD ./reckon/systems/ocons/ocons-src/flake.nix ./reckon/systems/ocons/ocons-src/flake.lock ./reckon/systems/ocons/ocons-src/dune-project reckon/systems/ocons/ocons-src/
# Cache reckon build without files (also caches client deps)
RUN git add . && bash -l -c "nix build -j auto ./reckon/systems/ocons/ocons-src" 
# Build client
ADD ./reckon/ocaml_client reckon/ocaml_client
ADD ./reckon/systems/ocons/clients reckon/systems/ocons/clients
RUN git add . && bash -l -c "nix build ./reckon/systems/ocons/clients"
# Build build server
ADD ./reckon/systems/ocons/ocons-src reckon/systems/ocons/ocons-src
RUN git add . && bash -l -c "nix build -j auto ./reckon/systems/ocons/ocons-src"

# Add reckon code
ADD . .
ENV PYTHONPATH="/root:${PYTHONPATH}"
ENV SHELL=/bin/bash

# Make directory for logs
RUN mkdir -p /results/logs

# Add built artefacts
COPY --from=etcd-image /reckon/systems/etcd reckon/systems/etcd
COPY --from=zk-image /reckon/systems/zookeeper/bins reckon/systems/zookeeper/bins
