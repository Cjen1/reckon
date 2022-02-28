
open Core
module OPC = Ocamlpaxos.Client

module Client : Rcclient.S with type t = OPC.t = 
struct 
  module M = Rcclient.Messages
  module L = Rcclient.Log

  type t = OPC.t

  let put client key value cid start_time = 
    let open M in
    let st = Unix.gettimeofday () in
    let%lwt err = 
      match%lwt OPC.op_write client key value with
      | Ok _res -> 
        Lwt.return ""
      | Error (`Msg e) -> 
        L.err (fun m -> m "Operation failed with %s" e);
        Lwt.return e
    in 
    let end_ = Unix.gettimeofday () in
    Lwt.return {
      response_time=end_-.st
    ; client_start = st
    ; queue_start = start_time
    ; end_
    ; clientid = cid
    ; optype = ""
    ; target = ""
    ; err
    }

  let get client key cid start_time = 
    let open M in 
    let st = Unix.gettimeofday () in
    let%lwt err =
      match%lwt OPC.op_read client key with
      | Ok _res -> 
        Lwt.return ""
      | Error (`Msg e) -> 
        L.err (fun m -> m "Operation failed with %s" e);
        Lwt.return e
    in 
    let end_ = Unix.gettimeofday () in
    Lwt.return {
      response_time=end_-.st
    ; client_start = st
    ; queue_start = start_time
    ; end_
    ; clientid = cid
    ; optype = ""
    ; target = ""
    ; err
    }
end 

module Test = Rcclient.Make(Client) 

let main caps id result_pipe = 
  let%lwt client = 
    OPC.new_client ~cid:(Int32.to_int_exn id) ~client_files:caps ()
  in Test.run client id result_pipe

let reporter =
  let report src level ~over k msgf =
    let k _ = over () ; k () in
    let src = Logs.Src.name src in
    msgf
    @@ fun ?header ?tags:_ fmt ->
    Fmt.kpf k Fmt.stdout
      ("[%a] %a %a @[" ^^ fmt ^^ "@]@.")
      Time.pp (Time.now ())
      Fmt.(styled `Magenta string)
      (Printf.sprintf "%14s" src)
      Logs_fmt.pp_header (level, header)
  in
  {Logs.report}

let node_list =
  Command.Arg_type.create @@ String.split ~on:','

let int32 = 
  Command.Arg_type.create Int32.of_string

let command = 
  Core.Command.basic ~summary:"Client Spawner for OcamlPaxos"
    Core.Command.Let_syntax.(
      let%map_open caps = anon ("cap_files" %: node_list) 
      and clientid = anon ("client_id" %: int32)
      and result_pipe = anon ("result_pipe" %: string)
      in 
      fun () ->
        Lwt_main.run @@ main caps clientid result_pipe
    )

let () = 
  Lwt_engine.set (new Lwt_engine.libev ());
  Fmt_tty.setup_std_outputs () ;
  Logs.(set_level (Some Debug));
  Logs.Src.set_level Capnp_rpc.Debug.src (Some Info);
  Logs.set_reporter reporter;
  Core.Command.run command
