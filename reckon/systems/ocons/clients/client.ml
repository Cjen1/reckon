open! Eio.Std
module O = Ocons_core
open Reckon_shim
(*let () = Ocons_conn_mgr.set_debug_flag ()*)

module Ocons_cli_shim : Types.S = struct
  type mgr =
    { cmgr: O.Client.cmgr
    ; clock: float Eio.Time.clock_ty Eio.Time.clock
    ; callback: Types.recv_callback }

  let submit_rate, run_sr = O.Utils.InternalReporter.rate_reporter "submit_rate"

  let submit (t : mgr) (rid, op) =
    run_sr := true ;
    submit_rate () ;
    let op =
      match op with
      | Types.Write (k, v) ->
          O.Types.Write (k, v)
      | Types.Read k ->
          O.Types.Read k
    in
    try
      let cmd =
        O.Types.Command.{op; id= rid; trace_start= Eio.Time.now t.clock}
      in
      dtraceln "Submitting request %d" rid ;
      O.Client.submit_request t.cmgr cmd
    with e when O.Utils.is_not_cancel e -> t.callback (rid, Failure (`Error e))

  let create ~sw ~(env : Eio_unix.Stdenv.base) ~(f : Types.recv_callback) ~urls
      ~id =
    O.Utils.InternalReporter.run ~sw env#clock 1. ;
    let create_conn addr sw =
      let c = Eio.Net.connect ~sw env#net addr in
      O.Utils.set_nodelay c ; c
    in
    let con_ress =
      urls
      |> List.mapi (fun idx addr ->
             (idx, (create_conn addr :> O.Client.Cmgr.resolver)) )
    in
    let recv_callback ((_, (rid, res, trace)) : _ * O.Client.response) =
      O.Utils.TRACE.ex_cli trace ;
      let res =
        match res with
        | O.Types.Failure msg ->
            Types.Failure (`Msg msg)
        | O.Types.(Success | ReadSuccess _) ->
            Types.Success
      in
      f (rid, res)
    in
    let cmgr, r = Promise.create () in
    Fiber.fork ~sw (fun () ->
        try
          Eio.Switch.run
          @@ fun sw ->
          let cmgr =
            O.Client.create_cmgr (*~use_domain:env#domain_mgr*)
              ~kind:(Ocons_conn_mgr.Iter recv_callback) ~sw con_ress id
              (fun () -> Eio.Time.sleep env#clock 1.)
          in
          Promise.resolve r cmgr
        with e ->
          Eio.traceln "Error while receiving: %a" Fmt.exn_backtrace
            (e, Printexc.get_raw_backtrace ()) ) ;
    let cmgr = Promise.await cmgr in
    {cmgr; callback= f; clock= (env#clock)}

  let flush (t : mgr) =
    if false then Ocons_conn_mgr.flush_all t.cmgr else Fiber.yield ()
end

module T = Make (Ocons_cli_shim)

let () = exit @@ Cmdliner.Cmd.eval T.cmd
