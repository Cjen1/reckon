{
  inputs = {
    flake-utils.url = "github:numtide/flake-utils";
    opam-nix = {
      url = "github:tweag/opam-nix";
      inputs.opam-repository.follows = "opam-repository";
    };
    ocons-src.url = "github:cjen1/ocons";
    opam-repository.follows = "ocons-src/opam-repository";
  };
  outputs = { self, flake-utils, opam-nix, nixpkgs, opam-repository, ocons-src}:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
        on = opam-nix.lib.${system};
        devPackagesQuery = {
          ocaml-lsp-server = "*";
          ocamlformat = "0.25.1";
          utop = "*";
        };
        reckon-shim-src = ./../../../ocaml_client;
        query = devPackagesQuery // {
          ocaml-base-compiler = "5.1.0";
          ocamlfind = "1.9.5";
        };
        repos = [
          (on.makeOpamRepo ocons-src)
          (on.makeOpamRepo reckon-shim-src)
          opam-repository
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
