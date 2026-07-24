#!/bin/sh
set -eu

command -v nano
cmp -s /home/hacker/README.txt - <<'EOF'
Add a second line below this one.
EOF
