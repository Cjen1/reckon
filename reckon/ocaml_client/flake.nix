{
  inputs = {
    opam-nix.url = "github:tweag/opam-nix";
    flake-utils.url = "github:numtide/flake-utils";
    nixpkgs.follows = "opam-nix/nixpkgs";
  };
  outputs = { self, flake-utils, opam-nix, nixpkgs }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
        on = opam-nix.lib.${system};
        devPackagesQuery = {
          ocaml-lsp-server = "*";
          ocamlformat = "*";
          utop = "*";


          bigstringaf = "*";
          cstruct = "*";
          lwt-dllist = "*";
          optint = "*";
          psq = "*";
          fmt = "*";
          hmap = "*";
          mtime = "*";
          uring = "*";
          logs = "*";
          luv_unix = "*";
        };
        query = devPackagesQuery // {
          ocaml-base-compiler = "5.0.0";
        };
        scope = on.buildDuneProject {} "reckon-shim" ./. query;
        devPackages = builtins.attrValues
          (pkgs.lib.getAttrs (builtins.attrNames query) scope);
      in
      {
        defaultPackage = pkgs.hello;
        devShell = pkgs.mkShell {
          inputsFrom = [scope.reckon-shim];
          buildInputs = devPackages ++ [
          ];
        };
      });
}
