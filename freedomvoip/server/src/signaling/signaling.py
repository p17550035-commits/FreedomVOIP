"""
Signaling Service (Blueprint v6)

WebSocket tunnel handler for encrypted hub signaling and routing.

Responsibilities:
- Tunnel termination (VOIP and CARRIER)
- RPC control message routing
- WebRTC signaling (SDP, ICE candidates)
- Session initialization on connect
- Zero-retention cleanup on disconnect

Tunnel Types (Blueprint v6 Section 2):
- VOIP Tunnel: Everyone (signaling, WebRTC, audio/video, messaging)
- CARRIER Tunnel: Dual-phone setups only (SIM dialing + forwarding)

Every message includes:
- from_identity: ephemeral device name or virtual number
- to_identity: target ephemeral device name or virtual number
- type: message type (rpc, webrtc-offer, webrtc-answer, webrtc-candidate, etc)
- payload: message data

Zero retention: messages not persisted, session data deleted on disconnect.
"""

import json
import uuid
from typing import Dict, Optional, Callable, Any
from enum import Enum
from datetime import datetime
import asyncio


class MessageType(Enum):
    """Message types handled by signaling service."""
    # Session control
    CONNECT = "connect"
    DISCONNECT = "disconnect"
    
    # RPC control messages
    RPC = "rpc"
    
    # WebRTC signaling
    WEBRTC_OFFER = "webrtc-offer"
    WEBRTC_ANSWER = "webrtc-answer"
    WEBRTC_CANDIDATE = "webrtc-candidate"
    
    # Tunnel negotiation
    TUNNEL_INIT = "tunnel-init"
    TUNNEL_ACK = "tunnel-ack"


class MessageDirection(Enum):
    """Message direction in routing."""
    INBOUND = "inbound"
    OUTBOUND = "outbound"
    ROUTED = "routed"


class SignalingMessage:
    """
    Represents a signaling message.
    
    Handled in RAM only. Never persisted.
    """
    
    def __init__(
        self,
        msg_id: str,
        msg_type: MessageType,
        from_identity: str,
        to_identity: Optional[str],
        payload: Dict[str, Any],
        direction: MessageDirection = MessageDirection.INBOUND,
        timestamp: Optional[datetime] = None
    ):
        self.msg_id = msg_id
        self.msg_type = msg_type
        self.from_identity = from_identity
        self.to_identity = to_identity
        self.payload = payload
        self.direction = direction
        self.timestamp = timestamp or datetime.utcnow()
    
    def to_json(self) -> str:
        """Serialize message to JSON (for sending over WebSocket)."""
        return json.dumps({
            "msg_id": self.msg_id,
            "type": self.msg_type.value,
            "from_identity": self.from_identity,
            "to_identity": self.to_identity,
            "payload": self.payload,
            "timestamp": self.timestamp.isoformat()
        })
    
    @staticmethod
    def from_json(json_str: str) -> Optional["SignalingMessage"]:
        """Deserialize message from JSON."""
        try:
            data = json.loads(json_str)
            msg_type = MessageType(data.get("type"))
            return SignalingMessage(
                msg_id=data.get("msg_id", str(uuid.uuid4())),
                msg_type=msg_type,
                from_identity=data.get("from_identity"),
                to_identity=data.get("to_identity"),
                payload=data.get("payload", {}),
                timestamp=datetime.fromisoformat(data.get("timestamp", datetime.utcnow().isoformat()))
            )
        except (json.JSONDecodeError, ValueError, KeyError):
            return None
    
    def to_dict(self) -> dict:
        """Convert to dict for logging (no sensitive data)."""
        return {
            "msg_id": self.msg_id,
            "type": self.msg_type.value,
            "from_identity": self.from_identity,
            "to_identity": self.to_identity,
            "direction": self.direction.value,
            "timestamp": self.timestamp.isoformat()
        }


