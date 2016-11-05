#!/bin/bash
# Startup menu for TMUX
# version: 2014-12-23

#set -x
export PATH=$PATH:usr/local/bin

# abort if we're already inside a TMUX session
[ "$TMUX" == "" ] || exit 0

# startup a "default" session if none currently exists
tmux has-session -t _default || tmux new-session -s _default -d

options=$(tmux list-sessions -F "#S ''" | sort)
exec 3>&1
RES=$(dialog --title "Available sessions" \
	--menu "Sessions" 19 50 10 \
	${options[@]} \
	"LOAD TMUXP" "" \
	"NEW SESSION" "" \
	"BASH" "" \
	"TMUX-IPython" "" \
	"TMUX-mocp" "" \
	2>&1 1>&3)
retval=$?

if [ "$retval" != "0" ]; then
	exit 0
fi

case $RES in
	"NEW SESSION")
		exec 3>&1
		SESSION_NAME=$(dialog --title "New session" --inputbox "New session name:" 8 51 "" 2>&1 1>&3)
		retval=$?
		exec 3>&-
		if [ "$retval" != "0" ]; then
			exit 0
		fi
		if [ "$SESSION_NAME" == "" ]; then
			exit 0
		fi
		NAME="echo -ne \"\e]0;$SESSION_NAME - Tmux\007\""
		trap "$NAME" DEBUG
		tmux new -s "$SESSION_NAME"
		exit 0
		;;
	"BASH")
		bash --login
		exit 0
		;;
	"TMUX-IPython")
		CNT=$(tmux ls | grep -c TMux-IPython)
		SESSION_NAME="TMux-IPython-$((CNT+1))"
		NAME="echo -ne \"\e]0;$SESSION_NAME - Tmux\007\""
		trap "$NAME" DEBUG
		tmux new -s "$SESSION_NAME" "/usr/bin/ipython"
		exit 0
		;;
	"TMUX-mocp")
		SESSION_NAME="TMux-mocp"
		tmux has-session -t $SESSION_NAME || tmux new-session -s $SESSION_NAME -d "/usr/bin/mocp"
		NAME="echo -ne \"\e]0;$SESSION_NAME - Tmux\007\""
		trap "$NAME" DEBUG
		tmux attach-session -t "$SESSION_NAME" -d
		exit 0
		;;
	"LOAD TMUXP")
		options=($(find "$HOME/.tmuxp" -printf "%P %P\n" | sort))
		#exec 3>&1
		RES=$(dialog --title "Available TMUXP sessions" \
			--menu "Sessions" 19 50 10 \
			${options[@]} \
			2>&1 1>&3)
		retval=$?

		if [ "$retval" != "0" ]; then
			exit 0
		fi

		tmuxp load "${RES%%.yaml}"
		exit 0
		;;
	*)
		NAME="echo -ne \"\e]0;$RES - Tmux\007\""
		trap "$NAME" DEBUG
		tmux attach-session -t "$RES" -d
		exit 0
		;;
esac

tmux attach-session -t _default -d
