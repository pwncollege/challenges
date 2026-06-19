#!/bin/bash -ex

cat >/tmp/wrong.js <<'EOF'
function build() {
    return [0, 97, 115, 109, 1, 0, 0, 0, 10, 0, 1, 0];
}
EOF

if /challenge/run /tmp/wrong.js 2>&1 | grep -q 'pwn.college{'; then
    echo "malformed module unexpectedly received the flag" >&2
    exit 1
fi