class SignalingService:
    """
    WebSocket tunnel handler for encrypted hub signaling.
    
    Responsibilities:
    - Accept WebSocket connections (VOIP and CARRIER tunnels)
    - Initialize sessions with routing service
    - Route messages between identities
    - Handle WebRTC signaling
    - Clean up on disconnect (zero-retention)
    
    Depends on:
    - routing.RoutingService
    - ephemeral_identity.EphemeralIdentity
    """
    
    def __init__(self, routing_service, ephemeral_identity):
        """
        Initialize signaling service.
        
        Args:
            routing_service: Routing service instance
            ephemeral_identity: Ephemeral identity manager instance
        """
        self.routing = routing_service
        self.ephemeral = ephemeral_identity
        
        # Active WebSocket connections
        self._connections: Dict[str, Any] = {}  # session_id -> websocket connection
        
        # Message handlers (can be registered for custom handling)
        self._message_handlers: Dict[MessageType, Callable] = {}
        self._register_default_handlers()
    
    def _register_default_handlers(self) -> None:
        """Register default message handlers."""
        self._message_handlers[MessageType.CONNECT] = self._handle_connect
        self._message_handlers[MessageType.DISCONNECT] = self._handle_disconnect
        self._message_handlers[MessageType.RPC] = self._handle_rpc
        self._message_handlers[MessageType.WEBRTC_OFFER] = self._handle_webrtc_offer
        self._message_handlers[MessageType.WEBRTC_ANSWER] = self._handle_webrtc_answer
        self._message_handlers[MessageType.WEBRTC_CANDIDATE] = self._handle_webrtc_candidate
    
    # ====================================================================
    # Connection Management
    # ====================================================================
    
    async def handle_connection(
        self,
        websocket,
        tunnel_type: str,
        user_mode: str
    ) -> None:
        """
        Handle new WebSocket connection.
        
        Args:
            websocket: WebSocket connection object
            tunnel_type: "voip" or "carrier"
            user_mode: "friends_family" or "dual_phone"
        """
        session_id = str(uuid.uuid4())
        
        try:
            # Generate ephemeral identity
            ephemeral_name = self.ephemeral.generate_name()
            
            # Create routing session
            from routing import TunnelType, UserMode
            tunnel = TunnelType.VOIP if tunnel_type == "voip" else TunnelType.CARRIER
            mode = UserMode.FRIENDS_FAMILY if user_mode == "friends_family" else UserMode.DUAL_PHONE_MASKING
            
            session = self.routing.create_session(
                session_id=session_id,
                ephemeral_name=ephemeral_name,
                tunnel_type=tunnel,
                user_mode=mode
            )
            
            # Store connection
            self._connections[session_id] = websocket
            
            # Send connect acknowledgment
            ack = SignalingMessage(
                msg_id=str(uuid.uuid4()),
                msg_type=MessageType.TUNNEL_ACK,
                from_identity="server",
                to_identity=ephemeral_name,
                payload={
                    "session_id": session_id,
                    "ephemeral_name": ephemeral_name,
                    "tunnel_type": tunnel_type,
                    "user_mode": user_mode
                }
            )
            await websocket.send(ack.to_json())
            
            # Listen for messages
            async for message in websocket:
                await self._process_message(session_id, message, ephemeral_name)
        
        except Exception as e:
            # Log error (no sensitive data)
            pass
        
        finally:
            # Cleanup on disconnect (zero-retention)
            self._connections.pop(session_id, None)
            self.routing.delete_session(session_id)
            self.ephemeral.delete_identity(session_id)
    
    async def _process_message(
        self,
        session_id: str,
        raw_message: str,
        from_identity: str
    ) -> None:
        """
        Process incoming message.
        
        Args:
            session_id: Session ID
            raw_message: Raw WebSocket message (JSON)
            from_identity: Sender's ephemeral identity
        """
        msg = SignalingMessage.from_json(raw_message)
        if not msg:
            return
        
        # Validate sender identity
        msg.from_identity = from_identity
        
        # Route to handler
        handler = self._message_handlers.get(msg.msg_type)
        if handler:
            await handler(session_id, msg)
    
    # ====================================================================
    # Message Handlers
    # ====================================================================
    
    async def _handle_connect(self, session_id: str, msg: SignalingMessage) -> None:
        """
        Handle CONNECT message (explicit session start).
        
        Args:
            session_id: Session ID
            msg: SignalingMessage
        """
        # Session already created in handle_connection, but can be used for
        # additional setup if needed
        pass
    
    async def _handle_disconnect(self, session_id: str, msg: SignalingMessage) -> None:
        """
        Handle DISCONNECT message (explicit session end).
        
        Args:
            session_id: Session ID
            msg: SignalingMessage
        """
        # Close WebSocket connection
        websocket = self._connections.get(session_id)
        if websocket:
            await websocket.close()
    
    async def _handle_rpc(self, session_id: str, msg: SignalingMessage) -> None:
        """
        Handle RPC message (control command).
        
        Route to destination identity if specified.
        
        Args:
            session_id: Session ID
            msg: SignalingMessage
        """
        if not msg.to_identity:
            return
        
        # Lookup destination session
        dest_session = self.routing.lookup_by_identity(msg.to_identity)
        if not dest_session:
            return
        
        # Route message
        msg.direction = MessageDirection.ROUTED
        dest_websocket = self._connections.get(dest_session.session_id)
        if dest_websocket:
            await dest_websocket.send(msg.to_json())
    
    async def _handle_webrtc_offer(self, session_id: str, msg: SignalingMessage) -> None:
        """
        Handle WebRTC OFFER (SDP).
        
        Route to destination.
        
        Args:
            session_id: Session ID
            msg: SignalingMessage
        """
        await self._route_webrtc_message(msg)
    
    async def _handle_webrtc_answer(self, session_id: str, msg: SignalingMessage) -> None:
        """
        Handle WebRTC ANSWER (SDP).
        
        Route to destination.
        
        Args:
            session_id: Session ID
            msg: SignalingMessage
        """
        await self._route_webrtc_message(msg)
    
    async def _handle_webrtc_candidate(self, session_id: str, msg: SignalingMessage) -> None:
        """
        Handle WebRTC ICE CANDIDATE.
        
        Route to destination.
        
        Args:
            session_id: Session ID
            msg: SignalingMessage
        """
        await self._route_webrtc_message(msg)
    
    async def _route_webrtc_message(self, msg: SignalingMessage) -> None:
        """
        Internal: Route WebRTC message to destination.
        
        Args:
            msg: SignalingMessage
        """
        if not msg.to_identity:
            return
        
        dest_session = self.routing.lookup_by_identity(msg.to_identity)
        if not dest_session:
            return
        
        msg.direction = MessageDirection.ROUTED
        dest_websocket = self._connections.get(dest_session.session_id)
        if dest_websocket:
            await dest_websocket.send(msg.to_json())
    
    # ====================================================================
    # Statistics & Monitoring
    # ====================================================================
    
    def get_active_connections(self) -> int:
        """Get number of active WebSocket connections."""
        return len(self._connections)
    
    def stats(self) -> dict:
        """
        Get signaling statistics.
        
        Returns:
            Dict with active connections and routing stats
        """
        return {
            "active_websocket_connections": len(self._connections),
            "routing_stats": self.routing.stats()
        }


# Global singleton instance
_instance: Optional[SignalingService] = None


def get_signaling_service(routing_service=None, ephemeral_identity=None) -> SignalingService:
    """
    Get or create the global SignalingService singleton.
    
    Args:
        routing_service: Routing service instance (required for first init)
        ephemeral_identity: Ephemeral identity instance (required for first init)
    
    Returns:
        SignalingService: Global signaling instance
    """
    global _instance
    if _instance is None:
        if routing_service is None or ephemeral_identity is None:
            raise ValueError("routing_service and ephemeral_identity required for initialization")
        _instance = SignalingService(routing_service, ephemeral_identity)
    return _instance
