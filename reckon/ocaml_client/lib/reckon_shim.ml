open Eio.Std
open Types
open Io
module Types = Types

let dtraceln fmt =
  let ignore_format = Format.ikfprintf ignore Fmt.stderr in
  if false then Eio.traceln fmt else ignore_format fmt

let is_not_cancel = function Eio.Cancel.Cancelled _ -> false | _ -> true

module Make (Cli : S) =
(*: sig
    val run : url list -> rid -> unit

    val cmd : unit Cmdliner.Cmd.t
  end *)
struct
  open Core

  type operation_state = {op: op; t_submitted: float}

  type result_state = {t_result: float; result: res}

  type t =
    { op_id_gen: unit -> int
    ; prereqs: (unit Promise.t * unit Promise.u) Hashtbl.M(Int).t
    ; operations: operation_state Hashtbl.M(Int).t
    ; results: result_state Hashtbl.M(Int).t }

  let catcher_callback clock t stop_reqs : recv_callback =
   fun (rid, res) ->
    dtraceln "Got result for %d" rid ;
    (* Set if not prereq *)
    match Hashtbl.find t.prereqs rid with
    | _ when Eio.Promise.is_resolved stop_reqs ->
        ()
    | Some (p, r) when not (Promise.is_resolved p) ->
        Promise.resolve r ()
    | _ when Hashtbl.mem t.operations rid && not (Hashtbl.mem t.results rid) ->
        Hashtbl.add_exn t.results ~key:rid
          ~data:{result= res; t_result= Eio.Time.now clock}
    | _ ->
        ()

  let retry_prereq t ((rid, op) as req : int * Types.op) clock mgr =
    dtraceln "Got prereq" ;
    let p, r = Promise.create () in
    Hashtbl.set t.prereqs ~key:rid ~data:(p, r) ;
    Cli.submit mgr req ;
    while not (Promise.is_resolved p) do
      (* Wait for response or timeout *)
      Eio.Fiber.first
        (fun () -> Promise.await p)
        (fun () ->
          Eio.Time.sleep clock 1. ;
          Cli.submit mgr (rid, op) )
    done

  let preload stdin clock t mgr =
    let req_q = Queue.create () in
    let rec aux () =
      match I.recv_msg stdin with
      | Preload {prereq= true; op; _} ->
          let req = (t.op_id_gen (), op) in
          retry_prereq t req clock mgr ;
          aux ()
      | Preload s ->
          dtraceln "Got op" ;
          Queue.enqueue req_q (s.op, s.aim_submit) ;
          aux ()
      | Finalise ->
          dtraceln "Got finalise" ; ()
      | m ->
          traceln "Unexpected msg: %a" pp_msg m ;
          exit 0
    in
    aux () ; Queue.to_array req_q

  let readying stdout stdin =
    traceln "Phase 2: Readying" ;
    O.send stdout Ready ;
    match I.recv_msg stdin with
    | Start ->
        dtraceln "Got start"
    | m ->
        Fmt.failwith "Unexpected msg: %a" pp_msg m

  let execute t mgr clock start_time (reqs : (op * float) Array.t) =
    traceln "Phase 3: Execute" ;
    let if_before t f =
      let open Float in
      if Eio.Time.now clock < t then f ()
    in
    Array.sort reqs ~compare:(fun (_, a) (_, b) -> Float.compare a b) ;
    Array.iter reqs ~f:(fun (op, target) ->
        let rid = t.op_id_gen () in
        try
          let aim_submit = start_time +. target in
          if_before aim_submit (fun () -> Cli.flush mgr) ;
          if_before aim_submit (fun () -> Eio.Time.sleep_until clock aim_submit) ;
          Hashtbl.add_exn t.operations ~key:rid
            ~data:{op; t_submitted= Eio.Time.now clock} ;
          Cli.submit mgr (rid, op)
        with e when is_not_cancel e ->
          Eio.traceln "Raised error while submitting %d %a" rid
            Fmt.exn_backtrace
            (e, Stdlib.Printexc.get_raw_backtrace ()) ) ;
    Eio.traceln "DONE EXECUTE"

  let collate t cid stdout =
    traceln "Phase 5: Collate" ;
    t.results |> Hashtbl.keys
    |> List.sort ~compare:Int.compare
    |> List.iter ~f:(fun rid ->
           match
             (Hashtbl.find t.results rid, Hashtbl.find t.operations rid)
           with
           | Some {t_result; result}, Some {op; t_submitted} ->
               O.send stdout (Result {op; t_submitted; t_result; result; cid})
           | _ ->
               () ) ;
    Eio.Buf_write.flush stdout

  let finalise stdout =
    traceln "Phase 5: finalise" ;
    O.send stdout Finished

  let run urls cid =
    traceln "Starting cid=%d attached to %a" cid
      (Fmt.list Eio.Net.Sockaddr.pp)
      urls ;
    let ( let* ) k f = k f in
    let* env = Eio_main.run in
    let* sw = Switch.run in
    let clock = Eio.Stdenv.clock env in
    let op_id_gen =
      let open Int in
      let x = ref 1 in
      fun () ->
        let x' = !x in
        Int.incr x;
        Int.shift_left x' 6 + cid
    in
    let state =
      { op_id_gen= op_id_gen
      ; prereqs= Hashtbl.create (module Int)
      ; operations= Hashtbl.create (module Int)
      ; results= Hashtbl.create (module Int) }
    in
    let stop_barrier_p, stop_barrier_u = Promise.create () in
    let mgr =
      Cli.create ~sw ~env
        ~f:(catcher_callback clock state stop_barrier_p)
        ~urls ~id:cid
    in
    let stdin = Eio.Stdenv.stdin env |> Eio.Buf_read.of_flow ~max_size:4096 in
    Eio.Buf_write.with_flow (Eio.Stdenv.stdout env) (fun stdout ->
        let reqs = preload stdin clock state mgr in
        readying stdout stdin ;
        execute state mgr clock (Eio.Time.now clock) reqs ;
        Eio.Time.sleep clock 5. ;
        Promise.resolve stop_barrier_u () ;
        collate state cid stdout ;
        finalise stdout ;
        Eio.Buf_write.flush stdout ;
        Stdlib.Out_channel.flush_all ();
        traceln "Phase 6: exit" ) ;
    exit 0

  let cmd = Command_line.cmd run
end
