#!/bin/bash

# Install this script into your PATH and chmod +x
# Usage example:
# $ cat /var/log/nginx.log | pastey

if ! command -v curl &> /dev/null ; then
    echo "Please install curl to use this script"
    exit 1
fi

PASTEY_ENDPOINT="{{ endpoint }}"
PASTEY_CONTENT=$(</dev/stdin)

# Submit paste
PASTEY_LINK=$(curl -s -X POST -H "Content-Type: text/plain" --data "${PASTEY_CONTENT}" "${PASTEY_ENDPOINT}")

# Print link
echo "${PASTEY_LINK}"
