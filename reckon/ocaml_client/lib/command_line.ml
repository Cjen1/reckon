open Cmdliner
open Types

let ipv4 =
  let conv = Arg.(t4 ~sep:'.' int int int int) in
  let parse s =
    let ( let+ ) = Result.bind in
    let+ res = Arg.conv_parser conv s in
    let check v = v >= 0 && v < 256 in
    match res with
    | v0, v1, v2, v3 when check v0 && check v1 && check v2 && check v3 ->
        let raw = Bytes.create 4 in
        Bytes.set_uint8 raw 0 v0 ;
        Bytes.set_uint8 raw 1 v1 ;
        Bytes.set_uint8 raw 2 v2 ;
        Bytes.set_uint8 raw 3 v3 ;
        Ok (Eio.Net.Ipaddr.of_raw (Bytes.to_string raw))
    | v0, v1, v2, v3 ->
        Error
          (`Msg
            Fmt.(
              str "Invalid IP address: %a"
                (list ~sep:(const string ".") int)
                [v0; v1; v2; v3] ) )
  in
  Arg.conv ~docv:"IPv4" (parse, Eio.Net.Ipaddr.pp)

let sockv4 =
  let conv = Arg.(pair ~sep:':' ipv4 int) in
  let parse s =
    let ( let+ ) = Result.bind in
    let+ ip, port = Arg.conv_parser conv s in
    Ok (`Tcp (ip, port) : Eio.Net.Sockaddr.stream)
  in
  Arg.conv ~docv:"TCP" (parse, Eio.Net.Sockaddr.pp)

let cmd (run : url list -> rid -> unit) =
  let info = Cmd.info "bench" in
  let id_t =
    Arg.(
      required
      & pos 0 (some int) None (info ~docv:"ID" ~doc:"The id of the client" []) )
  in
  let sockaddrs_t =
    Arg.(
      required
      & pos 1
          (some @@ list sockv4)
          None
          (info ~docv:"SOCKADDRS"
             ~doc:
               "This is a comma separated list of ip addresses and ports eg: \
                \"192.168.0.1:5000,192.168.0.2:5000\""
             [] ) )
  in
  Cmd.v info Term.(const run $ sockaddrs_t $ id_t)
