open! Core
open! Async
open! Ppx_log_async

let logger =
  let open Async_unix.Log in
  create ~level:`Info ~output:[] ~on_error:`Raise
    ~transform:(fun m -> Message.add_tags m [("src", "Reckon")])
    ()

module type Client = sig
  type t

  val put : t -> bytes -> bytes -> (unit, string) Deferred.Result.t

  val get : t -> bytes -> (bytes, string) Deferred.Result.t
end

module Make (Cli : Client) : sig
  type client = Cli.t

  val run : client -> int32 -> unit Deferred.t
end = struct
  module EB = EndianBytes.LittleEndian
  module MT = Message_types
  module MP = Message_pb
  module PD = Pbrt.Decoder
  module PE = Pbrt.Encoder

  type client = Cli.t

  let mk_response res clientid client_start queue_start end_ optype =
    let res = Result.join res in
    MT.
      { err= (match res with Ok _ -> "" | Error s -> s)
      ; client_start=
          client_start |> Time.to_span_since_epoch |> Time.Span.to_sec
      ; queue_start= queue_start |> Time.to_span_since_epoch |> Time.Span.to_sec
      ; end_= end_ |> Time.to_span_since_epoch |> Time.Span.to_sec
      ; optype
      ; response_time= -1.
      ; clientid
      ; target= "" }

  let perform op client start_time clientid =
    let keybuf = Bytes.create 8 in
    match op with
    | MT.Put {key; value} ->
        Stdlib.Bytes.set_int64_ne keybuf 0 key ;
        let actual_start = Time.now () in
        let%bind res =
          let open Deferred.Monad_infix in
          try_with (fun () -> Cli.put client keybuf value)
          >>| function Ok v -> Ok v | Error e -> Error (Exn.to_string e)
        in
        let fin = Time.now () in
        return @@ mk_response res clientid actual_start start_time fin "Write"
    | MT.Get {key} ->
        Stdlib.Bytes.set_int64_ne keybuf 0 key ;
        let actual_start = Time.now () in
        let%bind res =
          let open Deferred.Monad_infix in
          try_with (fun () -> Cli.get client keybuf)
          >>| function Ok v -> Ok v | Error e -> Error (Exn.to_string e)
        in
        let fin = Time.now () in
        return @@ mk_response res clientid actual_start start_time fin "Read"

  let fail_on_incomplete ?msg v =
    match%bind v with
    | `Ok ->
        Deferred.Result.return ()
    | `Eof i ->
        Deferred.Result.fail (i, msg)

  let recv (r : Async.Reader.t) =
    let open Deferred.Result.Let_syntax in
    let rd_buf = Bytes.create 4 in
    let%bind () =
      Reader.really_read r ~pos:0 ~len:4 rd_buf
      |> fail_on_incomplete ~msg:"len_read"
    in
    let size = EB.get_int32 rd_buf 0 |> Int32.to_int_exn in
    let payload_buf = Bytes.create size in
    let%bind () =
      Reader.really_read r ~pos:0 ~len:size payload_buf
      |> fail_on_incomplete ~msg:"payload_read"
    in
    [%log.debug logger "recieved op" (size : int)] ;
    MP.decode_request (PD.of_bytes payload_buf) |> return

  let send payload ?(flush = false) outfile =
    let p_len = Bytes.length payload in
    let payload_buf = Bytes.create (p_len + 4) in
    Bytes.blit ~src:payload ~src_pos:0 ~dst:payload_buf ~dst_pos:4 ~len:p_len ;
    EB.set_int32 payload_buf 0 (Int32.of_int_exn p_len) ;
    Writer.write_bytes outfile ~pos:0 ~len:(Bytes.length payload_buf)
      payload_buf ;
    match flush with true -> Writer.flushed outfile | false -> Deferred.unit

  let result_loop res_list outfile =
    let iter v =
      let encoder = PE.create () in
      let payload =
        MP.encode_response v encoder ;
        PE.to_bytes encoder
      in
      send payload outfile
    in
    [%log.info logger "Starting to return results"] ;
    let%bind () = Deferred.List.iter ~how:`Sequential ~f:iter res_list in
    [%log.info logger "Results returned"] ; Deferred.unit

  let sexp_of_request = function
    | MT.Start {msg} ->
        [%message "Start" (msg : string)]
    | MT.Finalise {msg} ->
        [%message "Finalise" (msg : string)]
    | MT.Op _ ->
        [%message "Op"]

  let run client clientid =
    [%log.debug logger "waiting for coordinator"] ;
    let in_pipe = Lazy.force Reader.stdin in
    let result_pipe = Lazy.force Writer.stdout in
    [%log.info logger "PRELOAD"] ;
    let op_stream =
      Pipe.unfold ~init:() ~f:(fun () ->
          match%bind recv in_pipe with
          | Ok (Finalise {msg}) ->
              [%log.debug logger "Finalise recv" (msg : string)] ;
              return None
          | Ok (Start _) ->
              failwith "Got start during preload"
          | Ok (Op op) ->
              Deferred.Option.return (op, ())
          | Error i ->
              [%message
                "EOF while reading" ~remaining:(i : int * string option)]
              |> Sexp.to_string_hum |> failwith )
    in
    let%bind op_list =
      Pipe.fold op_stream ~init:[] ~f:(fun ops v ->
          match v with
          | MT.{prereq= true; _} ->
              let%bind _res = perform v.op_type client (Time.now ()) clientid in
              return ops
          | _ ->
              v :: ops |> return )
    in
    let op_list = List.rev op_list in
    [%log.info logger "READYING"] ;
    let%bind () = send (Bytes.create 0) ~flush:true result_pipe in
    [%log.info logger "READIED"] ;
    let%bind _got_start =
      match%bind recv in_pipe with
      | Ok (Start {msg}) ->
          [%log.debug logger "Starting" (msg : string)] ;
          Deferred.unit
      | Error i ->
          [%message "EOF while reading" ~remaining:(i : int * string option)]
          |> Sexp.to_string_hum |> failwith
      | s ->
          [%message
            "Got unexpected message"
              ~msg:(s : (request, int * string option) Result.t)]
          |> Sexp.to_string_hum |> failwith
    in
    [%log.info logger "EXECUTE"] ;
    let start_time = Time.now () in
    let fold_op_list ops MT.{prereq= _; start; op_type= op} =
      let%bind () = Time.(add start_time (Span.of_sec start)) |> at in
      let res = perform op client (Time.now ()) clientid in
      res :: ops |> return
    in
    let%bind results = Deferred.List.fold ~init:[] ~f:fold_op_list op_list in
    let%bind results = Deferred.List.all results in
    [%log.debug logger "RESULTS"] ;
    let%bind () = result_loop results result_pipe in
    [%log.debug logger "EXIT"] ; Writer.close result_pipe
end
