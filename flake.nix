{
  description = "pwn.college challenges dev env";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-25.11";
  };

  outputs =
    { self, nixpkgs }:
    let
      lib = nixpkgs.lib;
      systems = [ "x86_64-linux" "aarch64-linux" ];
      forAllSystems = f: lib.genAttrs systems (system: f system);
    in
    {
      devShells = forAllSystems (system:
        let
          pkgs = import nixpkgs { inherit system; };
          runtimePkgs = {
            "pwn-challenge-runtime" = import ./runtime { inherit pkgs lib; };
          };
          pwnshop = pkgs.writeShellApplication {
            name = "pwnshop";
            runtimeInputs = with pkgs; [
              git
              uv
            ];
            text = ''
              set -euo pipefail
              root="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
              exec "$root/pwnshop" "$@"
            '';
          };
        in
        {
          default = pkgs.mkShell {
            packages = with pkgs; [
              docker
              git
              git-crypt
              runtimePkgs."pwn-challenge-runtime"
              pwnshop
              uv
            ];
            shellHook = ''
              export DOCKER_HOST="$(sudo ${runtimePkgs."pwn-challenge-runtime"}/bin/pwn-challenge-runtime)"
            '';
          };
        });
    };
}
