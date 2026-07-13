# FreedomVOIP Blueprint v3  
Audio + Video + Carrier Tunnel + Zero Retention + Security Modes + Invite System + Distribution + Liability Disclaimer

====================================================================
1. HIGH-LEVEL ARCHITECTURE
====================================================================

Components:
- FreedomVOIP Server (Core)
  - Auth
  - RPC signaling (WebSocket)
  - WebRTC signaling (audio + video)
  - Zero-retention call state (RAM only)
  - Stateless, horizontally scalable

- Gov Phone Agent App (Android)
  - Connects to server
  - Receives RPC commands
  - Places carrier calls
  - WebRTC audio + video (optional)
  - Hidden SIM gateway

- Wi‑Fi Phone Client App (Android)
  - Dialer UI
  - WebRTC audio + video
  - RPC signaling
  - Feels like a real phone

====================================================================
2. SERVER STACK
====================================================================

- Language: TypeScript (Node.js)
- Framework: Fastify / Express / NestJS
- Transport:
  - HTTPS REST (auth)
  - WebSocket (RPC)
  - WebRTC (audio/video)
- Infra:
  - Postgres (users/devices only)
  - Redis (pub/sub for scaling)
  - Docker (deployment)

====================================================================
3. ZERO-RETENTION CALL MODEL
====================================================================

Principles:
- No call logs
- No metadata
- No numbers stored
- No timestamps
- No SDP/ICE stored
- No RPC logs
- No audio/video stored
- Everything deleted immediately when call ends

In-memory call store:
export const calls: Record<string, any> = {};

Call service:
export function createCall(call_id: string, data: any) { calls[call_id] = data; }
export function updateCall(call_id: string, updates: any) { if (!calls[call_id]) return; Object.assign(calls[call_id], updates); }
export function endCall(call_id: string) { delete calls[call_id]; }

Logging policy:
- Log ONLY: server startup, fatal errors (no sensitive data)
- NEVER log: numbers, call IDs, SDP, ICE, RPC payloads, audio/video

====================================================================
4. RPC MESSAGE SCHEMA (WebSocket JSON)
====================================================================

Core RPC:
{ "type": "dial", "call_id": "abc123", "number": "+15551234567", "from_device": "wifi-123", "to_device": "gov-456" }
{ "type": "incoming", "call_id": "xyz789", "number": "+15559876543", "from_device": "gov-456", "to_device": "wifi-123" }
{ "type": "answer", "call_id": "xyz789", "from_device": "wifi-123" }
{ "type": "hangup", "call_id": "abc123", "from_device": "wifi-123" }

WebRTC Signaling (Audio + Video):
{ "type": "webrtc-offer", "call_id": "abc123", "from_device": "wifi-123", "sdp": "..." }
{ "type": "webrtc-answer", "call_id": "abc123", "from_device": "gov-456", "sdp": "..." }
{ "type": "webrtc-candidate", "call_id": "abc123", "from_device": "wifi-123", "candidate": "..." }

Video toggle (optional):
{ "type": "enable-video", "call_id": "abc123", "from_device": "wifi-123" }

====================================================================
5. SERVER FILE TREE
====================================================================

freedomvoip-server/
  package.json
  tsconfig.json
  src/
    index.ts
    config/
      env.ts
    core/
      logger.ts
      errors.ts
    auth/
      auth.controller.ts
      auth.service.ts
      auth.middleware.ts
      auth.types.ts
    devices/
      devices.controller.ts
      devices.service.ts
      devices.types.ts
    signaling/
      ws.server.ts
      rpc.router.ts
      rpc.handlers/
        dial.handler.ts
        incoming.handler.ts
        answer.handler.ts
        hangup.handler.ts
        webrtc-offer.handler.ts
        webrtc-answer.handler.ts
        webrtc-candidate.handler.ts
        enable-video.handler.ts
    calls/
      calls.memory.ts
      calls.service.ts
      calls.types.ts
    webrtc/
      signaling.service.ts
    db/
      db.ts
      migrations/
        001_init.sql
    redis/
      redis.ts

