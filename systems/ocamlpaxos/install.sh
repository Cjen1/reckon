apt update; apt install -y \
  opam \
  capnproto \
  libcapnp-dev \
  libgmp-dev
  libzmq3-dev m4 perl

opam init -a 
opam install -y dune ounit core yojson uri capnp-rpc-lwt capnp-rpc-unix ocaml-protoc zmq-lwt lwt_ppx utop
