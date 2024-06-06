#!/usr/bin/env bash

LOGFILE="docker_stats.jsonl"
INTERVAL="60s"
echo "logging 'docker stats' every $INTERVAL to $LOGFILE..."
echo "(stop with CTRL+C)"

while true;
  do
    printf "\n" >> $LOGFILE;
    date -Iseconds >> $LOGFILE;
    docker stats --no-stream --no-trunc --format json >> $LOGFILE;
    sleep $INTERVAL;
done;
