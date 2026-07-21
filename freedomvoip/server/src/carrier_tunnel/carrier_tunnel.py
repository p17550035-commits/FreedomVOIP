"""
Carrier Tunnel Service (Blueprint v6)

Handles SIM dialing and call forwarding for dual-phone masking setups.

Tunnel Type: CARRIER (only for dual-phone setups)
- Wi-Fi phone: VOIP tunnel + virtual numbers + vault
- Gov phone: carrier tunnel agent
- Server routes between both
- Full privacy bubble

Responsibilities:
- Bridge SIM calls from gov phone (agent) to WiFi phone (client)
- Forward incoming carrier calls to WiFi phone via VoIP
- Manage carrier tunnel sessions
- Handle call placement via ephemeral routing
- Implement zero-retention on disconnect

Call Flow (Outbound):
1. WiFi phone sends dial request via VOIP tunnel (virtual number + target)
2. Server routes via carrier tunnel to gov phone
3. Gov phone places actual SIM call
4. Audio streams back through carrier tunnel to WiFi phone
5. On hangup → server deletes call state

Call Flow (Inbound):
1. Incoming SIM call to gov phone number
2. Gov phone forwards via carrier tunnel to WiFi phone
3. WiFi phone rings via VoIP
4. Answer → audio streams through server
5. On hangup → server deletes call state

Zero Retention Principles:
- No call logs
- No SIM numbers stored
- No call recordings
- No SDP/ICE stored
- All state deleted on disconnect

Blueprint v6 Section 2.B: Carrier Tunnel (only masking setups)
"""

from typing import Dict, Optional, Callable, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import uuid
import threading


class CarrierCallType(Enum):
    """Types of carrier calls."""
    OUTBOUND = "outbound"  # WiFi phone initiates call via SIM
    INBOUND = "inbound"    # Incoming SIM call forwarded to WiFi phone


class CarrierCallState(Enum):
    """States of a carrier call."""
    PENDING = "pending"         # Awaiting gov phone to place call
    DIALING = "dialing"         # Gov phone actively dialing
    RINGING = "ringing"         # Call ringing on one end
    CONNECTED = "connected"     # Call active (audio flowing)
    HELD = "held"               # Call on hold
    TERMINATED = "terminated"   # Call ended


@dataclass
class CarrierCall:
    """
    Represents a single carrier call session.
    
    Stored in RAM only. Deleted on disconnect.
    """
    call_id: str                           # Unique call ID
    call_type: CarrierCallType             # Outbound or inbound
    state: CarrierCallState = CarrierCallState.PENDING
    
    # Participants
    wifi_device_identity: str              # WiFi phone ephemeral identity
    gov_device_identity: str               # Gov phone ephemeral identity
    
    # Virtual routing (no real SIM numbers stored)
    from_virtual_number: Optional[str] = None  # Virtual number used by WiFi phone
    to_virtual_number: Optional[str] = None    # Target virtual number (or SIM routing ID)
    
    # Timing
    created_at: datetime = field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None  # When audio began flowing
    ended_at: Optional[datetime] = None    # When call terminated
    
    # Call quality metrics (no sensitive data)
    duration_seconds: int = 0
    
    def to_dict(self) -> dict:
        """Convert to dict for logging (no sensitive data, no SIM numbers)."""
        return {
            "call_id": self.call_id,
            "call_type": self.call_type.value,
            "state": self.state.value,
            "wifi_device": self.wifi_device_identity,
            "gov_device": self.gov_device_identity,
            "duration_seconds": self.duration_seconds,
            "created_at": self.created_at.isoformat()
        }


