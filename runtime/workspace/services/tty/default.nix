{ pkgs }:
let
  ttydIndex =
    pkgs.runCommand "workspace-ttyd-index"
      {
        nativeBuildInputs = [
          pkgs.coreutils
          pkgs.gzip
          pkgs.perl
        ];
      }
      ''
        perl -0777 -ne 'while (/0x([0-9a-fA-F]{2})/g) { print chr(hex($1)) }' \
          ${pkgs.ttyd.src}/src/html.h \
          | gzip -dc > index.html

        {
          printf '<style>\n'
          printf '@font-face{font-family:"DejaVu Sans Mono";src:url(data:font/ttf;base64,'
          base64 -w0 ${pkgs.dejavu_fonts}/share/fonts/truetype/DejaVuSansMono.ttf
          printf ') format("truetype");font-weight:400;font-style:normal;font-display:block;}\n'
          printf '</style>\n'
        } > font.html

        perl -0pi -e 'open my $fh, "<", "font.html" or die $!; local $/; my $font = <$fh>; s#</head>#$font</head>#' index.html

        mkdir -p $out/share/workspace/ttyd
        cp index.html $out/share/workspace/ttyd/index.html
      '';

  ttyService = pkgs.writeShellApplication {
    name = "workspace-tty";
    runtimeInputs = [
      pkgs.ttyd
    ];
    text = ''
      exec ttyd \
        --index ${ttydIndex}/share/workspace/ttyd/index.html \
        --interface /run/workspace/user/services/tty/ttyd.sock \
        --writable \
        -t disableLeaveAlert=true \
        -t disableResizeOverlay=true \
        -t 'fontFamily="DejaVu Sans Mono", monospace' \
        --cwd "$HOME" \
        "$SHELL" \
        --login
    '';
  };

  serviceConfig = pkgs.writeText "tty.toml" ''
    name = "tty"
    socket_path = "/run/workspace/user/services/tty/ttyd.sock"
    start_timeout = "5s"
    ready_path = "/"

    command = [
      "workspace-tty",
    ]
  '';
in
pkgs.symlinkJoin {
  name = "workspace-tty";
  paths = [
    ttyService
  ];
  postBuild = ''
    mkdir -p $out/share/workspace/services
    cp ${serviceConfig} $out/share/workspace/services/tty.toml
  '';
}
