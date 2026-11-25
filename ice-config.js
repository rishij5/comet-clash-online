// Relay (TURN) server for phones on cellular data or strict Wi-Fi (UT, school, guest networks).
// Those networks block direct phone-to-screen connections, so traffic has to go through a relay.
// Paste your ExpressTURN username and password (expressturn.com, free tier) between the quotes.
// Leave them empty to use PeerJS's own public relays, which are often down.
window.CC_TURN = { username: '', credential: '' };
