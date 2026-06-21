case "${PATH:-}" in
/run/challenge/bin:/run/workspace/profile/bin | /run/challenge/bin:/run/workspace/profile/bin:*) ;;
*) export PATH="/run/challenge/bin:/run/workspace/profile/bin${PATH:+:$PATH}" ;;
esac

export LANG="${LANG:-C.UTF-8}"
export MANPATH="${MANPATH:-/run/workspace/profile/share/man:}"
export SSL_CERT_FILE="${SSL_CERT_FILE:-/run/workspace/profile/etc/ssl/certs/ca-bundle.crt}"
export TERMINFO="${TERMINFO:-/run/workspace/profile/share/terminfo}"

if tput setaf 1 >/dev/null 2>&1; then
  PS1='\[\033[01;32m\]\u@\h\[\033[00m\]:\[\033[01;34m\]\w\[\033[00m\]\$ '
  alias ls='ls --color=auto'
  alias grep='grep --color=auto'
fi

case ${TERM:-} in
xterm*)
  PS1="\[\e]0;\u@\h: \w\a\]$PS1"
  ;;
esac
