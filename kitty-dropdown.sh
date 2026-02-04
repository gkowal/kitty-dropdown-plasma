if [[ "$TERM" == "xterm-kitty" ]]; then
	PARENT_NAME=$(ps -p $PPID -o comm= 2>/dev/null | tr -d ' ')
	if [[ "$PARENT_NAME" == "kitten" ]]; then
		export IGNOREEOF=1
		bind '"\C-d": "\C-u \C-k clear\n"'
		alias qexit='unset IGNOREEOF && exit'
	else
		export IGNOREEOF=0
	fi
fi
