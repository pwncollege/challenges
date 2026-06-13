function set_secret {
	rm -f /tmp/.pwn-secret
	echo $RANDOM > /tmp/.pwn-secret
}

function check_cmd {
	BCMD=($BASH_COMMAND)
	BCMD_BASE=$(basename -- "${BCMD[0]}")

	if [ "$BCMD_BASE" != "bash" ] && [ "$BCMD_BASE" != "sh" ]
	then
		unset BASH_ENV
		return 0
	fi

	if [ "${#BCMD[@]}" -gt 2 ]
	then
		fold -s <<< "No shenanigans with bash options yet, please! Just run your script with 'bash x.sh'."
	fi

	if [[ "${BCMD[1]}" != *.sh ]]
	then
		fold -s <<< "Please name your script with an '.sh' extension. This isn't strictly necessary eventually, but we'll keep things explicit for the next few levels."
		return 1
	fi

	export BASH_ENV=/challenge/.hook
}

shopt -s extdebug
PROMPT_COMMAND="trap check_cmd debug; set_secret; $PROMPT_COMMAND"
