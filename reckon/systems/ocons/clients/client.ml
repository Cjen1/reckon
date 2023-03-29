open! Eio.Std
module O = Ocons_core
open Reckon_shim
let () = Ocons_conn_mgr.set_debug_flag ()

module Ocons_cli_shim : Types.S = struct
  type mgr = {cmgr: O.Client.cmgr; callback: Types.recv_callback}

  let submit (t : mgr) (rid, op) =
    let op =
      match op with
      | Types.Write (k, v) ->
          O.Types.Write (k, v)
      | Types.Read k ->
          O.Types.Read k
    in
    try
      let cmd =
        O.Types.Command.
          {op; id= rid; trace_start= Mtime.of_uint64_ns Int64.min_int}
      in
      traceln "Submitting request %d" rid;
      O.Client.submit_request t.cmgr cmd
    with e when O.Utils.is_not_cancel e -> t.callback (rid, Failure (`Error e))

  let create ~sw ~(env : Eio.Stdenv.t) ~(f : Types.recv_callback) ~urls ~id =
    let con_ress =
      urls
      |> List.mapi (fun idx addr ->
             ( idx
             , fun sw -> (Eio.Net.connect ~sw env#net addr :> Eio.Flow.two_way)
             ) )
    in
    let recv_callback ((_, (rid, res, _)) : _ * O.Client.response) =
      traceln "got result for %d" rid;
      let res =
        match res with
        | O.Types.Failure msg ->
            Types.Failure (`Msg msg)
        | O.Types.(Success | ReadSuccess _) ->
            Types.Success
      in
      f (rid, res)
    in
    let cmgr =
      O.Client.create_cmgr ~kind:(Ocons_conn_mgr.Iter recv_callback) ~sw
        con_ress id (fun () -> Eio.Time.sleep env#clock 1.)
    in
    Eio.Time.sleep env#clock 1.;
    {cmgr; callback= f}
end

module T = Make (Ocons_cli_shim)

let () = exit @@ Cmdliner.Cmd.eval T.cmd
