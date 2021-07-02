open! Core
open! Async
open! Ppx_log_async
open! Ocons_core

module Reckon_client = Reckon.Make (struct
  type t = Client.t

  let put client k v =
    let open Client in
    let open Deferred.Result in
    match%bind.Deferred op_write client ~k ~v with
    | Success ->
        return ()
    | Failure s ->
        fail s
    | ReadSuccess _ ->
        fail "Got read success on write"

  let get client k =
    let open Client in
    let open Deferred.Result in
    match%bind.Deferred op_read client k with
    | ReadSuccess s ->
        return (Bytes.of_string s)
    | Failure s ->
        fail s
    | Success ->
        fail "Got write success on read operataion"
end)

let network_address =
  let parse s =
    match String.split ~on:':' s with
    | [addr; port] ->
        Fmt.str "%s:%s" addr port
    | _ ->
        Fmt.failwith "Expected ip:port | path rather than %s " s
  in
  Command.Arg_type.create parse

let arg_int32 = Command.Arg_type.create Int32.of_string

let node_list =
  Command.Arg_type.comma_separated ~allow_empty:false network_address

let () =
  let command =
    Command.async_spec ~summary:"Reckon OCons client"
      Command.Spec.(
        empty
        +> anon ("node_list" %: node_list)
        +> anon ("client_id" %: arg_int32)
        +> anon ("result_pipe" %: string))
      (fun node_list cid result_pipe () ->
        let client = Client.new_client node_list in
        let%bind () = Reckon_client.run client cid result_pipe in
        Async.exit 0 )
  in
  Command.run command
