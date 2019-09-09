apt update; apt install -y \
  capnproto \
  libcapnp-dev \
  libgmp-dev
  libzmq3-dev m4 perl

add-apt-repository ppa:avsm/ppa
apt update
apt install opam
opam init -a 
opam install -y dune ounit core yojson uri capnp-rpc-lwt capnp-rpc-unix ocaml-protoc zmq-lwt lwt_ppx utop capnp-rpc
