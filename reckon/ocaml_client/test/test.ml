open Reckon_shim
open Reckon_shim.Types

module Cli = struct
  type mgr = (rid * op) Eio.Stream.t

  let submit t v = Eio.Stream.add t v; Eio.Fiber.yield ()

  let create ~sw ~env ~f:(callback : recv_callback) ~urls:_ ~id:_ =
    let mgr = Eio.Stream.create Int.max_int in
    Eio.Fiber.fork_daemon ~sw (fun () ->
        while true do
          let rid, op = Eio.Stream.take mgr in
          Eio.Fiber.fork ~sw (fun () ->
            let res =
              match op with
              | Write _ ->
                  Success
              | Read _ ->
                  Failure (`Msg "TEST FAILURE")
            in
            Eio.Time.sleep env#clock 1.;
            callback (rid, res)
          );
        done ;
        Eio.Fiber.await_cancel () ) ;
    mgr
end

module T = Make (Cli)

(*
type s = {mutable foo: int; idx: int}

let () =
  let arr = Array.init 3 (fun idx -> {foo= -1; idx}) in
  let pp ppf s = Fmt.pf ppf "{foo=%d; idx=%d}" s.foo s.idx in
  Fmt.pr "Init array: %a" Fmt.(array ~sep:(const string ", ") pp) arr ;
  Eio_main.run
  @@ fun _ ->
  Eio.Switch.run
  @@ fun sw ->
  Eio.Fiber.fork ~sw (fun () -> Array.iteri (fun i s -> s.foo <- i) arr) ;
  Fmt.pr "Final array: %a" Fmt.(array ~sep:(const string ", ") pp) arr
  *)

let () = exit @@ Cmdliner.Cmd.eval T.cmd
