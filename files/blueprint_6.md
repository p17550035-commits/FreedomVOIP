FREEDOMVOIP — BLUEPRINT v6 (FINALIZED)
Future Add‑Ons Included at Top (as requested)

========================================================
FUTURE ADD‑ONS (NOT IMPLEMENTED YET — PLANNED FEATURES)
========================================================
- Identity Vault (per‑website bundles: unique email, password, alias, virtual number)
- Fingerprint unlock for vault + virtual numbers tab
- PIN fallback (6–8 digits)
- Master password fallback (bypasses fingerprint/PIN)
- Local‑only encryption (no cloud, no master crypto key, no catastrophic failure mode)
- Export/import (local only, encrypted)
- Per‑identity encryption (lose one identity = lose one identity, not entire vault)
- Vault integrates directly with the Virtual Numbers tab for organization

========================================================
1. CORE PRINCIPLES
========================================================
- Every device ALWAYS tunnels to the server.
- No direct peer‑to‑peer connections.
- Server acts as the encrypted hub for signaling + routing.
- Zero retention: all session data wiped immediately on disconnect.
- Ephemeral identities: random human‑readable names per session.
- Virtual numbers: 5–10 per user, stored locally only.
- Memo tab: lets users label each virtual number without storing contacts.
- No cloud storage, no subscriptions, no master crypto key.

========================================================
2. TUNNEL TYPES
========================================================

A. VOIP Tunnel (everyone)
- App → secure tunnel → server → secure tunnel → other app.
- Handles signaling, WebRTC, audio/video, messaging.
- Mandatory for all users.

B. Carrier Tunnel (only masking setups)
- Wi‑Fi phone → server → gov/working phone (agent app).
- Handles SIM dialing + forwarding.
- Only needed for dual‑phone setups.

========================================================
3. USER MODES
========================================================

A. Friends & Family Mode (one app)
- One phone.
- One app.
- VOIP tunnel only.
- Virtual numbers + memo tab.
- Ephemeral identities.
- Zero retention.
- Fingerprint/PIN/master‑password unlock for identity tab.

B. Dual‑Phone Masking Mode (your setup)
- Wi‑Fi phone: VOIP tunnel + virtual numbers + vault.
- Gov phone: carrier tunnel agent.
- Server routes between both.
- Full privacy bubble.

========================================================
4. STANDALONE SERVER
========================================================
Runs on:
- Raspberry Pi
- laptop
- home server
- mini PC
- cloud VM
- router (if capable)
- or even a phone

Server handles:
- tunnel termination
- WebRTC signaling
- RPC control
- routing
- ephemeral identity assignment
- virtual number mapping (RAM only)
- zero‑retention session handling

No persistent:
- user list
- device list
- call history
- message history
- metadata logs

========================================================
5. EPHEMERAL IDENTITY SYSTEM
========================================================
Per call/session:
- App generates random human‑readable name.
- Server uses it for routing.
- Deleted on disconnect.

Examples:
- “ember‑wolf”
- “quiet‑river”
- “silver‑fern”

Never tied to:
- IMEI, IMSI, MAC, IP, SIM, model, OS, phone number.

========================================================
6. VIRTUAL NUMBER SYSTEM
========================================================
Each user gets 5–10 virtual numbers:
- “oak‑line‑01”
- “ember‑dial‑07”
- “silver‑call‑12”

These are NOT real numbers.
They’re routing identities.

Users can:
- assign memos (“Used for Netflix”, “Used for banking”)
- pick which identity to use per call
- keep everything organized without a contact list

Server sees only:
- ephemeral device name
- ephemeral virtual number

Memo stays local only.

========================================================
7. ROUTING SERVICE (LIGHTWEIGHT)
========================================================
RAM‑only routing table:
- ephemeral device name → session
- ephemeral virtual number → session

On connect:
- create routing entry
- assign ephemeral name

On call:
- route signaling/media using ephemeral identities

On disconnect:
- delete everything

Zero retention.
Zero logs.
Zero metadata.

========================================================
8. SECURITY MODEL (v6 UPDATE)
========================================================
Unlock Options:
- Fingerprint unlock (preferred)
- PIN fallback (6–8 digits)
- Master password fallback (bypasses fingerprint/PIN)

Why this is perfect:
- No single master key
- No catastrophic failure mode
- No cloud recovery
- No subscription
- No lock‑in
- No losing everything if one key is lost
- Works on phones without fingerprint scanners

========================================================
9. CI/CD + BUILD ARTIFACTS
========================================================
GitHub runner builds:
- freedomvoip-client.apk
- freedomvoip-agent.apk
- freedomvoip-server.zip

Runner supports:
- dependency prep
- version bump
- release automation
- artifact publishing

========================================================
10. FUTURE EXPANSION (IDENTITY VAULT)
========================================================
Will include:
- per‑website identity bundles
- unique email generator
- unique password generator
- unique alias generator
- virtual number assignment
- fingerprint/PIN/master‑password unlock
- local encryption
- no cloud
- no subscription
- no master key failure mode

========================================================
END OF FREEDOMVOIP BLUEPRINT v6 (FINAL)
========================================================
