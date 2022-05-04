{
  inputs = {
    nixpkgs.url = "github:nixos/nixpkgs";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let pkgs = nixpkgs.legacyPackages.${system};
          jdk_ = pkgs.jdk11;
          gradle_ = pkgs.gradle_7.override {
            java = jdk_;
          };
      in {
        devShell = pkgs.mkShell {
          buildInputs = [
            jdk_
            gradle_
          ];
        };
      });
}
