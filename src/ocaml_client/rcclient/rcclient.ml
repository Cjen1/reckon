
module Messages = Message_types

let src = Logs.Src.create "client" ~doc:("Resolving consensus test logger")

module Log = (val Logs.src_log src : Logs.LOG)

module type S = sig
  type t

  val put : t -> bytes -> bytes -> int32 -> float -> Message_types.response Lwt.t
  val get : t -> bytes -> int32 -> float -> Message_types.response Lwt.t
end 


module Make (Cli : S) : sig
  type client = Cli.t
  val run : client -> int32 -> string -> unit Lwt.t 
end = struct
  module EB = EndianBytes.LittleEndian
  module MT = Message_types
  module MP = Message_pb
  module PD = Pbrt.Decoder
  module PE = Pbrt.Encoder
  module L = Log

  type client = Cli.t

  let perform op client cid start_time = 
    L.debug (fun m -> m "Submitting request");
    let%lwt res = 
      let keybuf = Bytes.create 8 in
      match op with
      | MT.Put {key; value} -> (
          Stdlib.Bytes.set_int64_ne keybuf 0 key;
          Cli.put client keybuf value cid start_time
        )
      | MT.Get {key} -> (
          Stdlib.Bytes.set_int64_ne keybuf 0 key;
          Cli.get client keybuf cid start_time
        )
    in 
    L.debug (fun m -> m "Performed op");
    Lwt.return res

  let recv_from_br (br : Lwt_io.input_channel) = 
    let rd_buf = Bytes.create 4 in
    let%lwt () = Lwt_io.read_into_exactly br rd_buf 0 4 in
    let size = EB.get_int32 rd_buf 0 |> Int32.to_int in
    let payload_buf = Bytes.create size in
    let%lwt () = Lwt_io.read_into_exactly br payload_buf 0 size in
    Logs.debug (fun m -> m "received op size = %d\n" size);
    MP.decode_request (PD.of_bytes payload_buf) |> Lwt.return

  let send payload outfile =
    let p_len = Bytes.length payload in
    let payload_buf = Bytes.create (p_len + 4) in
    Bytes.blit payload 0 payload_buf 4 p_len;
    let p_len = Int32.of_int p_len in
    EB.set_int32 payload_buf 0 p_len;
    Lwt_io.write_from_exactly outfile payload_buf 0 (Bytes.length payload_buf)

  let result_loop res_list outfile =
    let iter v =
      let encoder = PE.create () in
      let payload = MP.encode_response v encoder; PE.to_bytes encoder in
      send payload outfile
    in 
    L.info (fun m -> m "Starting to return results");
    let%lwt () = Lwt_list.iter_s iter res_list in
    L.info (fun m -> m "Finished returning results");
    Lwt.return_unit

  let run client id result_pipe = 
    let%lwt result_pipe = Lwt_io.open_file ~flags:[Unix.O_WRONLY] ~perm:0x0755 ~mode:Lwt_io.output result_pipe in
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
          | (MT.{prereq=true; _}) ->
            let%lwt _res = perform v.op_type client id (Unix.gettimeofday ()) in 
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
    let iter_op_list MT.{prereq=_; start; op_type=op} =
      let sleep_time = start +. start_time -. Unix.gettimeofday () in
      let%lwt () = Lwt_unix.sleep sleep_time in
      perform op client id (Unix.gettimeofday ())
    in 
    let%lwt res_list = Lwt_list.map_p iter_op_list op_list in
    L.info (fun m -> m "Finished applying ops");
    result_loop res_list result_pipe
end 
