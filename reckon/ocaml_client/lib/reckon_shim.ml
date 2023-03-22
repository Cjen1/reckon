open Eio.Std
open Types
open Accessor.O
open StdLabels
open Io
module Types = Types

let dtraceln fmt =
  let ignore_format = Format.ikfprintf ignore Fmt.stderr in
  if false then Eio.traceln fmt else ignore_format fmt

module Make (Cli : S) : sig
  val run : url list -> rid -> unit

  val cmd : unit Cmdliner.Cmd.t
end = struct
  type req_state =
    { op: op
    ; aim_submit: float
    ; mutable t_submitted: float
    ; mutable result: res
    ; mutable t_result: float }
  [@@deriving accessors ~submodule:ReqState]

  type t =
    { recv: Eio.Condition.t
    ; mutable recv_prereq_count: int
    ; mutable req_state: req_state array
    ; mutable should_record_result: bool
    ; mutable version: string }

  let nth n =
    [%accessor
      Accessor.field
        ~get:(fun arr -> Array.get arr n)
        ~set:(fun arr x -> Array.set arr n x)]

  let catcher_iter (clock : #Eio.Time.clock) t : recv_callback =
   fun (rid, res) ->
    traceln "Got result for %d" rid ;
    if rid < Array.length t.req_state && t.should_record_result then (
      traceln "Using version %s" t.version ;
      t.req_state.@(nth rid @> ReqState.t_result) <- Eio.Time.now clock ;
      t.req_state.@(nth rid @> ReqState.result) <- res ) ;
    t.recv_prereq_count <- t.recv_prereq_count + 1 ;
    Eio.Condition.broadcast t.recv

  let preload reqsQ stdin mgr t =
    let trid = ref @@ (Int32.(to_int max_int) / 2) in
    traceln "Phase 1: Preload" ;
    let rec aux () =
      match I.recv_msg stdin with
      | Preload {prereq= true; op; _} ->
          dtraceln "Got prereq" ;
          let prereq_count = t.recv_prereq_count in
          Cli.submit mgr (!trid, op) ;
          trid := !trid - 1 ;
          (* Wait for response *)
          while prereq_count + 1 > t.recv_prereq_count do
            Eio.Condition.await_no_mutex t.recv
          done ;
          aux ()
      | Preload s ->
          dtraceln "Got op" ;
          Queue.add (s.op, s.aim_submit) reqsQ ;
          aux ()
      | Finalise ->
          dtraceln "Got finalise" ; ()
      | m ->
          Fmt.failwith "Unexpected msg: %a" pp_msg m
    in
    aux ()

  let readying stdout =
    traceln "Phase 2: Readying" ;
    O.send stdout Ready

  let execute state mgr clock =
    traceln "Phase 3: Execute" ;
    traceln "execute uses %s" state.version ;
    (* For each request try to submit it *)
    Array.iteri state.req_state ~f:(fun rid {op; aim_submit; _} ->
        let t_curr = Eio.Time.now clock in
        if t_curr < aim_submit then Eio.Time.sleep_until clock aim_submit ;
        Cli.submit mgr (rid, op) ;
        traceln "Updating %d" rid ;
        state.req_state.@(nth rid @> ReqState.t_submitted) <- Eio.Time.now clock )

  let collate state cid stdout =
    traceln "Phase 4: Collate" ;
    (* Iterate through results and return them to the coordinator *)
    state.should_record_result <- false ;
    Array.iter state.req_state ~f:(fun {op; t_submitted; t_result; result; _} ->
        O.send stdout (Result {op; t_submitted; t_result; result; cid}) ) ;
    O.send stdout Finished

  let run urls cid =
    Eio_main.run
    @@ fun env ->
    Switch.run
    @@ fun sw ->
    (* Set up state *)
    let null_time = -1. in
    let state =
      { req_state= Array.init 0 ~f:(fun _ -> assert false)
      ; should_record_result= true
      ; recv= Eio.Condition.create ()
      ; recv_prereq_count= 0
      ; version= "Init" }
    in
    let mgr =
      Cli.create ~sw
        ~f:(catcher_iter (Eio.Stdenv.clock env) state)
        ~urls ~id:cid
    in
    (* Get stdin/stdout *)
    Eio.Buf_write.with_flow (Eio.Stdenv.stdout env)
    @@ fun stdout ->
    let stdin = Eio.Stdenv.stdin env |> Eio.Buf_read.of_flow ~max_size:4096 in
    let reqs = Queue.create () in
    (* fill reqs and apply initial requests synchronously *)
    preload reqs stdin mgr state ;
    let req_state =
      reqs |> Queue.to_seq
      |> Seq.map (fun (op, aim_submit) ->
             { op
             ; aim_submit
             ; t_submitted= null_time
             ; result= Failure (`Msg "Not yet recv'd response")
             ; t_result= null_time } )
      |> Array.of_seq
    in
    state.req_state <- req_state ;
    Array.sort
      ~cmp:(fun a b -> Float.compare a.aim_submit b.aim_submit)
      state.req_state ;
    state.version <- "execute" ;
    (* Notify ready*)
    readying stdout ;
    (* Submit requests *)
    execute state mgr (Eio.Stdenv.clock env) ;
    (* Collate *)
    Eio.Time.sleep (Eio.Stdenv.clock env) 1. ;
    collate state cid stdout ;
    traceln "Finished execution"

  let cmd = Command_line.cmd run
end
