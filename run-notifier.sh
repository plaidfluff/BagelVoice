#!/bin/sh

PIDFILE=`dirname $0`/logs/notifier.pid
if ! [ -f "$PIDFILE" ] || ! kill -0 `cat "$PIDFILE"` > /dev/null 2>&1 ; then
    ./notifier.py &
    echo $! > "$PIDFILE"
fi
