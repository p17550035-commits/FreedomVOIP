FREEDOMVOIP BLUEPRINT V5
Tunnels Everywhere • Ephemeral Identities • Virtual Numbers • Friends & Family Mode

====================================================================
1. CORE PRINCIPLES
====================================================================

- Every device ALWAYS connects through a secure tunnel to the server.
- No direct peer-to-peer without the server.
- The server is the encrypted hub for signaling, routing, and WebRTC.
- No real device info, SIM info, or phone numbers are stored.
- All identities are ephemeral and randomly generated.
- Zero-retention: when a session ends, all state is wiped.

====================================================================
2. TUNNEL TYPES
====================================================================

A. VOIP Tunnel (everyone gets this)
- App → secure tunnel → server → secure tunnel → other app.
- Used for:
  - signaling
  - WebRTC negotiation
  - audio/video/media
  - messaging
- Always encrypted, always routed through the server.

B. Carrier Tunnel (only for masking setups)
- Wi-Fi phone → server → gov/working phone (agent app).
- Used for:
  - call forwarding
  - SIM-based dialing
  - SIM-based SMS/RCS
- Only needed when user wants to mask their real number using two phones.

====================================================================
3. USER MODES
====================================================================

A. Friends & Family Mode (normal users)
- ONE phone.
- ONE app (FreedomVOIP Client).
- VOIP tunnel only.
- No carrier tunnel, no forwarding, no dual-phone setup.
- Connects to a shared server (Raspberry Pi, laptop, home server, etc.).
- Gets:
  - secure calling
  - secure messaging
  - secure video
  - zero-retention
  - multiple virtual numbers (optional)
  - ephemeral identities

B. Dual-Phone Masking Mode (your use case)
- Wi-Fi phone:
  - runs FreedomVOIP Client.
  - uses VOIP tunnel.
  - holds multiple virtual numbers.
- Gov/working phone:
  - runs FreedomVOIP Agent.
  - uses Carrier Tunnel.
  - performs real SIM dialing/forwarding.
- Server:
  - routes between Wi-Fi phone, gov phone, and other users.
  - never stores real numbers or device info.

====================================================================
4. STANDALONE SERVER ARCHITECTURE
====================================================================

Server can run on:
- Raspberry Pi
- old laptop
- home server / NAS
- mini PC
- cloud VM
- router (if capable)
- or even a phone (for simple setups)

Server responsibilities:
- secure tunnel termination
- WebRTC signaling
- RPC control
- routing between connected devices
- ephemeral identity assignment
- virtual number mapping (in-memory only)
- zero-retention session handling

No persistent:
- user list
- device list
- call history
- message history
- logs with metadata

====================================================================
5. EPHEMERAL IDENTITY SYSTEM
====================================================================

Per connection / per call:
- App generates a random human-readable name.
- Example names:
  - "ember-wolf"
  - "quiet-river"
  - "silver-fern"
  - "midnight-sparrow"
- Server uses this name ONLY for:
  - routing
  - signaling
  - session identification

Rules:
- Name is RAM-only on the server.
- Name is not tied to:
  - IMEI, IMSI, MAC, IP, SIM, model, OS, phone number.
- When call/session ends:
  - random name deleted
  - routing entry deleted
  - ICE candidates deleted
  - SDP deleted
  - RPC state deleted
  - tunnel state deleted

Result:
- Even if someone taps the server, they see only meaningless, temporary names.
- No way to know who is who or correlate sessions.

====================================================================
6. VIRTUAL NUMBER SYSTEM
====================================================================

Each user can have 5–10 virtual numbers inside the app.

These are:
- NOT real carrier numbers.
- NOT tied to SIM.
- NOT tied to identity.
- Just internal routing identities.

Examples:
- "oak-line-01"
- "ember-dial-07"
- "silver-call-12"
- "pine-route-03"

Usage:
- User picks a virtual number when placing a call.
- App generates:
  - ephemeral device name
  - uses chosen virtual number
- Server routes using:
  - ephemeral device name
  - ephemeral virtual number

Zero-retention:
- When call ends:
  - virtual number mapping for that session is wiped from RAM.
  - no history of which virtual number was used by which person.

Server capacity:
- Easily supports:
  - 10 numbers per user
  - 10–20 users
  - 100–200 active virtual numbers
- Raspberry Pi or small Node.js server can handle this comfortably.

====================================================================
7. ROUTING SERVICE (LIGHTWEIGHT)
====================================================================

Routing table (RAM-only):
- key: ephemeral device name
- value:
  - current WebRTC session
  - current virtual number (for this session)
  - current tunnel endpoint

On connect:
- create routing entry.
- assign ephemeral name.
- associate tunnel and virtual number.

On call:
- look up target’s ephemeral name.
- route signaling and media between endpoints.

On disconnect:
- delete routing entry.
- delete ephemeral name.
- delete all session state.

No logs, no retention, no persistent mapping.

====================================================================
8. CI/CD + BUILD ARTIFACTS (SUMMARY)
====================================================================

GitHub runner builds:
- freedomvoip-client.apk
  - one-app mode for friends/family.
- freedomvoip-agent.apk
  - carrier tunnel agent for masking setups.
- freedomvoip-server.zip
  - Node.js server bundle for Pi/PC/VM.

Runner can:
- prep dependencies without building APKs initially.
- later enable full APK + server builds.
- auto-bump versions.
- auto-tag releases.
- auto-publish artifacts.
- send email notifications on success/failure.

====================================================================
END OF FREEDOMVOIP BLUEPRINT V5
====================================================================
