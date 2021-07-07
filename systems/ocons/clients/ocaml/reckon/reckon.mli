open! Core
open! Async

val logger : Async_unix.Log.t

module type Client = sig
  type t

  val put : t -> bytes -> bytes -> (unit, string) Deferred.Result.t

  val get : t -> bytes -> (bytes, string) Deferred.Result.t
end

module Make (Cli : Client) : sig
  type client = Cli.t

  val run : client -> int32 -> unit Deferred.t
end
