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
          printf '@font-face{font-family:"JetBrains Mono";src:url(data:font/woff2;base64,'
          base64 -w0 ${pkgs.jetbrains-mono}/share/fonts/WOFF2/JetBrainsMono-Regular.woff2
          printf ') format("woff2");font-weight:400;font-style:normal;font-display:block;}\n'
          printf '</style>\n'
          printf '<script>\n'
          printf 'window.__workspaceReadyTerminalFont=function(){if(!document.fonts)return Promise.resolve();var font=Promise.all([document.fonts.load('"'"'13px "JetBrains Mono"'"'"'),document.fonts.ready]);var timeout=new Promise(function(resolve){setTimeout(resolve,1000)});return Promise.race([font,timeout]).catch(function(){})};\n'
          printf '</script>\n'
        } > font.html

        perl -0pi -e 'open my $fh, "<", "font.html" or die $!; local $/; my $font = <$fh>; s#</head>#$font</head>#' index.html
        perl -0pi -e 's#fontFamily:"Consolas,Liberation Mono,Menlo,Courier,monospace"#fontFamily:"\\"JetBrains Mono\\", monospace"#' index.html
        perl -0pi -e 's#\Q(0,e.render)((0,e.h)(t.App,null),document.body)\E#(window.__workspaceReadyTerminalFont?window.__workspaceReadyTerminalFont():Promise.resolve()).then(function(){(0,e.render)((0,e.h)(t.App,null),document.body)})#' index.html

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
