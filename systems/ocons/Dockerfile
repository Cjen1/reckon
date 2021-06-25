FROM ocaml/opam:ubuntu-21.04-ocaml-4.10

# Add the opam file to install dependencies outside of likely rebuild path
ADD ocons/ocons-core.opam /system/ocons/ocons-core.opam
RUN sudo apt install -y pkg-config liblapacke-dev libopenblas-dev zlib1g-dev
RUN cd /system/ocons && opam install --deps-only .

ADD Makefile /system/Makefile
ADD ocons /system/ocons
RUN cd /system && make system

ADD clients /system/clients
RUN cd /system && make client
