#!/usr/bin/env bash
set -euo pipefail

label="$1"
shift

heartbeat_interval="${HEARTBEAT_INTERVAL_SECONDS:-10}"
log_file="$(mktemp)"

print_resource_snapshot() {
  echo "loadavg: $(cut -d' ' -f1-3 /proc/loadavg)"
  echo "::group::host resources $(date -Ins)"
  free -h || true
  df -h / /tmp /run /mnt/pwn.college /var/lib/pwn.college 2>/dev/null | awk '!seen[$0]++' || true
  for pressure in cpu memory io; do
    if [ -r "/proc/pressure/${pressure}" ]; then
      echo "--- /proc/pressure/${pressure} ---"
      cat "/proc/pressure/${pressure}" || true
    fi
  done
  echo "--- top cpu ---"
  ps -eo pid,ppid,stat,etime,pcpu,pmem,rss,args --sort=-pcpu | head -n 12 || true
  echo "--- top rss ---"
  ps -eo pid,ppid,stat,etime,pcpu,pmem,rss,args --sort=-rss | head -n 12 || true
  echo "::endgroup::"
}

echo "${label}: started at $(date -Ins)"
"$@" >"$log_file" 2>&1 &
cmd_pid=$!

(
  while kill -0 "$cmd_pid" 2>/dev/null; do
    sleep "$heartbeat_interval"
    if ! kill -0 "$cmd_pid" 2>/dev/null; then
      break
    fi
    echo "::group::${label} heartbeat $(date -Ins)"
    echo "recent ${label} output:"
    tail -n 80 "$log_file" || true
    print_resource_snapshot
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

print_resource_snapshot
echo "::group::${label} final output"
tail -n 200 "$log_file" || true
echo "::endgroup::"
echo "${label}: finished at $(date -Ins) (status=${status})"
rm -f "$log_file"
exit "$status"
