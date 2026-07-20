# FreedomVOIP — Agent Build Instructions (v6)

## 1. Purpose
You are generating the initial codebase for the FreedomVOIP project.
Follow the folder tree exactly. Do not create new folders unless explicitly stated.
Do not rename folders. Do not flatten structure.

FreedomVOIP consists of:
- Android client module
- Android agent module
- Python server module

Blueprints are located in /freedomvoip/docs/.
Use them as the authoritative specification.

---

## 2. Folder Tree Rules
Place files ONLY in these locations:

### Client (Android)
freedomvoip/client/app/src/main/java/com/freedomvoip/client/ui/
freedomvoip/client/app/src/main/java/com/freedomvoip/client/voip/
freedomvoip/client/app/src/main/java/com/freedomvoip/client/tunnel/
freedomvoip/client/app/src/main/java/com/freedomvoip/client/identity/
freedomvoip/client/app/src/main/java/com/freedomvoip/client/config/

### Agent (Android)
freedomvoip/client/agent/src/main/java/com/freedomvoip/agent/

### Server (Python)
freedomvoip/server/src/signaling/
freedomvoip/server/src/routing/
freedomvoip/server/src/ephemeral/
freedomvoip/server/src/virtual_numbers/
freedomvoip/server/src/carrier_tunnel/

Do not place files anywhere else.

---

## 3. Android Client Requirements
Generate Kotlin code for:

### UI
- Basic placeholder Activity (FreedomVoipActivity)
- Minimal UI for call connect/disconnect
- Status indicators

### VoIP Engine
- VoipEngine.kt (stub)
- VoipController.kt (stub)
- VoipConfig.kt (basic config class)

### Tunnel
- TunnelManager.kt (stub)
- TunnelSession.kt (stub)

### Identity
- EphemeralIdentity.kt (random human-readable names)
- IdentityManager.kt (stub)

### Config
- ClientConfig.kt (stub)

All classes must be simple, compilable placeholders.

---

## 4. Android Agent Requirements
Generate Kotlin code for:

- AgentBootstrap.kt
- AgentConfig.kt
- AgentTaskRunner.kt

These are placeholders for future automation.

---

## 5. Python Server Requirements
Generate Python files:

### signaling/
- signaling.py (stub)

### routing/
- routing.py (stub)

### ephemeral/
- ephemeral_identity.py (stub)

### virtual_numbers/
- virtual_numbers.py (stub)

### carrier_tunnel/
- carrier_tunnel.py (stub)

Server must run with:
python3 server.py

Generate server.py in /freedomvoip/server/.

---

## 6. Behavior Rules
- Do NOT generate full implementations.
- Do NOT add external dependencies.
- Do NOT create new folders.
- Do NOT rename anything.
- Do NOT generate UI layouts unless asked.
- Do NOT generate Gradle files unless asked.
- Keep everything minimal and compilable.

---

## 7. Output Format
When generating code:
- Create files directly in the correct folders.
- Do not output code in chat unless asked.
- Do not create duplicate files.
- Do not overwrite existing files unless instructed.

---

## 8. Start
Begin by generating placeholder Kotlin and Python files according to the rules above.
