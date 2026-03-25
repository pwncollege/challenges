#!/usr/bin/env bash
set -euo pipefail

label="$1"
shift

log_file="$(mktemp)"
echo "${label}: started at $(date -Ins)"
"$@" >"$log_file" 2>&1 &
cmd_pid=$!

(
  while kill -0 "$cmd_pid" 2>/dev/null; do
    sleep 15
    if ! kill -0 "$cmd_pid" 2>/dev/null; then
      break
    fi
    echo "::group::${label} heartbeat $(date -Ins)"
    echo "recent ${label} output:"
    tail -n 80 "$log_file" || true
    ps -eo pid,ppid,stat,etime,pcpu,pmem,args \
      | grep -E 'pwnshop|docker( |$)|pytest|python .*pwnshop|python .*lib.run_challenge|timeout --signal=TERM' \
      | grep -v grep || true
    docker ps --format 'table {{.ID}}\t{{.Status}}\t{{.Image}}\t{{.Names}}' || true
    echo "::endgroup::"
  done
) &
heartbeat_pid=$!

status=0
wait "$cmd_pid" || status=$?
kill "$heartbeat_pid" 2>/dev/null || true
wait "$heartbeat_pid" 2>/dev/null || true

echo "::group::${label} final output"
tail -n 200 "$log_file" || true
echo "::endgroup::"
echo "${label}: finished at $(date -Ins) (status=${status})"
rm -f "$log_file"
exit "$status"
