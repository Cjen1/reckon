{
  description = "";

  inputs = {
    flake-utils.url = "github:numtide/flake-utils";
    nixpkgs.url = "github:NixOS/nixpkgs";
    mach-nix.url = "github:DavHau/mach-nix";
  };

  outputs = { self, nixpkgs, flake-utils, mach-nix }:
  flake-utils.lib.eachDefaultSystem (system:
  let 
    pkgs = nixpkgs.legacyPackages.${system};
    machNix = mach-nix.lib."${system}";
    mypython = machNix.mkPython {
      requirements = ''
        numpy
        metaflow
        pandas
        parsec
        black
        dpkt
        seaborn
        plotnine
        pythonflow
      '';
    };
  in {
    devShell = pkgs.mkShell {
      buildInputs = with pkgs; [
        mypython
      ];
    };
  });
}
