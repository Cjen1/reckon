open Eio.Std
open Types
open Accessor.O
open StdLabels
open Io
module Types = Types

let dtraceln fmt =
  let ignore_format = Format.ikfprintf ignore Fmt.stderr in
  if true then Eio.traceln fmt else ignore_format fmt

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
    ; mutable recv_prereq_hwm: int
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
      t.req_state.@(nth rid @> ReqState.t_result) <- Eio.Time.now clock ;
      t.req_state.@(nth rid @> ReqState.result) <- res ) ;
    t.recv_prereq_hwm <- max t.recv_prereq_hwm rid ;
    Eio.Condition.broadcast t.recv

  let retry_prereq t clock mgr rid op =
    dtraceln "Got prereq" ;
    Cli.submit mgr (rid, op) ;
    while rid > t.recv_prereq_hwm do
      (* Wait for response or timeout *)
      Eio.Fiber.first
        (fun () -> Eio.Condition.await_no_mutex t.recv)
        (fun () ->
          Eio.Time.sleep clock 0.1 ;
          Cli.submit mgr (rid, op) )
    done

  let preload reqsQ stdin mgr t clock =
    (* Giving Int30.max_int -> Int31.max_int*)
    let trid = ref @@ (Int32.(to_int max_int) / 4) in
    traceln "Phase 1: Preload" ;
    (* At most one prereq outstanding at a time
       => Can use a high water mark for trid to check for response
    *)
    let rec aux () =
      match I.recv_msg stdin with
      | Preload {prereq= true; op; _} ->
          let lrid = !trid in
          trid := !trid + 1 ;
          retry_prereq t clock mgr lrid op ;
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

  let readying stdout stdin =
    traceln "Phase 2: Readying" ;
    O.send stdout Ready ;
    match I.recv_msg stdin with
    | Start ->
        traceln "Got start"
    | m ->
        Fmt.failwith "Unexpected msg: %a" pp_msg m

  let execute state mgr clock start_time =
    traceln "Phase 3: Execute" ;
    traceln "execute uses %s" state.version ;
    (* For each request try to submit it *)
    let maybe_yield =
      let te = 100 in
      let e = ref te in
      fun () ->
        if !e <= 0 then (
          e := te ;
          Eio.Fiber.yield () ) ;
        e := !e - 1
    in
    Array.iteri state.req_state ~f:(fun rid {op; aim_submit; _} ->
        let t_curr = Eio.Time.now clock in
        let aim_submit = start_time +. aim_submit in
        if t_curr < aim_submit then Eio.Time.sleep_until clock aim_submit ;
        Cli.submit mgr (rid, op) ;
        traceln "Updating %d" rid ;
        state.req_state.@(nth rid @> ReqState.t_submitted) <- Eio.Time.now clock ;
        maybe_yield () )

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
      ; recv_prereq_hwm= 0
      ; version= "Init" }
    in
    let mgr =
      Cli.create ~sw ~env
        ~f:(catcher_iter (Eio.Stdenv.clock env) state)
        ~urls ~id:cid
    in
    (* Get stdin/stdout *)
    Eio.Buf_write.with_flow (Eio.Stdenv.stdout env)
    @@ fun stdout ->
    let stdin = Eio.Stdenv.stdin env |> Eio.Buf_read.of_flow ~max_size:4096 in
    let reqs = Queue.create () in
    (* fill reqs and apply initial requests synchronously *)
    preload reqs stdin mgr state env#clock ;
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
    readying stdout stdin ;
    (* Submit requests *)
    execute state mgr (Eio.Stdenv.clock env) (Eio.Time.now env#clock) ;
    (* Collate *)
    Eio.Time.sleep (Eio.Stdenv.clock env) 1. ;
    collate state cid stdout ;
    traceln "Finished execution" ;
    Eio.Buf_write.flush stdout ;
    exit 0

  let cmd = Command_line.cmd run
end
