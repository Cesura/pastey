#!/usr/bin/env bash

PASTEY_ENDPOINT={{ endpoint }}

show_help() {
	cat <<-EOF
	Usage: ${0##*/} [-h] [-e] [-f INFILE] [-s] [-t title] [-x time_hrs] [-- command]

	CLI interface to pastey.

	Available options:

	-h, --help      Print this help and exit
	-e, --encrypt   Encrypt the paste content
	-f, --file		Read the content from this file.
	-s, --single    Create a paste that expires after the first view
	-t, --title     Set the title of the paste
	-x, --expiration
	                Set the time in hours after which the paste expires
	                (Default is expiration is disabled)
                    
	--              Stop further option parsing
	                Arguments passed after the -- option are evaluated
	                as a command, and that command's output is pasted.
	                The full command is used a the title.

	If zero arguments are passed,
	or none of --file or -- are passed,
	content is read from stdin.

	EOF
}

die() {
	printf '%s\n' "$1" >&2
	exit 1
}


# check required params and arguments

file=
expiration=
title=
single=
encrypt=
execute=

while :; do
	case $1 in
		-h|--help)
			show_help
			exit
			;;
		-e|--encrypt)
			encrypt='-F encrypt='
			;;
		-f|--file)
			if [ "$2" ]; then
				file=$2
				if [ ! "$title" ]; then
					title=$file
				fi
				shift
			else
				die 'ERROR: "--file requires a non-empty option argument.'
			fi
			;;
		--file=?*)
			file=${1#*=}
			title=$file
			;;
		--file=)	# Handle the case of an empty --file=
			die 'ERROR: "--file requires a non-empty option argument.'
			;;
		-s|--single)
			single='-F single='
			expiration=
			;;
		-t|--title)
			if [ "$2" ]; then
				title=$2
				shift
			else
				die 'ERROR: --title requires a non-empty option argument'
			fi
			;;
		--title=?*)
			title=${1#*=}
			;;
		--title=)	# Handle the case of an empty --title=
			die 'ERROR: --title requires a non-empty option argument'
			;;
		-x|--expiration)
			if [ "$2" ]; then
				expiration=$2
				shift
			else
				die 'ERROR: --expiration requires a non-empty option argument'
			fi
			;;
		--expiration=?*)
			expiration=${1#*=}
			;;
		--expiration=)	# Handle the case of an empty --expiration=
			die 'ERROR: --expiration requires a non-empty option argument'
			;;
		--)		# End of all options
			shift
			execute=("$@")
			if [ ! "$title" ]; then
				title=${execute[*]}
			fi
			break
			;;
		-?*)
			printf 'WARN: Unknown option (ignored): %s\n' "$1" >&2
			;;
		*)		# Default case: No more options, so break out of the loop.
			break
	esac
	shift
done


# do some sanity checks

if [ "$expiration" ] && [ "$single" ]; then
    die 'option -x|--expiration and -s|--single are mutually exclusive'
fi

if [ "${execute[*]}" ] && [ "$file" ]; then
    die "-f|--file and -- <command> are mutually exclusive"
fi

# set title to unknown if empty

if [ ! "$title" ]; then
	title=untitled
fi


# read contents

if [ "$execute" ]; then		# input from an executed command
	exec {content_fd}< <("${execute[@]}" 2>&1)
elif [ "$file" ]; then		# input from a file
	if [ -r "$file" ]; then
		exec {content_fd}< "$file"
	else
		die "Could not read from file \"$file\""
	fi
else	# read from stdin
	exec {content_fd}< /dev/fd/0
fi


# expiration needs to be set to -1 if disabled

if [ ! "${expiration}" ]; then
	expiration="-1"
fi


# upload

curl \
	-X POST \
	-F "cli=" \
	-F "title=$title" \
	-F "content=</dev/fd/$content_fd" \
	-F "expiration=$expiration" \
	${encrypt} \
	${single} \
	"${PASTEY_ENDPOINT}"
echo

exec {content_fd}<&-
