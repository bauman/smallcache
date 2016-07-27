#!/bin/sh

errcho(){ >&2 echo $@; }

if [[ $EUID -ne 0 ]]; then
   errcho "This script must be run as root" 1>&2
   exit 1
fi

if [[ $# -ne 3 ]]; then
   errcho "Usage: clean_cache.sh <cache dir> <size> <timeframe>" 1>&2
   exit 1
fi


CACHEDIR=$1
MAXSIZE=$2
TIMEFRAME=$3
TMPWATCHFLAGS="-msv"



FULL=$(df $CACHEDIR | tail -n1 | awk {'print $5'} | sed s/\%//)

if [[ $FULL -lt $MAXSIZE ]]; then
   errcho "$CACHEDIR is only $FULL .  Will clean when over $MAXSIZE" 1>&2
   exit 0
fi

/usr/bin/tmpwatch $TMPWATCHFLAGS $TIMEFRAME $CACHEDIR

AFTERFULL=$(df $CACHEDIR | tail -n1 | awk {'print $5'} | sed s/\%//)

if [[ $AFTERFULL -gt $MAXSIZE ]]; then
   errcho "$CACHEDIR is still $AFTERFULL .  Need a shorter timeframe, currently: $TIMEFRAME" 1>&2
   exit -1
fi