#!/bin/sh

set -eu

umask 077

###
### Globals
###

SSH_TIMEOUT=10
# this assumes it's called from root dir
SRCFILE="public_keys"
MERGE_SCRIPT="src/merge_keys.py"
TMPDIR="$(mktemp -d --tmpdir=.)"
TMPFILE="${TMPDIR}/tmpfile"
KEYSFILE="${TMPDIR}/authorized_keys"

###
### Functions
###

cleanup() {
    rm -rf "${TMPDIR}"
    echo "Cleaned up ${TMPDIR}"
}

get_authorized_keys() {
    local readonly host="${1}"

    echo "Getting authorized keys..."
    if scp -i "${TMPFILE}" -o StrictHostKeyChecking=no -o ConnectTimeout=${SSH_TIMEOUT} "${host}:~/.ssh/authorized_keys" "${KEYSFILE}"; then
        return 0
    else
        return 1
    fi
}

set_authorized_keys() {
    local readonly host="${1}"

    echo "Setting authorized keys..."
    # TODO: remove .new when we are sure this works
    if scp -i "${TMPFILE}" -o StrictHostKeyChecking=no -o ConnectTimeout=${SSH_TIMEOUT} "${KEYSFILE}" "${host}:~/.ssh/authorized_keys.new"; then
        return 0
    else
        return 1
    fi
}

edit_authorized_keys() {
    echo "Editing authorized keys..."
    python "${SRCFILE}" "${KEYSFILE}"
}

distribute() {
    local total=0
    local count=0

    echo "Storing private key to file: ${TMPFILE}"
    echo "${PRIVATE_KEY}" > "${TMPFILE}"
    for host in ${DISTRIBUTION_HOSTS}; do
        total=$((total + 1))
        echo "* Host #${count}"
        if get_authorized_keys "${host}"; then
            edit_authorized_keys
            if set_authorized_keys "${host}"; then
                count=$((count + 1))
                echo "All good!"
            else
                echo "Something went wrong while setting authorized keys."
            fi
        else
            echo "Something went wrong while getting authorized keys."
        fi
        echo "************************************"
    done
    echo "${count}/${total} hosts were updated."
}

###
### Main
###

trap 'cleanup' 0

distribute

exit 0
