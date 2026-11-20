#!/bin/bash
# Start Comet Clash, share it over the internet with Tailscale Funnel (works on uni/guest
# Wi-Fi), and open the game in your browser. Safe to run again while it's already running.
#   ./play-online.sh            (or double-click "Comet Clash.command")
cd "$(dirname "$0")"
PORT="${PORT:-8765}"
GAME="http://localhost:$PORT"
TS="$(command -v tailscale || echo /Applications/Tailscale.app/Contents/MacOS/Tailscale)"

port_busy() { ! python3 -c "import socket,sys; s=socket.socket(); s.bind(('0.0.0.0', int(sys.argv[1])))" "$PORT" 2>/dev/null; }
open_game() { (sleep "${1:-0}"; open "$GAME") & }

# Already running? Just bring the game up again.
if port_busy; then
  if curl -fs --max-time 2 "$GAME/" | grep -q "Comet Clash"; then
    echo "Comet Clash is already running, opening it."
    open_game
    exit 0
  fi
  echo "Port $PORT is used by something else. Stop it, or run:  PORT=9000 ./play-online.sh"
  exit 1
fi

# Bring Tailscale up (start the app if it's closed), then switch on Funnel.
HOST=""
if [ -x "$TS" ]; then
  get_host() { "$TS" status --json 2>/dev/null | python3 -c 'import json,sys; d=json.load(sys.stdin); print(d["Self"]["DNSName"].rstrip(".") if d.get("BackendState")=="Running" else "")' 2>/dev/null; }
  HOST="$(get_host)"
  if [ -z "$HOST" ] && [ -d /Applications/Tailscale.app ]; then
    echo "Starting Tailscale…"
    open -g -a Tailscale
    sleep 2
    "$TS" up --timeout 15s >/dev/null 2>&1 || true   # reconnect if it was switched off (uses your existing sign-in)
    for _ in $(seq 1 20); do HOST="$(get_host)"; [ -n "$HOST" ] && break; sleep 1; done
  fi
fi

if [ -n "$HOST" ]; then
  echo "Turning on Tailscale Funnel for port $PORT…"
  if "$TS" funnel --bg "$PORT"; then
    trap '"$TS" funnel --https=443 off >/dev/null 2>&1; echo "Funnel turned off."' EXIT
    export PUBLIC_URL="https://$HOST"
  else
    echo "Couldn't switch on Funnel, so phones will need to be on the same Wi-Fi."
  fi
else
  echo "Tailscale isn't installed or signed in, so phones will need to be on the same Wi-Fi."
fi

open_game 1.5
PORT="$PORT" python3 server.py
