#!/usr/bin/env bash
set -euo pipefail

export DOCKER_BUILDKIT=1

parallel_jobs="${JOBS:-$(nproc)}"
build_timestamp_utc="$(date --utc +'%Y-%m-%dT%H:%M:%SZ')"
export build_timestamp_utc

build_one_task() {
  local dojo_root="$1" dojo_id="$2" module_id="$3" challenge_id="$4" instance_id="$5" base_image="$6"

  local image_tag="pwncollege/challenge-${module_id}-${challenge_id}${instance_id:+-${instance_id}}:latest"

  local dockerfile_content="# syntax=docker/dockerfile:1\nFROM ${base_image}\n"

  local challenge_dir="${dojo_root}/${module_id}/${challenge_id}"
  if [[ -d "$challenge_dir" ]]; then
    while IFS= read -r -d '' file_path; do
      local rel_src="${file_path#${dojo_root}/}"
      local image_path="/challenge/${rel_src#${module_id}/${challenge_id}/}"
      dockerfile_content+="COPY --chmod=4755 --chown=0:0 ${rel_src} ${image_path}\n"
    done < <(find "$challenge_dir" -maxdepth 1 -xtype f -print0)
  fi

  if [[ -n "$instance_id" ]]; then
    local instance_dir="${challenge_dir}/_${instance_id}"
    if [[ -d "$instance_dir" ]]; then
      while IFS= read -r -d '' file_path; do
        local rel_src="${file_path#${dojo_root}/}"
        local image_path="/challenge/${file_path#${instance_dir}/}"
        dockerfile_content+="COPY --chmod=4755 --chown=0:0 ${rel_src} ${image_path}\n"
      done < <(find "$instance_dir" -xtype f -print0)
    fi
  fi

  printf '%b' "$dockerfile_content" |
  docker build -t "$image_tag" \
    --annotation "college.pwn.dojo=${dojo_id}" \
    --annotation "college.pwn.module=${module_id}" \
    --annotation "college.pwn.challenge=${challenge_id}" \
    ${instance_id:+--annotation "college.pwn.challenge-instance=${instance_id}"} \
    --annotation "org.opencontainers.image.created=${build_timestamp_utc}" \
    --pull --quiet -f - "$dojo_root" > /dev/null 2>&1 \
  || { echo "[ERROR] Failed to build image: ${image_tag}" >&2; exit 1; }

  echo "[OK] ${image_tag}"
}
export -f build_one_task

generate_tasks_for_dojo() {
  local dojo_root="$1"
  local dojo_manifest="${dojo_root}/dojo.yml"
  [[ -f "$dojo_manifest" ]] || { echo "[WARN] No dojo.yml in ${dojo_root}, skipping" >&2; return; }

  local dojo_id modules_list challenges_list module_id challenge_id base_image challenge_root instance_id
  dojo_id="$(yq -r '.id' "$dojo_manifest")"
  modules_list="$(yq -r '.modules[].id' "$dojo_manifest")"

  for module_id in $modules_list; do
    local module_manifest="${dojo_root}/${module_id}/module.yml"
    [[ -f "$module_manifest" ]] || continue

    challenges_list="$(yq -r '[
      (.challenges[]? | .id),
      (.resources[]? | select(.type=="challenge") | .id)
    ] | .[]' "$module_manifest")"

    for challenge_id in $challenges_list; do
      base_image="$(yq -r --arg id "$challenge_id" '
        [
          (.challenges[]? | select(.id==$id) | .image),
          (.resources[]? | select(.type=="challenge" and .id==$id) | .image)
        ] | map(select(.!=null and .!="" )) | .[0] // ""' "$module_manifest")"
      base_image="${base_image:-pwncollege/challenge-legacy:latest}"

      challenge_root="${dojo_root}/${module_id}/${challenge_id}"
      if ! compgen -G "${challenge_root}/_*" > /dev/null; then
        printf '%s\0%s\0%s\0%s\0\0%s\0' "$dojo_root" "$dojo_id" "$module_id" "$challenge_id" "$base_image"
        continue
      fi

      find "$challenge_root" -maxdepth 1 -type d -name '_*' -print0 |
      while IFS= read -r -d '' instance_dir; do
        instance_id="${instance_dir##*/_}"
        printf '%s\0%s\0%s\0%s\0%s\0%s\0' "$dojo_root" "$dojo_id" "$module_id" "$challenge_id" "$instance_id" "$base_image"
      done
    done
  done
}

for dojo_root in "$@"; do
  generate_tasks_for_dojo "$dojo_root"
done |
xargs -0 -n6 -P "$parallel_jobs" bash -c '
  trap "kill 0" INT TERM
  build_one_task "$@" &
  wait
' _
