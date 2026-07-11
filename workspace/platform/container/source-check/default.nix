{ pkgs }:

pkgs.buildGoModule {
  pname = "pwn-source-check";
  version = "0.1.0";

  src = ./.;
  vendorHash = "sha256-em9ml6uLPU+ftvcqDezB+mb94Kw5Jf7kuuwbC65Xfac=";

  postInstall = ''
    mv "$out/bin/source-check" "$out/bin/pwn-source-check"
  '';

  ldflags = [
    "-s"
    "-w"
  ];
}
