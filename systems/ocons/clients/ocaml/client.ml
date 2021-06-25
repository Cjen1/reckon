open! Core
open! Async
open! Ppx_log_async

open! Ocons_core

module Reckon_client = Reckon.Make (struct
    type t = Client.t

    let put client key value time = 
      let%bind Client.op_read 
  end )
