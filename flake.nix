{
  description = "pwn.college challenges dev env";

  nixConfig = {
    extra-substituters = [ "https://nix-cache.challenges.pwn.college" ];
    extra-trusted-public-keys = [
      "nix-cache.challenges.pwn.college-1:Qj32MyanSS2fW+W7MtEFN3fWSksMT8l6IyJuG9Lw5bc="
    ];
  };

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-25.11";
  };

  outputs =
    { self, nixpkgs }:
    let
      lib = nixpkgs.lib;
      systems = [ "x86_64-linux" ];
      forAllSystems = f: lib.genAttrs systems (system: f system);
    in
    {
      formatter = forAllSystems (
        system:
        let
          pkgs = import nixpkgs { inherit system; };
        in
        pkgs.writeShellApplication {
          name = "fmt";
          runtimeInputs = [
            pkgs.nixfmt-rfc-style
            pkgs.ruff
            pkgs.treefmt
          ];
          text = ''
            set -euo pipefail
            exec treefmt "$@"
          '';
        }
      );

      devShells = forAllSystems (
        system:
        let
          pkgs = import nixpkgs { inherit system; };

          pwn-challenge-runtime = import ./runtime { inherit pkgs lib; };

          pwnshop = pkgs.writeShellApplication {
            name = "pwnshop";
            runtimeInputs = with pkgs; [
              clang-tools
              git
              uv
            ];
            text = ''
              set -euo pipefail
              root="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
              # On NixOS, the PyPI clang-format wheel's embedded binary generally can't run
              # (dynamic linker), so force the Nix-provided clang-format.
              export PWN_CLANG_FORMAT='${pkgs.clang-tools}/bin/clang-format'
              exec "$root/pwnshop" "$@"
            '';
          };
        in
        {
          default = pkgs.mkShell {
            packages = with pkgs; [
              clang-tools
              docker
              git
              git-crypt
              pwn-challenge-runtime
              pwnshop
              uv
            ];
            shellHook = ''
              export DOCKER_HOST="$(sudo ${pwn-challenge-runtime}/bin/pwn-challenge-runtime)"
              # Ensure pwnshop uses a working clang-format under Nix (uv's wheel binary won't).
              export PWN_CLANG_FORMAT='${pkgs.clang-tools}/bin/clang-format'
            '';
          };
        }
      );
    };
}
