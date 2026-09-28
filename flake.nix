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
    { nixpkgs, ... }:
    let
      lib = nixpkgs.lib;
      systems = [ "x86_64-linux" ];
      forAllSystems = f: lib.genAttrs systems (system: f system);
      workspaceConfig = {
        packageProfile =
          let
            value = builtins.getEnv "PWN_WORKSPACE_PACKAGES";
          in
          if value == "" then "minimal" else value;
        code = builtins.getEnv "PWN_WORKSPACE_SERVICE_CODE" == "1";
        desktop = builtins.getEnv "PWN_WORKSPACE_SERVICE_DESKTOP" == "1";
      };
    in
    {
      nixosModules = {
        default = import ./workspace/module.nix;
        workspace = import ./workspace/module.nix;
      };

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

          workspaceSystem = import ./workspace { inherit pkgs lib; };
          runtime = workspaceSystem.mkRuntime workspaceConfig;
          workspace-daemon = workspaceSystem.workspaceDaemon;
          pwn-workspace = workspaceSystem.mkActivator runtime { };

          pwnshop = import ./tools/pwnshop {
            inherit pkgs;
            pwn-workspace-runtime = runtime.runtime;
          };
          discord-feedback = import ./tools/feedback { inherit pkgs; };
        in
        {
          default = pwnshop;
          inherit
            discord-feedback
            pwn-workspace
            pwnshop
            workspace-daemon
            ;
        }
      );

      devShells = forAllSystems (
        system:
        let
          pkgs = import nixpkgs { inherit system; };

          workspaceSystem = import ./workspace { inherit pkgs lib; };
          runtime = workspaceSystem.mkRuntime workspaceConfig;
          fullRuntime = workspaceSystem.mkRuntime {
            packageProfile = "extended";
            code = true;
            desktop = true;
          };
          pwnshop = import ./tools/pwnshop {
            inherit pkgs;
            pwn-workspace-runtime = runtime.runtime;
          };
          discord-feedback = import ./tools/feedback { inherit pkgs; };
          mkDevShell =
            {
              selectedRuntime,
              activatorOptions ? { },
              extraPackages ? [ ],
            }:
            let
              pwn-workspace = workspaceSystem.mkActivator selectedRuntime activatorOptions;
            in
            pkgs.mkShell {
              packages =
                (with pkgs; [
                  asciinema
                  discord-feedback
                  docker
                  git
                  git-crypt
                  jq
                  pwn-workspace
                  pwnshop
                  tomlq
                  uv
                  selectedRuntime.runtime
                ])
                ++ extraPackages;
              shellHook = ''
                export PWN_WORKSPACE="${selectedRuntime.runtime}"
                echo "workspace: ${selectedRuntime.summary}" >&2

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

                if ! runtime_environment="$($sudo ${lib.getExe pwn-workspace})"; then
                  echo "error: failed to start the challenge runtime" >&2
                  return 1
                fi
                eval "$runtime_environment"
              '';
            };
        in
        {
          default = mkDevShell { selectedRuntime = runtime; };
          full = mkDevShell { selectedRuntime = fullRuntime; };
          control-plane = mkDevShell {
            selectedRuntime = runtime;
            activatorOptions.volumeBasePath = "/var/lib/pwn.college/homes";
            extraPackages = [
              pkgs.nodejs_24
              pkgs.containerd
            ];
          };
        }
      );
    };
}
