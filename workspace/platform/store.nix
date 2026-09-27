{ pkgs, workspaceRuntime }:

let
  closureInfo = pkgs.closureInfo { rootPaths = [ workspaceRuntime ]; };
in
pkgs.runCommand "pwn-workspace-store.erofs"
  {
    nativeBuildInputs = [
      pkgs.erofs-utils
      pkgs.gnutar
    ];
  }
  ''
    sed 's|^/nix/store/||' ${closureInfo}/store-paths > paths
    tar --create --directory /nix/store --files-from paths \
      --sort=name --owner=0 --group=0 --mtime=@0 |
      mkfs.erofs --quiet --tar=f -zlz4hc -T0 -U00000000-0000-0000-0000-000000000000 "$out"
    fsck.erofs "$out"
  ''
