"""
Routing Service (Blueprint v6)

Lightweight RAM-only routing table for zero-retention session management.

Maps:
- ephemeral device name → session
- ephemeral virtual number → session

On connect:
- Create routing entry
- Assign ephemeral name (from ephemeral_identity module)

On call:
- Route signaling/media using ephemeral identities

On disconnect:
- Delete everything

Zero retention. Zero logs. Zero metadata.
"""

from typing import Dict, Optional, Set, List, Tuple
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import threading


class TunnelType(Enum):
    """Tunnel types per Blueprint v6 Section 2."""
    VOIP = "voip"           # Everyone (signaling, WebRTC, audio/video, messaging)
    CARRIER = "carrier"     # Dual-phone setups only (SIM dialing + forwarding)


class UserMode(Enum):
    """User modes per Blueprint v6 Section 3."""
    FRIENDS_FAMILY = "friends_family"  # One phone, one app, VOIP tunnel only
    DUAL_PHONE_MASKING = "dual_phone"  # Wi-Fi phone + gov phone, both tunnels


@dataclass
class Session:
    """
    Represents a single user session.
    
    Stored in RAM only. Deleted on disconnect.
    """
    session_id: str
    ephemeral_name: str                    # Random identity (ember-wolf, etc)
    tunnel_type: TunnelType                # VOIP or CARRIER
    user_mode: UserMode                    # Friends & Family or Dual-Phone
    virtual_numbers: Set[str] = field(default_factory=set)  # 5-10 per user
    active_calls: Set[str] = field(default_factory=set)     # Call IDs
    connected_at: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> dict:
        """Convert to dict for logging/debugging (no sensitive data)."""
        return {
            "session_id": self.session_id,
            "ephemeral_name": self.ephemeral_name,
            "tunnel_type": self.tunnel_type.value,
            "user_mode": self.user_mode.value,
            "virtual_numbers_count": len(self.virtual_numbers),
            "active_calls_count": len(self.active_calls),
            "connected_at": self.connected_at.isoformat()
        }


@dataclass
class Route:
    """
    Represents a route entry in the routing table.
    
    Maps ephemeral identity (device name or virtual number) to session.
    """
    identity: str                  # ephemeral device name or virtual number
    session_id: str                # target session
    identity_type: str             # "device" or "virtual_number"
    created_at: datetime = field(default_factory=datetime.utcnow)


