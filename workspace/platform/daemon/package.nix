{ pkgs }:

pkgs.buildGoModule {
  pname = "workspace-daemon";
  version = "0.1.0";

  src = ./.;
  vendorHash = "sha256-+WUINRXAKVIQ3uSrRQvVduH9dlbt+79DQpRSE5bNUB0=";

  nativeCheckInputs = [ pkgs.e2fsprogs ];

  ldflags = [
    "-s"
    "-w"
  ];
}
