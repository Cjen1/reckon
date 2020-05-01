module EB = EndianBytes.LittleEndian
module OPC = Ocamlpaxos.Client

open Message_types
open Message_pb
open Core

let paxos = Logs.Src.create "client" ~doc:"client module"

module L = (val Logs.src_log paxos : Logs.LOG)

let put client key value cid start_time = 
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

let perform op client push_src_o cid start_time () = 
  L.debug (fun m -> m "Submitting request");
  let%lwt res = 
    match op with
  | Put {key; value} -> 
    put client (Int64.to_string key) (Bytes.to_string value) cid start_time
  | Get {key} -> 
    get client (Int64.to_string key) cid start_time
  in 
  L.debug (fun m -> m "Performed op");
  match push_src_o with
  | None -> Lwt.return_unit
  | Some push_src -> push_src#push res

let recv_from_br (br : Lwt_io.input_channel) = 
  let rd_buf = Bytes.create 4 in
  let%lwt () = Lwt_io.read_into_exactly br rd_buf 0 4 in
  let size = EB.get_int32 rd_buf 0 |> Int32.to_int_exn in
  let payload_buf = Bytes.create size in
  let%lwt () = Lwt_io.read_into_exactly br payload_buf 0 size in
  Logs.debug (fun m -> m "received op size = %d\n" size);
  decode_request (Pbrt.Decoder.of_bytes payload_buf) |> Lwt.return

let send payload outfile =
    let p_len = Bytes.length payload in
    let payload_buf = Bytes.create (p_len + 4) in
    Bytes.blit ~src:payload ~src_pos:0 ~dst:payload_buf ~dst_pos:4 ~len:p_len;
    let p_len = Int32.of_int_exn p_len in
    EB.set_int32 payload_buf 0 p_len;
    payload_buf |> Hex.of_bytes |> Hex.hexdump;
    Lwt_io.write_from_exactly outfile payload_buf 0 (Bytes.length payload_buf)

let result_loop res_str outfile =
  let iter v =
    let encoder = Pbrt.Encoder.create () in
    let payload = encode_response v encoder; Pbrt.Encoder.to_bytes encoder in
    send payload outfile
  in 
  let%lwt () = Lwt_stream.iter_s iter res_str in
  L.info (fun m -> m "Finished returning results");
  Lwt.return_unit

let main caps id result_pipe = 
  let%lwt result_pipe = Lwt_io.open_file ~flags:[Unix.O_WRONLY] ~perm:0x0755 ~mode:Lwt_io.output result_pipe in
  let%lwt client = 
    OPC.new_client ~cid:(Int32.to_int_exn id) ~client_files:caps ()
  in
  let in_pipe = Lwt_io.of_fd ~mode:Lwt_io.input Lwt_unix.stdin in

  L.info (fun m -> m "PRELOAD - Start");
  let stream = 
    Lwt_stream.from (fun () -> 
        match%lwt recv_from_br in_pipe with
        | Finalise {msg} -> (L.debug (fun m -> m "Got finalise %s" msg); Lwt.return_none)
        | Start {msg=_msg}-> failwith "Got start during preload phase"
        | Op op -> Lwt.return_some op )
  in 
  let%lwt op_list = 
  Lwt_stream.fold_s (fun v ops -> 
      match v with
      | ({prereq=true; _}) ->
        let%lwt _res = perform v.op_type client None id (Unix.gettimeofday ()) () in 
        Lwt.return ops
      | _ -> 
        v :: ops |> Lwt.return
    ) stream [] 
  in 
  L.info (fun m -> m "READYING - Start");
  let%lwt () = send (Bytes.create 0) result_pipe in
  let%lwt _got_start = 
    match%lwt recv_from_br in_pipe with
    | Start {msg} ->
      L.debug (fun m -> m "Starting with %s" msg);
      Lwt.return_unit 
    | _ -> failwith "Got something other than a ready!"
  in 
  L.info (fun m -> m "EXECUTE - Start");
  let start_time = Unix.gettimeofday() in
  let res_str, push_src = Lwt_stream.create_bounded 50000 in
  let iter {prereq=_; start; op_type=op} = 
    let sleep_time = start +. start_time -. Unix.gettimeofday () in
    let%lwt () = Lwt_unix.sleep sleep_time in
    Lwt.async(perform op client (Some push_src) id (Unix.gettimeofday ()));
    Lwt.return_unit
  in 
  let apply_ops_p = 
    let%lwt () = Lwt_list.iter_s iter op_list in
    L.info(fun m -> m "Finishing applying ops");
    push_src#close;
    Lwt.return_unit
  in 
  let%lwt () = Lwt.join [apply_ops_p; result_loop res_str result_pipe] in
  Lwt_io.close result_pipe

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
