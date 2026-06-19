{
  description = "pwn.college challenges dev env";

  nixConfig = {
    extra-substituters = [ "https://nix-cache.challenges.pwn.college" ];
    extra-trusted-public-keys = [
      "nix-cache.challenges.pwn.college-1:Qj32MyanSS2fW+W7MtEFN3fWSksMT8l6IyJuG9Lw5bc="
    ];
  };

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-26.05";
  };

  outputs =
    {
      self,
      nixpkgs,
    }:
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

      packages = forAllSystems (
        system:
        let
          pkgs = import nixpkgs { inherit system; };

          pwn-workspace-runtime = import ./runtime/workspace { inherit pkgs; };
          pwn-platform-runtime = import ./runtime/platform { inherit pkgs lib; };

          pwnshop = import ./tools/pwnshop { inherit pkgs pwn-workspace-runtime; };
          discord-feedback = import ./tools/feedback { inherit pkgs; };
        in
        {
          default = pwnshop;
          inherit
            discord-feedback
            pwn-platform-runtime
            pwn-workspace-runtime
            pwnshop
            ;
        }
      );

      devShells = forAllSystems (
        system:
        let
          pkgs = import nixpkgs { inherit system; };

          pwn-workspace-runtime = import ./runtime/workspace { inherit pkgs; };
          pwn-platform-runtime = import ./runtime/platform { inherit pkgs lib; };

          pwnshop = import ./tools/pwnshop { inherit pkgs pwn-workspace-runtime; };
          discord-feedback = import ./tools/feedback { inherit pkgs; };
        in
        {
          default = pkgs.mkShell {
            packages = with pkgs; [
              asciinema
              discord-feedback
              docker
              git
              git-crypt
              jq
              pwn-platform-runtime
              pwn-workspace-runtime
              pwnshop
              tomlq
              uv
            ];
            shellHook = ''
              export PWN_WORKSPACE="${pwn-workspace-runtime}"

              # Install the secret-test encryption pre-commit hook (idempotent,
              # non-destructive). Resolve the path Git actually runs the hook from
              # -- honoring core.hooksPath and the shared hooks dir of a linked
              # worktree -- and point it at the main checkout's copy so removing a
              # worktree can't break it.
              if git rev-parse --git-dir >/dev/null 2>&1; then
                hooks_dir="$(git config --path core.hooksPath 2>/dev/null || true)"
                [ -n "$hooks_dir" ] || hooks_dir="$(git rev-parse --git-path hooks)"
                root="$(cd "$(git rev-parse --git-common-dir)/.." && pwd)"
                hook="$hooks_dir/pre-commit"
                target="$root/tools/git-hooks/pre-commit"
                if [ ! -e "$hook" ] && [ ! -L "$hook" ]; then
                  mkdir -p "$hooks_dir"
                  ln -s "$target" "$hook"
                elif [ "$(readlink -f "$hook" 2>/dev/null)" != "$(readlink -f "$target" 2>/dev/null)" ]; then
                  echo "note: $hook already exists; not overwriting (encryption hook: tools/git-hooks/pre-commit)" >&2
                fi
              fi

              sudo=
              if [ "$(id -u)" -ne 0 ]; then
                if command -v sudo >/dev/null 2>&1; then
                  sudo=sudo
                else
                  echo "error: cannot start the challenge runtime without root privileges" >&2
                  return 1
                fi
              fi

              if ! runtime_environment="$($sudo ${lib.getExe pwn-platform-runtime})"; then
                echo "error: failed to start the challenge runtime" >&2
                return 1
              fi
              eval "$runtime_environment"
            '';
          };
        }
      );
    };
}
