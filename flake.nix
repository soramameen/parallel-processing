{
  description = "Python project with uv";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
        python = pkgs.python312;
      in
      {
        devShells.default = pkgs.mkShell {
          packages = [
            python
            pkgs.uv
          ];

          shellHook = ''
            export UV_PYTHON="${python}/bin/python"
            echo "=================================================="
            echo "  Python: $(python --version)"
            echo "  uv: $(uv --version)"
            echo "=================================================="
          '';
        };
      });
}
