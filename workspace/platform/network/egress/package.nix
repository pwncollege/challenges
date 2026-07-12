{ pkgs }:

pkgs.buildGoModule {
  pname = "workspace-egress";
  version = "0.1.0";

  src = ./.;
  vendorHash = "sha256-4V3cIgEN8WkHHrPz9SRshoiu0C+NHR0Xov1FZ06Q9XI=";

  ldflags = [
    "-s"
    "-w"
  ];
}
