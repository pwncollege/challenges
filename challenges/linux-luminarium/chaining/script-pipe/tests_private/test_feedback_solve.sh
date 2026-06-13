#!/bin/bash
set -eo pipefail

cd /home/hacker

run_solve() {
	local shell_path=$1
	local script_name=$2
	local output

	cat > "$script_name" <<'EOF'
/challenge/pwn
/challenge/college
EOF

	output=$(
		bash -i <<EOF 2>&1
$shell_path $PWD/$script_name | /challenge/solve
EOF
	)
	printf '%s\n' "$output" | tee /dev/stderr

	grep -F 'pwn.college{' <<< "$output"
	! grep -F 'not piping this script out to /challenge/solve' <<< "$output"
}

run_solve bash feedback-bash.sh
run_solve /bin/bash feedback-bin-bash.sh
