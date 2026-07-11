{ pkgs }:

pkgs.buildGoModule {
  pname = "workspace-daemon";
  version = "0.1.0";

  src = ./.;
  vendorHash = "sha256-kjpwIfxM9MA98Wa6hSrbYMD4pcq+VAaXzlFhJRcC3fQ=";

  buildInputs = [ pkgs.btrfs-progs.dev ];

  ldflags = [
    "-s"
    "-w"
  ];
}
