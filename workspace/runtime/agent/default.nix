{ pkgs }:

pkgs.buildGoModule {
  pname = "workspace-agent";
  version = "0.1.0";

  src = ./.;
  vendorHash = "sha256-kqUJAETQLpXyi/2FpNZG66nS+oX/qLeHZd4BUQjEvNA=";

  ldflags = [
    "-s"
    "-w"
  ];
}
