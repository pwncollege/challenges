#!/bin/bash
set -euo pipefail

work=$(mktemp -d)
trap 'rm -rf "$work"' EXIT
mkdir "$work/bin"
cat > "$work/bin/gcc" <<'EOF'
#!/bin/sh
echo 'The workspace compiler should not be used.' >&2
exit 1
EOF
chmod +x "$work/bin/gcc"

test "$(command -v make)" = /run/challenge/bin/make
cd /usr/src/linux
before=$(sha256sum .config)
PATH="/run/challenge/bin:$work/bin:$PATH" make -j4 </dev/null
test "$(sha256sum .config)" = "$before"

cat > "$work/Makefile" <<'EOF'
all:
	@test "$$(command -v gcc)" = /usr/lib/ccache/gcc
	@test "$$(command -v ld)" = /usr/bin/ld
	@gcc --version
EOF
PATH="/run/challenge/bin:$work/bin:$PATH" make -f "$work/Makefile"
