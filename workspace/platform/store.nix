{
  pkgs,
  name,
  workspaceRuntime,
  dataDir,
}:

let
  closureInfo = pkgs.closureInfo { rootPaths = [ workspaceRuntime ]; };
  closuresDir = "${dataDir}/workspace-closures";
  closureRoot = "${closuresDir}/${builtins.baseNameOf workspaceRuntime}";
  nixStorePath = "${closureRoot}/store";
  gcRoot = "/nix/var/nix/gcroots/${name}-store";

  populate = pkgs.writeShellApplication {
    name = "${name}-store-populate";
    runtimeInputs = with pkgs; [
      coreutils
      util-linux
    ];
    text = ''
      set -euo pipefail

      build_root="$1"
      store_paths_file="$2"

      mount --make-rprivate /
      # The helper itself is loaded from the store, so detach the read-only
      # mount while its executable remains referenced by this namespace.
      umount --lazy /nix/store

      if [[ "$(stat --format=%d /nix/store)" != "$(stat --format=%d "$build_root")" ]]; then
        echo "Error: workspace closures and the Nix store must share a filesystem" >&2
        exit 1
      fi

      mapfile -t store_paths < "$store_paths_file"
      if (( ''${#store_paths[@]} == 0 )); then
        echo "Error: workspace runtime closure is empty" >&2
        exit 1
      fi
      cp --archive --link -- "''${store_paths[@]}" "$build_root/store/"
    '';
  };

  setup = pkgs.writeShellApplication {
    name = "${name}-store-setup";
    runtimeInputs = with pkgs; [
      coreutils
      util-linux
    ];
    text = ''
      set -euo pipefail

      closures_dir='${closuresDir}'
      closure_root='${closureRoot}'
      store_path='${nixStorePath}'

      install -d -m 0711 "$closures_dir"
      install -d -m 0755 /nix/var/nix/gcroots
      ln -sfnT '${workspaceRuntime}' '${gcRoot}'

      exec 9>"$closures_dir/.lock"
      flock 9

      if [[ -d "$store_path" ]]; then
        exit 0
      fi

      build_root="$(mktemp --directory "$closures_dir/.${builtins.baseNameOf workspaceRuntime}.XXXXXX")"
      cleanup() {
        rm -rf "$build_root"
      }
      trap cleanup EXIT

      install -d -m 0555 "$build_root/store"
      unshare --mount --fork -- \
        '${populate}/bin/${name}-store-populate' \
        "$build_root" \
        '${closureInfo}/store-paths'

      chmod 0555 "$build_root"
      mv --no-target-directory "$build_root" "$closure_root"
      trap - EXIT
    '';
  };
in
{
  inherit nixStorePath;

  service = {
    description = "pwn.college workspace Nix store";
    after = [ "local-fs.target" ];
    wantedBy = [ "multi-user.target" ];
    serviceConfig = {
      Type = "oneshot";
      ExecStart = "${setup}/bin/${name}-store-setup";
      RemainAfterExit = true;
    };
  };

  tmpfilesRules = [ "d ${closuresDir} 0711 root root -" ];
}
