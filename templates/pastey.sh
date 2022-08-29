#!/usr/bin/env bash

# c-basic-offset: 4; tab-width: 4; indent-tabs-mode: t
# vi: set shiftwidth=4 tabstop=4 noexpandtab:
# :indentSize=4:tabSize=4:noTabs=false:

# script framework based on https://betterdev.blog/minimal-safe-bash-script-template/
# initially adapted and written by Serge van Ginderachter <serge@vanginderachter.be>

set -Eeo pipefail
#execute=(echo popo)trap cleanup SIGINT SIGTERM ERR EXIT

script_dir=$(cd "$(dirname "${BASH_SOURCE[0]}")" &>/dev/null && pwd -P)

# your custom endpoint
PASTEY_ENDPOINT="{{ endpoint }}"

#
## functions

usage() {
  cat <<-EOF
	Usage: $(basename "${BASH_SOURCE[0]}") [-h] [-v] [-f] -p param_value arg1 [arg2...]

	Script description here.

	Available options:

	-h, --help      Print this help and exit
	-v, --verbose   Print script debug info
	-c, --content   Pass the content of the paste in a simple argument
	-e, --encrypt   Encrypt the paste content
	-f, --file		Read the content from this file. If file is "-", read from stdin
	-s, --single    Create a paste that expires after the first view
	-t, --title     Set the title of the paste
	-x, --expiration
					Set the time in hours after which the paste expires

	--              Stop further option parsing
					Arguments passed after the -- option are evaluated
					as a command, and that command's output is pasted.
					The full command is used a the title.

	If zero arguments are passed,
	or none of --content, --file or -- are passed,
	content is read from stdin.

	EOF
  exit
}

cleanup() {
  trap - SIGINT SIGTERM ERR EXIT
  msg "Some unhandled error happened.\n"
  usage
}

msg() {
  echo >&2 -e "${1-}"
}

die() {
  local msg=$1
  local code=${2-1} # default exit status 1
  msg "$msg\n"
  exit "$code"
}

parse_params() {
	# check required params and arguments


	expiration=
	content=
	title=
	file=
	single=
	encrypt=

	while (( "$#" ))
    do
        case "${1-}" in

            -h | --help)
                usage
                ;;

            -v | --verbose)
                set -x
                ;;

            -t | --title)
                shift || :
                title="${1}"
                shift || :
                ;;

            -c | --content)
                shift || :
                content="${1}"
                shift || :
                ;;

            -f | --file)
                shift || :
				file="${1}"
                shift || :
                ;;
            -x | --expiration)
                shift || :
                expiration="${1}"
                shift || :
                ;;

            -s | --single)
                shift || :
                single="-F single="
                ;;

            -e | --encrypt)
                shift || :
                encrypt="-F encrypt="
                ;;

            --)
                shift || :
				execute=($*)
				shift $#
				;;

            -?*)
                die "Unknown option: $1"
                shift || :
                ;;

            *)
                if [[ -n "${1:-}" ]]
                then
                    die "Unknown parameter: $1"
                fi
                ;;

        esac
    done

}

parse_options(){

	# warn if both single and expiration are set
    if [[ -n "${expiration}" ]] && [[ -n "${single}" ]]
    then
        die "option -x|--expiration and -s|--single are mutually exclusive"
    fi

	# warn if more than 1 source
    if [[ -n "${content}"    && -n "${file}" ]] ||
       [[ -n "${content}"    && -n "${execute[*]}" ]] ||
       [[ -n "${execute[*]}" && -n "${file}" ]]
    then
        die "option -c|--content, -f|--file and -- <command> are mutually exclusive"
    fi

	if [[ -z "${content}" ]]
	then
		if [[ -n "${file}" ]]
		then
			if [[ ${file} = "-" ]]
			then
				content="$(</dev/stdin)"
			elif [ -r ${file} ]
			then
				content="$(<${file})"
			else
				die "Could not read from ${file}"
			fi
		elif [[ -n "${execute[*]}" ]]
		then
			content="$( bash -c "${execute[*]}" 2>&1 ||: )"
		else
			content="$(</dev/stdin)"
		fi
	fi

	# expiration needs to be set to disabled
	if [ -z "${expiration}" ]
	then
		expiration="-1"
	fi

	# alternative titles if possible
	if [ -z "${title}" ]
	then
		if [ -n "${file}" ]
		then
			title="${file}"
		elif [ -n "${execute[*]}" ]
		then
			title="${execute[@]}"
		fi
	fi

}


# just do it now
paste_it() {

	curl \
		-X POST \
		-F "cli=" \
		-F "title=${title}" \
		-F "content=${content}" \
		-F "expiration=${expiration}" \
		${encrypt} ${single} \
		${PASTEY_ENDPOINT}

}

## main execution

parse_params $*
parse_options
paste_it

# exit cleanly
trap - SIGINT SIGTERM ERR EXIT
exit 0
