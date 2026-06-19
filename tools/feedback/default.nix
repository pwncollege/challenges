{ pkgs }:

pkgs.writeShellApplication {
  name = "discord-feedback";
  runtimeInputs = with pkgs; [
    git
    uv
  ];
  text = ''
    set -euo pipefail
    root="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
    exec "$root/tools/feedback/discord-feedback" "$@"
  '';
}
