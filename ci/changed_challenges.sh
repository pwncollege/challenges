#!/bin/bash

# Script to detect changed challenges in a git repository
# Usage: ./changed_challenges.sh [BASE_SHA] [HEAD_SHA]
#        ./changed_challenges.sh [BASE_SHA]  # compares BASE_SHA with HEAD
#
# If no arguments provided, it will try to detect from GitHub Actions environment
# Output: Space-separated list of changed challenge paths (module/challenge format)
#
# This script also detects when base templates change and includes all challenges
# that depend on those templates

set -e

# Determine the SHAs to compare
if [ $# -eq 2 ]; then
    # Use provided arguments
    BASE_SHA="$1"
    HEAD_SHA="$2"
elif [ $# -eq 1 ]; then
    # Single argument is the BASE SHA, compare with current HEAD
    BASE_SHA="$1"
    HEAD_SHA="HEAD"
elif [ -n "$GITHUB_EVENT_NAME" ]; then
    # Running in GitHub Actions
    if [ "$GITHUB_EVENT_NAME" = "pull_request" ]; then
        BASE_SHA="${GITHUB_BASE_SHA:-$GITHUB_EVENT_PULL_REQUEST_BASE_SHA}"
        HEAD_SHA="HEAD"
    else
        # For pushes, use the before and after commits from the push event
        BASE_SHA="${GITHUB_EVENT_BEFORE}"
        HEAD_SHA="${GITHUB_EVENT_AFTER}"
        
        # If this is the first commit or force push with no common history
        if [ "$BASE_SHA" = "0000000000000000000000000000000000000000" ]; then
            # Compare against empty tree
            BASE_SHA=$(git hash-object -t tree /dev/null)
        fi
    fi
else
    # Default to comparing with main branch
    # Check if we're on main branch locally
    CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
    if [ "$CURRENT_BRANCH" = "main" ]; then
        # On main branch, compare with origin/main
        if git rev-parse --verify origin/main >/dev/null 2>&1; then
            BASE_SHA="origin/main"
        else
            echo "Error: On main branch but origin/main not found" >&2
            exit 1
        fi
    else
        # Not on main, compare with local main
        if git rev-parse --verify main >/dev/null 2>&1; then
            BASE_SHA="main"
        else
            echo "Error: Could not find main branch" >&2
            exit 1
        fi
    fi
    HEAD_SHA="HEAD"
fi

# Find all challenges that use (extend/include) a template
find_dependent_challenges() {
    local template="$1"
    template=${template#./}
    local name=$(basename "$template")
    local rel_path=${template#challenges/}
    rel_path=${rel_path#*/}  # Remove module prefix
    
    # Find all .j2 files in challenge dirs that reference this template
    find challenges -name "*.j2" -path "*/challenge/*" 2>/dev/null | \
        xargs grep -lE "{%-? *(extends|include).*[\"'](.*/)?(${name}|${rel_path})[\"']" 2>/dev/null | \
        sed 's|^challenges/||' | cut -d'/' -f1-2 | sort -u || true
}

# Recursively find all templates that depend on a given template
find_child_templates() {
    local template="$1"
    template=${template#./}
    local module_path=${template#challenges/}
    local module=${module_path%%/*}
    local module_dir="challenges/$module"
    local seen=()
    local queue=("$template")
    
    while [ ${#queue[@]} -gt 0 ]; do
        local current="${queue[0]}"
        queue=("${queue[@]:1}")  # Remove first element
        
        # Skip if already seen
        [[ " ${seen[@]} " =~ " ${current} " ]] && continue
        seen+=("$current")
        
        local name=$(basename "$current")
        local rel_path=${current#challenges/}
        rel_path=${rel_path#*/}
        
        # Find templates that reference this one
        local children=$(
            grep -rE "{%-? *(extends|include).*[\"'](.*/)?(${name}|${rel_path})[\"']" \
                --include="*.j2" "$module_dir" 2>/dev/null | cut -d':' -f1 | sort -u || true
        )
        
        # Add children to queue
        for child in $children; do
            [[ " ${seen[@]} " =~ " ${child} " ]] || queue+=("$child")
        done
    done
    
    printf '%s\n' "${seen[@]}"
}

DIRECT_CHALLENGES=$(git diff --name-only "$BASE_SHA" "$HEAD_SHA" | grep -E '^challenges/[^/]+/[^/]+/' | cut -d'/' -f2-3 | sort -u || true)
CHANGED_BASE_TEMPLATES=$(git diff --name-only "$BASE_SHA" "$HEAD_SHA" | grep -E '^challenges/[^/]+/base_templates/.*\.j2$' || true)

declare -A AFFECTED_CHALLENGES_SET

# Add directly changed challenges that exist
for challenge in $DIRECT_CHALLENGES; do
    if [[ -d "challenges/$challenge/challenge" || -d "challenges/$challenge/tests_public" || -d "challenges/$challenge/tests_private" ]]; then
        AFFECTED_CHALLENGES_SET["$challenge"]=1
    fi
done

# Process base template changes
for template in $CHANGED_BASE_TEMPLATES; do
    # Find all templates that depend on this one (including itself)
    for dependent_template in $(find_child_templates "$template"); do
        # Find all challenges using this template
        for challenge in $(find_dependent_challenges "$dependent_template"); do
            AFFECTED_CHALLENGES_SET["$challenge"]=1
        done
    done
done

[ ${#AFFECTED_CHALLENGES_SET[@]} -eq 0 ] || printf '%s\n' "${!AFFECTED_CHALLENGES_SET[@]}" | sort
