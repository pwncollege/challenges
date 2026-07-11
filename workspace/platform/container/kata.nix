{ pkgs }:

let
  kernel = import ./kernel.nix { inherit pkgs; };
in
pkgs.runCommand "pwn-workspace-kata-config.toml" { nativeBuildInputs = [ pkgs.gawk ]; } ''
  kernel_line="$(awk '$1 == "kernel" { print; exit }' ${pkgs.kata-runtime}/share/defaults/kata-containers/configuration.toml)"
  substitute ${pkgs.kata-runtime}/share/defaults/kata-containers/configuration.toml "$out" \
    --replace-fail \
      "$kernel_line" \
      'kernel = "${kernel}/share/kata-containers/vmlinux.container"'

  annotations_line="$(awk '$1 == "enable_annotations" { print; exit }' "$out")"
  substituteInPlace "$out" \
    --replace-fail \
      "$annotations_line" \
      'enable_annotations = ["enable_iommu", "virtio_fs_extra_args", "kernel_params", "kernel_verity_params", "default_memory"]'
''
