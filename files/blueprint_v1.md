# FreedomVOIP Blueprint v1

## 1. High-level architecture

**Components:**

- **FreedomVOIP Server (Core)**
  - Auth
  - RPC signaling (WebSocket)
  - Call/session state (in RAM only)
  - WebRTC signaling (for audio)
  - Zero retention: no call records, no logs of numbers

- **Gov Phone Agent App (Android)**
  - Connects to server
  - Listens for RPC
  - Places carrier calls
  - (Later) participates in WebRTC audio tunnel

- **Wi‑Fi Phone Client App (Android)**
  - Dialer UI
  - Connects to server
  - Sends RPC (dial/answer/hangup)
  - WebRTC for audio
  - Feels like a normal phone

---

## 2. Server stack

- **Language:** TypeScript (Node.js)
- **Framework:** Fastify or Express (or NestJS if you want structure)
- **Transport:**
  - HTTPS REST (auth, device registration)
  - WebSocket (WSS) for RPC signaling
  - WebRTC for audio (signaling via WebSocket)
- **Infra:**
  - Postgres (users, devices, tokens)
  - Redis (pub/sub for signaling between instances)
  - Docker for deployment

---

## 3. Zero-retention call model

- Call state lives **only in RAM**, never in DB.
- When call ends → state is deleted immediately.
- No call logs, no numbers stored, no metadata.

### In-memory call store

```ts
// src/calls/calls.memory.ts
export const calls: Record<string, any> = {};
