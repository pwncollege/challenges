function check_cmd {
	local assignment_re='^(export[[:space:]]+)?([a-zA-Z_][a-zA-Z0-9_]*)=(\$\((.*)\)|`(.*)`|"\$\((.*)\)"|"`(.*)`")$'

	if [ "$BASH_SUBSHELL" -eq 0 ]
	then
		rm -f /tmp/subshell

		if [[ "${BASH_COMMAND}" =~ $assignment_re ]]
		then
			printf '%s\n' "${BASH_REMATCH[2]}" > /tmp/dstvar
		else
			rm -f /tmp/dstvar
		fi
	else
		touch /tmp/subshell
	fi
}

set -T
PROMPT_COMMAND="trap check_cmd debug"
