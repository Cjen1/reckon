open Types
open StdLabels

type input_message =
  | Preload of {prereq: bool; op: op; aim_submit: float}
  | Finalise
  | Start

let pp_msg : input_message Fmt.t =
 fun ppf msg ->
  match msg with
  | Preload _ ->
      Fmt.pf ppf "Preload"
  | Finalise ->
      Fmt.pf ppf "Finalise"
  | Start ->
      Fmt.pf ppf "Start"

let is_preload = function Preload _ -> true | _ -> false

let is_finalise = function Finalise -> true | _ -> false

let is_start = function Start -> true | _ -> false

type output_message =
  | Ready
  | Result of
      {op: op; t_submitted: float; t_result: float; result: res; cid: int}
  | Finished

module O = struct
  open Eio.Buf_write

  let out_msg_to_json : output_message -> Yojson.Basic.t = function
    | Ready ->
        `Assoc [("kind", `String "ready")]
    | Finished ->
        `Assoc [("kind", `String "finished")]
    | Result s ->
        let op_kind = match s.op with Write _ -> "write" | Read _ -> "read" in
        let result =
          match s.result with
          | Success ->
              "Success"
          | Failure (`Error e) ->
              Fmt.str "Failure exception: %a" Fmt.exn e
          | Failure (`Msg s) ->
              Fmt.str "Failure msg: %s" s
        in
        `Assoc
          [ ("kind", `String "result")
          ; ("clientid", `String (Int.to_string s.cid))
          ; ("op_kind", `String op_kind)
          ; ("result", `String result)
          ; ("t_submitted", `Float s.t_submitted)
          ; ("t_result", `Float s.t_result) ]

  let send out msg =
    let json = out_msg_to_json msg in
    let str = Yojson.Basic.to_string json in
    LE.uint32 out (String.length str |> Int32.of_int) ;
    string out str
end

module I = struct
  open Eio.Buf_read
  open Eio.Buf_read.Syntax

  let recv =
    let buf = Buffer.create 4096 in
    let* len = Eio.Buf_read.LE.uint32 in
    let* str = Eio.Buf_read.take (len |> Int32.to_int) in
    return (Yojson.Basic.from_string ~buf str)

  let parse_operation json =
    let open Yojson.Basic.Util in
    match json |> member "kind" with
    | `String "write" ->
        Write
          ( json |> member "key" |> to_string
          , json |> member "value" |> to_string )
    | `String "read" ->
        Read (json |> member "key" |> to_string)
    | _ ->
        Fmt.failwith "Incorrect operation kind:%a%a" Fmt.cut () Yojson.Basic.pp
          json

  let parse_preload json =
    let open Yojson.Basic.Util in
    let prereq = json |> member "prereq" |> to_bool in
    let op =
      json |> member "operation" |> member "payload" |> parse_operation
    in
    let aim_submit = json |> member "operation" |> member "time" |> to_float in
    Preload {prereq; op; aim_submit}

  let recv_msg =
    let open Eio.Buf_read.Syntax in
    let+ json = recv in
    let open Yojson.Basic.Util in
    match json |> member "kind" with
    | `String "preload" ->
        parse_preload json
    | `String "finalise" ->
        Finalise
    | `String "start" ->
        Start
    | _ ->
        Fmt.failwith "Incorrect msg kind: %a%a" Fmt.cut () Yojson.Basic.pp json
end
