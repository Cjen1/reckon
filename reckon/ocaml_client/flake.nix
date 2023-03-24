{
  inputs = {
    flake-utils.url = "github:numtide/flake-utils";
    nixpkgs.follows = "opam-nix/nixpkgs";
    opam-repository = {
      url = "github:ocaml/opam-repository/562afb69b736d0b96a88588228dd55ae9cfefe60";
      flake = false;
    };
    opam-nix = {
      url = "github:tweag/opam-nix";
      inputs.opam-repository.follows = "opam-repository";
    };
  };
  outputs = { self, flake-utils, opam-nix, nixpkgs, opam-repository}:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
        on = opam-nix.lib.${system};
        devPackagesQuery = {
          ocaml-lsp-server = "*";
          ocamlformat = "*";
          utop = "*";
        };
        query = devPackagesQuery // {
          ocaml-base-compiler = "5.0.0";
        };
        scope = on.buildDuneProject { } "reckon-shim" ./. query;
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
