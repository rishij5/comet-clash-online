# Comet Clash

One-button arena dogfights for 1–8 players. Everyone flies a ship that always moves forward,
with just two controls: **TURN** and **FIRE**. Play on one keyboard, with bots, or with phones as controllers.

## Run it

You only need Python 3 (already on macOS).

```bash
python3 server.py
```

Then open http://localhost:8765. Without the server, you can also open `index.html`
directly for keyboard-only play.

- **Mac shortcut:** double-click `Comet Clash.command`. It starts the server and opens the game.
- **Phones on any network:** `./play-online.sh` shares the game through
  [Tailscale Funnel](https://tailscale.com/kb/1223/funnel). This needs Tailscale installed and signed in.
  Without it, phones must be on the same Wi-Fi.

## Controls

| Player | Turn | Fire |
|---|---|---|
| Red | Q | W |
| Blue | B | N |
| Green | O | P |
| Gold | ← | ↑ |

- **Join:** press your TURN key in the lobby.
- **Add a bot:** click a slot.
- **Rebind a key:** click a key cap.
- **Phones:** scan the QR code in the lobby.

**In a match**

- **Hold TURN** to rotate. **Tap FIRE** to shoot: 3 shots that reload automatically.
- **Double-tap TURN** to dash.
- **If your ship is destroyed,** your pilot ejects. Survive 5 s to get a new ship.

**Other keys**

- **`` ` ``:** opens the tuning panel.
- **Esc:** pauses.

## Files

| File | What it is |
|---|---|
| `index.html` | The game: lobby, gameplay, bots, rendering |
| `pad.html` | Phone controller page |
| `server.py` | Serves the game and relays phone input over WebSockets (standard library only) |
| `play-online.sh` | Starts the server and shares it online with Tailscale Funnel |
| `Comet Clash.command` | Double-click launcher for macOS |
