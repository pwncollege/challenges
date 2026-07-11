{ pkgs }:

pkgs.buildGoModule {
  pname = "workspace-daemon";
  version = "0.1.0";

  src = ./.;
  vendorHash = "sha256-gseQY5ihAwjIa5WDtcNJHSqen+IqmkzaDHo7uPdcIy8=";

  buildInputs = [ pkgs.btrfs-progs.dev ];

  ldflags = [
    "-s"
    "-w"
  ];
}
