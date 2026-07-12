{ pkgs }:

pkgs.buildGoModule {
  pname = "pwn-network-policy";
  version = "0.1.0";

  src = ./.;
  vendorHash = "sha256-em9ml6uLPU+ftvcqDezB+mb94Kw5Jf7kuuwbC65Xfac=";

  postInstall = ''
    mv "$out/bin/policy" "$out/bin/pwn-network-policy"
  '';

  ldflags = [
    "-s"
    "-w"
  ];
}