class RoutingService:
    """
    Lightweight RAM-only routing table for zero-retention routing.
    
    Core responsibilities:
    - Store sessions (ephemeral_name → session data)
    - Store routes (device_name → session_id, virtual_number → session_id)
    - Support session creation/deletion
    - Support route creation/lookup/deletion
    - Implement zero-retention on disconnect
    - Thread-safe operations
    """
    
    def __init__(self):
        """Initialize routing service (RAM only, not persisted)."""
        self._sessions: Dict[str, Session] = {}
        self._routes: Dict[str, Route] = {}
        self._lock = threading.RLock()
    
    # ====================================================================
    # Session Management
    # ====================================================================
    
    def create_session(
        self,
        session_id: str,
        ephemeral_name: str,
        tunnel_type: TunnelType,
        user_mode: UserMode,
        virtual_numbers: Optional[Set[str]] = None
    ) -> Session:
        """
        Create a new session on connect.
        
        Args:
            session_id: Unique session identifier
            ephemeral_name: Random human-readable name (ember-wolf, etc)
            tunnel_type: VOIP or CARRIER
            user_mode: FRIENDS_FAMILY or DUAL_PHONE_MASKING
            virtual_numbers: 5-10 virtual numbers for user (optional)
        
        Returns:
            Session: New session object
        """
        with self._lock:
            if session_id in self._sessions:
                return self._sessions[session_id]
            
            session = Session(
                session_id=session_id,
                ephemeral_name=ephemeral_name,
                tunnel_type=tunnel_type,
                user_mode=user_mode,
                virtual_numbers=virtual_numbers or set()
            )
            
            self._sessions[session_id] = session
            
            # Create route: ephemeral_name → session_id
            self._create_route(ephemeral_name, session_id, "device")
            
            return session
    
    def get_session(self, session_id: str) -> Optional[Session]:
        """
        Get session by ID.
        
        Args:
            session_id: Unique session identifier
        
        Returns:
            Session or None if not found
        """
        with self._lock:
            return self._sessions.get(session_id)
    
    def delete_session(self, session_id: str) -> None:
        """
        Delete session on disconnect (zero-retention).
        
        Removes session and all associated routes from RAM.
        
        Args:
            session_id: Unique session identifier
        """
        with self._lock:
            session = self._sessions.pop(session_id, None)
            if not session:
                return
            
            # Remove device name route
            self._routes.pop(session.ephemeral_name, None)
            
            # Remove virtual number routes
            for vnum in session.virtual_numbers:
                self._routes.pop(vnum, None)
    
    def list_active_sessions(self) -> List[dict]:
        """
        List all active sessions (for debugging/monitoring only).
        
        WARNING: In production, this should be restricted or disabled.
        
        Returns:
            List of session dicts (no sensitive data)
        """
        with self._lock:
            return [s.to_dict() for s in self._sessions.values()]
    
    # ====================================================================
    # Route Management
    # ====================================================================
    
    def _create_route(self, identity: str, session_id: str, identity_type: str) -> None:
        """
        Internal: Create a route entry.
        
        Args:
            identity: Ephemeral device name or virtual number
            session_id: Target session ID
            identity_type: "device" or "virtual_number"
        """
        route = Route(
            identity=identity,
            session_id=session_id,
            identity_type=identity_type
        )
        self._routes[identity] = route
    
    def add_virtual_number(self, session_id: str, virtual_number: str) -> bool:
        """
        Add a virtual number route to an existing session.
        
        Args:
            session_id: Target session ID
            virtual_number: Virtual number (oak-line-01, etc)
        
        Returns:
            bool: True if added, False if session not found
        """
        with self._lock:
            session = self._sessions.get(session_id)
            if not session:
                return False
            
            session.virtual_numbers.add(virtual_number)
            self._create_route(virtual_number, session_id, "virtual_number")
            return True
    
    def remove_virtual_number(self, session_id: str, virtual_number: str) -> bool:
        """
        Remove a virtual number route from a session.
        
        Args:
            session_id: Target session ID
            virtual_number: Virtual number to remove
        
        Returns:
            bool: True if removed, False if not found
        """
        with self._lock:
            session = self._sessions.get(session_id)
            if not session:
                return False
            
            session.virtual_numbers.discard(virtual_number)
            self._routes.pop(virtual_number, None)
            return True
    
    def lookup_by_identity(self, identity: str) -> Optional[Session]:
        """
        Lookup session by ephemeral identity (device name or virtual number).
        
        This is the core routing operation.
        
        Args:
            identity: Ephemeral device name or virtual number
        
        Returns:
            Session if found, None otherwise
        """
        with self._lock:
            route = self._routes.get(identity)
            if not route:
                return None
            
            return self._sessions.get(route.session_id)
    
    def route_to_identity(self, from_identity: str, to_identity: str) -> Tuple[Optional[Session], Optional[Session]]:
        """
        Route between two identities.
        
        Returns both source and destination sessions.
        
        Args:
            from_identity: Source ephemeral identity
            to_identity: Destination ephemeral identity
        
        Returns:
            Tuple (from_session, to_session) or (None, None) if not found
        """
        with self._lock:
            from_session = self._sessions.get(self._routes.get(from_identity, Route("", "", "")).session_id)
            to_session = self._sessions.get(self._routes.get(to_identity, Route("", "", "")).session_id)
            return from_session, to_session
    
    # ====================================================================
    # Call Management
    # ====================================================================
    
    def add_active_call(self, session_id: str, call_id: str) -> bool:
        """
        Register an active call for a session.
        
        Args:
            session_id: Session ID
            call_id: Call identifier
        
        Returns:
            bool: True if added, False if session not found
        """
        with self._lock:
            session = self._sessions.get(session_id)
            if not session:
                return False
            
            session.active_calls.add(call_id)
            return True
    
    def remove_active_call(self, session_id: str, call_id: str) -> bool:
        """
        Unregister an active call (call ended).
        
        Args:
            session_id: Session ID
            call_id: Call identifier
        
        Returns:
            bool: True if removed, False if not found
        """
        with self._lock:
            session = self._sessions.get(session_id)
            if not session:
                return False
            
            session.active_calls.discard(call_id)
            return True
    
    def get_active_calls(self, session_id: str) -> Set[str]:
        """
        Get all active calls for a session.
        
        Args:
            session_id: Session ID
        
        Returns:
            Set of call IDs
        """
        with self._lock:
            session = self._sessions.get(session_id)
            return set(session.active_calls) if session else set()
    
    # ====================================================================
    # Cleanup
    # ====================================================================
    
    def clear_all(self) -> None:
        """
        Clear all sessions and routes (for shutdown or testing).
        
        Implements zero-retention on server shutdown.
        """
        with self._lock:
            self._sessions.clear()
            self._routes.clear()
    
    def stats(self) -> dict:
        """
        Get routing statistics (for monitoring only).
        
        Returns:
            Dict with session and route counts
        """
        with self._lock:
            return {
                "total_sessions": len(self._sessions),
                "total_routes": len(self._routes),
                "total_active_calls": sum(len(s.active_calls) for s in self._sessions.values())
            }


# Global singleton instance
_instance: Optional[RoutingService] = None


def get_routing_service() -> RoutingService:
    """
    Get or create the global RoutingService singleton.
    
    Returns:
        RoutingService: Global routing instance
    """
    global _instance
    if _instance is None:
        _instance = RoutingService()
    return _instance
