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

let log_param =
  Log_extended.Command.(
    setup_via_params ~log_to_console_by_default:(Stderr Color)
      ~log_to_syslog_by_default:false ())

let () =
  let command =
    Command.async_spec ~summary:"Reckon OCons client"
      Command.Spec.(
        empty
        +> anon ("node_list" %: node_list)
        +> anon ("client_id" %: arg_int32)
        +> log_param)
      (fun node_list cid () () ->
        let global_level = Async.Log.Global.level () in
        let global_output = Async.Log.Global.get_output () in
        List.iter [Reckon.logger] ~f:(fun log ->
            Async.Log.set_level log global_level ;
            Async.Log.set_output log global_output ) ;
        let client = Client.new_client node_list in
        let%bind () = Reckon_client.run client cid in
        Async.exit 0 )
  in
  Command.run command
