#!/bin/bash

PID_FILE="crawler.pid"
LOG_FILE="crawler.log"
SPIDER_SCRIPT="crawler/async_spider.py"

start() {
    if [ -f "$PID_FILE" ] && kill -0 $(cat "$PID_FILE") 2>/dev/null; then
        echo "Crawler daemon is already running (PID: $(cat $PID_FILE))."
    else
        echo "Starting Cognicore Crawler Daemon..."
        # Set PYTHONPATH so crawler/async_spider.py can import indexer modules without path errors
        PYTHONPATH=. nohup python -u "$SPIDER_SCRIPT" > "$LOG_FILE" 2>&1 &
        echo $! > "$PID_FILE"
        echo "Crawler started with PID $(cat $PID_FILE). Logs writing to $LOG_FILE"
    fi
}

stop() {
    if [ -f "$PID_FILE" ]; then
        PID=$(cat $PID_FILE)
        echo "Stopping Crawler daemon (PID: $PID)..."
        kill $PID 2>/dev/null
        rm -f "$PID_FILE"
        echo "Crawler stopped."
    else
        echo "Crawler daemon is not currently running."
    fi
}

status() {
    if [ -f "$PID_FILE" ] && kill -0 $(cat "$PID_FILE") 2>/dev/null; then
        echo "Crawler is RUNNING (PID: $(cat $PID_FILE))"
    else
        echo "Crawler is STOPPED."
        [ -f "$PID_FILE" ] && rm -f "$PID_FILE"
    fi
}

case "$1" in
    start) start ;;
    stop) stop ;;
    status) status ;;
    *) echo "Usage: $0 {start|stop|status}" ;;
esac