class CarrierTunnelService:
    """
    Manages carrier tunnel for dual-phone masking setups.
    
    Responsibilities:
    - Accept carrier tunnel connections from gov phone (agent)
    - Route SIM calls between WiFi and gov phones
    - Manage call state (RAM-only, zero retention)
    - Bridge audio streams
    - Clean up on disconnect
    
    Depends on:
    - routing.RoutingService (for session lookup)
    - signaling.SignalingService (for message routing)
    
    Important Notes:
    - This service ONLY handles dual-phone masking setups
    - Single-phone (Friends & Family) users do NOT use carrier tunnel
    - Gov phone (agent) always initiates carrier tunnel connection
    - All SIM data is ephemeral and zero-retention
    """
    
    def __init__(self, routing_service, signaling_service):
        """
        Initialize carrier tunnel service.
        
        Args:
            routing_service: Routing service instance
            signaling_service: Signaling service instance
        """
        self.routing = routing_service
        self.signaling = signaling_service
        
        # Active carrier calls
        self._carrier_calls: Dict[str, CarrierCall] = {}  # call_id -> CarrierCall
        
        # Gov phone -> carrier calls mapping
        self._gov_device_calls: Dict[str, set] = {}  # gov_device_identity -> set of call_ids
        
        # WiFi phone -> carrier calls mapping
        self._wifi_device_calls: Dict[str, set] = {}  # wifi_device_identity -> set of call_ids
        
        # Message handlers
        self._message_handlers: Dict[str, Callable] = {}
        self._register_default_handlers()
        
        self._lock = threading.RLock()
    
    def _register_default_handlers(self) -> None:
        """Register default message handlers."""
        self._message_handlers["carrier-dial"] = self._handle_carrier_dial
        self._message_handlers["carrier-incoming"] = self._handle_carrier_incoming
        self._message_handlers["carrier-answer"] = self._handle_carrier_answer
        self._message_handlers["carrier-hangup"] = self._handle_carrier_hangup
        self._message_handlers["carrier-state-update"] = self._handle_carrier_state_update
    
    # ====================================================================
    # Outbound Call Handling (WiFi → SIM via Gov Phone)
    # ====================================================================
    
    def initiate_carrier_call(
        self,
        wifi_device_identity: str,
        gov_device_identity: str,
        from_virtual_number: str,
        to_virtual_number: str
    ) -> Optional[str]:
        """
        Initiate an outbound carrier call.
        
        WiFi phone wants to make a call via gov phone SIM.
        
        Args:
            wifi_device_identity: Calling device (ephemeral name)
            gov_device_identity: Gov phone agent (ephemeral name)
            from_virtual_number: Virtual number used by WiFi phone
            to_virtual_number: Target virtual number (routing identity)
        
        Returns:
            str: Call ID, or None if devices not found
        """
        with self._lock:
            # Verify both devices are connected
            wifi_session = self.routing.lookup_by_identity(wifi_device_identity)
            gov_session = self.routing.lookup_by_identity(gov_device_identity)
            
            if not wifi_session or not gov_session:
                return None
            
            # Create carrier call
            call_id = str(uuid.uuid4())
            call = CarrierCall(
                call_id=call_id,
                call_type=CarrierCallType.OUTBOUND,
                wifi_device_identity=wifi_device_identity,
                gov_device_identity=gov_device_identity,
                from_virtual_number=from_virtual_number,
                to_virtual_number=to_virtual_number
            )
            
            # Store call
            self._carrier_calls[call_id] = call
            
            # Track per device
            if gov_device_identity not in self._gov_device_calls:
                self._gov_device_calls[gov_device_identity] = set()
            self._gov_device_calls[gov_device_identity].add(call_id)
            
            if wifi_device_identity not in self._wifi_device_calls:
                self._wifi_device_calls[wifi_device_identity] = set()
            self._wifi_device_calls[wifi_device_identity].add(call_id)
            
            # Register call in routing
            self.routing.add_active_call(wifi_session.session_id, call_id)
            self.routing.add_active_call(gov_session.session_id, call_id)
            
            return call_id
    
    # ====================================================================
    # Inbound Call Handling (SIM → WiFi via Gov Phone)
    # ====================================================================
    
    def forward_inbound_carrier_call(
        self,
        gov_device_identity: str,
        wifi_device_identity: str,
        from_virtual_number: str,
        to_virtual_number: str
    ) -> Optional[str]:
        """
        Forward an inbound carrier call to WiFi phone.
        
        Incoming SIM call routed from gov phone to WiFi phone.
        
        Args:
            gov_device_identity: Gov phone agent (ephemeral name)
            wifi_device_identity: WiFi phone (ephemeral name)
            from_virtual_number: Caller virtual number (routing ID)
            to_virtual_number: Called virtual number (routing ID)
        
        Returns:
            str: Call ID, or None if devices not found
        """
        with self._lock:
            # Verify both devices are connected
            gov_session = self.routing.lookup_by_identity(gov_device_identity)
            wifi_session = self.routing.lookup_by_identity(wifi_device_identity)
            
            if not gov_session or not wifi_session:
                return None
            
            # Create carrier call
            call_id = str(uuid.uuid4())
            call = CarrierCall(
                call_id=call_id,
                call_type=CarrierCallType.INBOUND,
                wifi_device_identity=wifi_device_identity,
                gov_device_identity=gov_device_identity,
                from_virtual_number=from_virtual_number,
                to_virtual_number=to_virtual_number
            )
            
            # Store call
            self._carrier_calls[call_id] = call
            
            # Track per device
            if gov_device_identity not in self._gov_device_calls:
                self._gov_device_calls[gov_device_identity] = set()
            self._gov_device_calls[gov_device_identity].add(call_id)
            
            if wifi_device_identity not in self._wifi_device_calls:
                self._wifi_device_calls[wifi_device_identity] = set()
            self._wifi_device_calls[wifi_device_identity].add(call_id)
            
            # Register call in routing
            self.routing.add_active_call(gov_session.session_id, call_id)
            self.routing.add_active_call(wifi_session.session_id, call_id)
            
            return call_id
    
    # ====================================================================
    # Call State Management
    # ====================================================================
    
    def update_call_state(self, call_id: str, new_state: CarrierCallState) -> bool:
        """
        Update carrier call state.
        
        Args:
            call_id: Call ID
            new_state: New state
        
        Returns:
            bool: True if updated, False if not found
        """
        with self._lock:
            call = self._carrier_calls.get(call_id)
            if not call:
                return False
            
            call.state = new_state
            
            if new_state == CarrierCallState.CONNECTED:
                call.started_at = datetime.utcnow()
            
            return True
    
    def get_call(self, call_id: str) -> Optional[CarrierCall]:
        """
        Get carrier call details.
        
        Args:
            call_id: Call ID
        
        Returns:
            CarrierCall or None if not found
        """
        with self._lock:
            return self._carrier_calls.get(call_id)
    
    def end_call(self, call_id: str) -> bool:
        """
        End a carrier call (zero-retention cleanup).
        
        Args:
            call_id: Call ID
        
        Returns:
            bool: True if ended, False if not found
        """
        with self._lock:
            call = self._carrier_calls.pop(call_id, None)
            if not call:
                return False
            
            # Calculate duration
            if call.started_at:
                call.ended_at = datetime.utcnow()
                call.duration_seconds = int((call.ended_at - call.started_at).total_seconds())
            
            # Remove from device call lists
            self._gov_device_calls[call.gov_device_identity].discard(call_id)
            self._wifi_device_calls[call.wifi_device_identity].discard(call_id)
            
            # Remove from routing active calls
            gov_session = self.routing.lookup_by_identity(call.gov_device_identity)
            wifi_session = self.routing.lookup_by_identity(call.wifi_device_identity)
            
            if gov_session:
                self.routing.remove_active_call(gov_session.session_id, call_id)
            if wifi_session:
                self.routing.remove_active_call(wifi_session.session_id, call_id)
            
            return True
    
    # ====================================================================
    # Message Handlers
    # ====================================================================
    
    async def _handle_carrier_dial(self, msg: Dict[str, Any]) -> None:
        """
        Handle CARRIER-DIAL message (WiFi phone initiates SIM call).
        
        Args:
            msg: Message payload
        """
        call_id = self.initiate_carrier_call(
            wifi_device_identity=msg.get("from_device"),
            gov_device_identity=msg.get("to_device"),
            from_virtual_number=msg.get("from_virtual_number"),
            to_virtual_number=msg.get("to_virtual_number")
        )
        # Further RPC handling delegated to signaling service
    
    async def _handle_carrier_incoming(self, msg: Dict[str, Any]) -> None:
        """
        Handle CARRIER-INCOMING message (inbound SIM call forwarded).
        
        Args:
            msg: Message payload
        """
        call_id = self.forward_inbound_carrier_call(
            gov_device_identity=msg.get("from_device"),
            wifi_device_identity=msg.get("to_device"),
            from_virtual_number=msg.get("from_virtual_number"),
            to_virtual_number=msg.get("to_virtual_number")
        )
        # Further RPC handling delegated to signaling service
    
    async def _handle_carrier_answer(self, msg: Dict[str, Any]) -> None:
        """
        Handle CARRIER-ANSWER message (call answered).
        
        Args:
            msg: Message payload
        """
        call_id = msg.get("call_id")
        self.update_call_state(call_id, CarrierCallState.CONNECTED)
    
    async def _handle_carrier_hangup(self, msg: Dict[str, Any]) -> None:
        """
        Handle CARRIER-HANGUP message (call terminated).
        
        Args:
            msg: Message payload
        """
        call_id = msg.get("call_id")
        self.end_call(call_id)
    
    async def _handle_carrier_state_update(self, msg: Dict[str, Any]) -> None:
        """
        Handle CARRIER-STATE-UPDATE message (call state change).
        
        Args:
            msg: Message payload
        """
        call_id = msg.get("call_id")
        state_str = msg.get("state")
        
        try:
            state = CarrierCallState(state_str)
            self.update_call_state(call_id, state)
        except ValueError:
            pass
    
    # ====================================================================
    # Cleanup
    # ====================================================================
    
    def cleanup_device_calls(self, device_identity: str) -> int:
        """
        Clean up all calls for a device on disconnect (zero-retention).
        
        Args:
            device_identity: Device ephemeral identity
        
        Returns:
            int: Number of calls cleaned up
        """
        with self._lock:
            count = 0
            
            # Clean gov phone calls
            gov_calls = self._gov_device_calls.pop(device_identity, set()).copy()
            for call_id in gov_calls:
                if self.end_call(call_id):
                    count += 1
            
            # Clean WiFi phone calls
            wifi_calls = self._wifi_device_calls.pop(device_identity, set()).copy()
            for call_id in wifi_calls:
                if self.end_call(call_id):
                    count += 1
            
            return count
    
    def clear_all(self) -> None:
        """
        Clear all carrier calls (for shutdown or testing).
        
        Implements zero-retention on server shutdown.
        """
        with self._lock:
            self._carrier_calls.clear()
            self._gov_device_calls.clear()
            self._wifi_device_calls.clear()
    
    # ====================================================================
    # Statistics
    # ====================================================================
    
    def stats(self) -> dict:
        """
        Get carrier tunnel statistics.
        
        Returns:
            Dict with call counts and states
        """
        with self._lock:
            by_state = {}
            for call in self._carrier_calls.values():
                state = call.state.value
                by_state[state] = by_state.get(state, 0) + 1
            
            return {
                "total_active_calls": len(self._carrier_calls),
                "calls_by_state": by_state,
                "total_gov_devices": len(self._gov_device_calls),
                "total_wifi_devices": len(self._wifi_device_calls)
            }


# Global singleton instance
_instance: Optional[CarrierTunnelService] = None


def get_carrier_tunnel_service(routing_service=None, signaling_service=None) -> CarrierTunnelService:
    """
    Get or create the global CarrierTunnelService singleton.
    
    Args:
        routing_service: Routing service instance (required for first init)
        signaling_service: Signaling service instance (required for first init)
    
    Returns:
        CarrierTunnelService: Global carrier tunnel instance
    """
    global _instance
    if _instance is None:
        if routing_service is None or signaling_service is None:
            raise ValueError("routing_service and signaling_service required for initialization")
        _instance = CarrierTunnelService(routing_service, signaling_service)
    return _instance
