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
    ocons-src = {
      url = "github:cjen1/ocons";
      #url = "./../ocons-src";
      flake = false;
    };
  };
  outputs = { self, flake-utils, opam-nix, nixpkgs, opam-repository, ocons-src}:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
        on = opam-nix.lib.${system};
        devPackagesQuery = {
          ocaml-lsp-server = "*";
          ocamlformat = "*";
          utop = "*";
        };
        reckon-shim-src = ./../../../ocaml_client;
        query = devPackagesQuery // {
          ocaml-base-compiler = "5.0.0";
        };
        repos = [
          (on.makeOpamRepo ocons-src)
          (on.makeOpamRepo reckon-shim-src)
          on.opamRepository
        ];
        scope = on.buildDuneProject { inherit repos; } "reckon-ocons" ./. query;
        devPackages = builtins.attrValues
          (pkgs.lib.getAttrs (builtins.attrNames query) scope);
      in
      {
        defaultPackage = scope.reckon-ocons;
        devShell = pkgs.mkShell {
          inputsFrom = [scope.reckon-ocons];
          buildInputs = devPackages ++ [
          ];
        };
      });
}