====================================================================
6. GOV PHONE AGENT APP (ANDROID)
====================================================================

Responsibilities:
- Maintain WebSocket connection
- Handle RPC (dial/answer/hangup)
- Place carrier calls
- WebRTC audio + video
- Call state listener

File Tree:
freedomvoip-agent-android/
  app/
    src/
      main/
        AndroidManifest.xml
        java/com/freedomvoip/agent/
          AgentApp.kt
          WebSocketClient.kt
          RpcHandler.kt
          CallController.kt
          CallStateListener.kt
          WebRtcClient.kt

====================================================================
7. WI-FI PHONE CLIENT APP (ANDROID)
====================================================================

Responsibilities:
- Dialer UI
- Incoming call UI
- WebRTC audio + video
- RPC signaling

File Tree:
freedomvoip-client-android/
  app/
    src/
      main/
        AndroidManifest.xml
        java/com/freedomvoip/client/
          ClientApp.kt
          WebSocketClient.kt
          RpcClient.kt
          DialerActivity.kt
          CallActivity.kt
          WebRtcClient.kt

====================================================================
8. CALL FLOWS
====================================================================

Outbound (Wi‑Fi → Carrier via gov phone):
1. Wi‑Fi phone sends dial RPC.
2. Server routes to gov phone.
3. Gov phone places carrier call.
4. WebRTC audio + video tunnel established.
5. On hangup → server deletes call state.

Inbound (Carrier → Wi‑Fi via forwarding):
1. Carrier forwards gov number → FreedomVOIP number.
2. Wi‑Fi phone rings via VoIP.
3. WebRTC audio/video.
4. On hangup → server deletes call state.

====================================================================
9. BUILD ORDER
====================================================================

1. Server skeleton
2. RPC router
3. Gov agent stub
4. Wi‑Fi client stub
5. Telephony integration
6. Zero-retention call state
7. WebRTC signaling
8. Audio tunnel
9. Video track
10. UI polish
11. Error handling + reconnection

====================================================================
10. SECURITY MODES (INTEROPERABILITY)
====================================================================

Secure Modes (FreedomVOIP → FreedomVOIP):
- FreedomVOIP Call (Secure)
- FreedomVOIP Video (Secure)
- FreedomVOIP Chat (Secure)

Non-Secure Modes (External Apps):
- Normal Phone Call (Carrier)
- System Messages (SMS/RCS)
- External Video Apps

Warning:
"This call/video/message is NOT using FreedomVOIP encryption. Carriers or app providers may log metadata or content."

====================================================================
11. DISTRIBUTION MODEL (NO GOOGLE PLAY)
====================================================================

Primary distribution channels:
1. GitHub Releases (APK)
2. F‑Droid (if approved)
3. Self-hosted F‑Droid repo (fallback)

Distribution URLs:
https://github.com/FreedomVOIP/FreedomVOIP/releases
https://f-droid.org/packages/com.freedomvoip.client/
https://repo.freedomvoip.app/fdroid/repo

====================================================================
12. INVITE / SHARE FEATURE
====================================================================

Share link format:
https://github.com/FreedomVOIP/FreedomVOIP
https://f-droid.org/packages/com.freedomvoip.client/
freedomvoip://invite?ref=<device_id>

Behavior:
- Opens GitHub or F‑Droid page
- Opens app directly if installed
- Shows “Join FreedomVOIP” screen
- Explains secure vs non-secure modes

Security:
- No sensitive data
- Optional referral ID only
- No numbers, metadata, or retention

====================================================================
13. LIABILITY DISCLAIMER
====================================================================

FreedomVOIP is provided “AS IS” without any warranty of any kind, express or implied.
Use at your own risk.

The developers and contributors assume no liability for:
- data loss
- service interruption
- call failures
- misconfiguration
- misuse
- security breaches caused by user behavior
- carrier restrictions or changes

FreedomVOIP is a privacy-focused communication tool.
It is NOT a replacement for emergency services.

By using this software, you agree that you are solely responsible for your own actions,
configuration, and compliance with local laws.

====================================================================
END OF FREEDOMVOIP BLUEPRINT v3
====================================================================
