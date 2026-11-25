# Comet Clash

One-button arena dogfights for 1–8 players. Everyone flies a ship that always moves forward,
with just two controls: **TURN** and **FIRE**. Play on one keyboard, with bots, or with phones as controllers.

## Play online (GitHub Pages)

The game runs as plain static files, so it can be hosted on GitHub Pages with no server:
open the page on the TV/laptop, and it makes a room with a 4-letter code and a QR code.
Phones scan it and connect **straight to the game screen** over WebRTC (via [PeerJS](https://peerjs.com)).
The free PeerJS broker only introduces the phone and the screen. Button presses go directly between them,
on an unordered channel so one lost packet never delays the presses behind it.

To turn it on: **Settings → Pages → Deploy from a branch → `main` / root.** The game is then at
`https://<owner>.github.io/comet-clash/`. (Pages on a private repo needs a paid GitHub plan. Otherwise make the repo public.)

- On strict networks (uni, school, guest Wi-Fi) a direct connection can fail. PeerJS then falls back to its
  free relay servers, which work but add delay.
- `?peerhost=host:port` points it at your own PeerJS server instead of the public one.

## Run it locally

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

### Do I need Tailscale?

Usually not. Only the computer **hosting** a game ever needs it.

- **No Tailscale needed** to work on the code or play with keyboard and bots.
- **No Tailscale needed** to host with phones on a home Wi-Fi: `python3 server.py`, and phones scan the lobby QR code.
- **No Tailscale needed** to **join** someone else's game: phones just open their link or QR code.
- **Tailscale needed** to host with phones on a network that blocks devices from reaching each other,
  such as uni, school or guest Wi-Fi.

To set it up:

1. Install [Tailscale](https://tailscale.com/download) and sign in with your own free account.
2. Run `./play-online.sh`.

The first time, it prints a link to approve Funnel for your account. After that, the game gets its own
public `https://…ts.net` address, and the lobby QR code points phones there.

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
| `server.py` | Serves the game and relays phone input over WebSockets (standard library only). Not needed on GitHub Pages, where phones connect peer-to-peer |
| `play-online.sh` | Starts the server and shares it online with Tailscale Funnel |
| `Comet Clash.command` | Double-click launcher for macOS |
