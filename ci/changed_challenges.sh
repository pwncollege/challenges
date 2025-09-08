#!/bin/bash

# Script to detect changed challenges in a git repository
# Usage: ./changed_challenges.sh [BASE_SHA] [HEAD_SHA]
#        ./changed_challenges.sh [BASE_SHA]  # compares BASE_SHA with HEAD
#
# If no arguments provided, it will try to detect from GitHub Actions environment
# Output: Space-separated list of changed challenge paths (module/challenge format)

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

# Get list of changed files
CHANGED_FILES=$(git diff --name-only "$BASE_SHA" "$HEAD_SHA")

# Extract unique challenge paths (module/challenge format)
CHALLENGES=$(echo "$CHANGED_FILES" | grep -E '^[^/]+/[^/]+/' | cut -d'/' -f1-2 | sort -u)

# Filter out non-challenge directories (like base_templates, legacy, etc.)
for CHALLENGE in $CHALLENGES; do
    if [[ -d "$CHALLENGE/challenge" || -d "$CHALLENGE/tests_public" || -d "$CHALLENGE/tests_private" ]]; then
        echo "$CHALLENGE"
    fi
done
