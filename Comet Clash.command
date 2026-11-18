#!/bin/bash
# Double-click to play: starts Tailscale + the game server and opens the game.
# Close this Terminal window (or press Ctrl+C) to stop the server and switch Funnel off.
cd "$(dirname "$0")"
exec ./play-online.sh
