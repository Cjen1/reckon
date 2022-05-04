{
  inputs = {
    nixpkgs.url = "github:nixos/nixpkgs";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let pkgs = nixpkgs.legacyPackages.${system};
          gradle_ = pkgs.gradle_7.override {
            java = pkgs.jdk11;
          };
      in {
        devShells.default = pkgs.mkShell {
          buildInputs = with pkgs; [
            jdk11
            gradle_
          ];
        };
      });
}
