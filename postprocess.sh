#!/bin/bash
if [ $# -eq 0 ]
    then
        echo "No arguments supplied"
        exit 1
    fi
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
API_KEY=XXXXXXX
TTBIN=$1
BASE=$(basename $TTBIN .ttbin)
ttbincnv -E -f ${TTBIN}
python3 ${DIR}/main.py ${BASE}.tcx ${BASE}.out.tcx $API_KEY
