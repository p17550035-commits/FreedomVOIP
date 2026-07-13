# FreedomVOIP Blueprint v2  
Audio + Video + Carrier Tunnel + Zero Retention + Liability Disclaimer

---

## 1. High-Level Architecture

### Components
- **FreedomVOIP Server (Core)**
  - Auth
  - RPC signaling (WebSocket)
  - WebRTC signaling (audio + video)
  - Zero-retention call state (RAM only)
  - Stateless, horizontally scalable

- **Gov Phone Agent App (Android)**
  - Connects to server
  - Receives RPC commands
  - Places carrier calls
  - WebRTC audio + video (optional)
  - Hidden SIM gateway

- **Wi‑Fi Phone Client App (Android)**
  - Dialer UI
  - WebRTC audio + video
  - RPC signaling
  - Feels like a real phone

---

## 2. Server Stack

- **Language:** TypeScript (Node.js)
- **Framework:** Fastify / Express / NestJS
- **Transport:**
  - HTTPS REST (auth)
  - WebSocket (RPC)
  - WebRTC (audio/video)
- **Infra:**
  - Postgres (users/devices only)
  - Redis (pub/sub for scaling)
  - Docker (deployment)

---

## 3. Zero-Retention Call Model

### Principles
- No call logs  
- No metadata  
- No numbers stored  
- No timestamps  
- No SDP/ICE stored  
- No RPC logs  
- No audio/video stored  
- Everything deleted immediately when call ends  

### In-memory call store

```ts
// src/calls/calls.memory.ts
export const calls: Record<string, any> = {};
