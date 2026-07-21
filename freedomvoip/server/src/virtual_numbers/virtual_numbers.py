"""
Virtual Numbers System (Blueprint v6)

Virtual numbers are NOT real phone numbers.
They are routing identities used for privacy and organization.

Each user gets 5-10 virtual numbers:
- "oak-line-01"
- "ember-dial-07"
- "silver-call-12"

Users can:
- Assign memos ("Used for Netflix", "Used for banking")
- Pick which identity to use per call
- Keep everything organized without a contact list

Server sees only:
- ephemeral device name
- ephemeral virtual number

Memo stays local only (NOT stored on server).

Virtual Numbers are:
- Local-only
- RAM-only (zero retention)
- Routing identities only
- Never stored on server as persistent data
- Deleted on disconnect

Blueprint v6 Section 6: Routing Service
- Virtual numbers map to sessions via routing service
- On call: route signaling/media using ephemeral identities
- On disconnect: delete everything
"""

import random
from typing import Dict, Optional, Set, List
from dataclasses import dataclass, field
from datetime import datetime
import threading


# Noun pools for virtual number generation
NOUNS_FIRST = [
    "oak", "elm", "ash", "pine", "cedar", "birch", "maple", "willow",
    "sage", "fern", "moss", "coral", "jade", "ivory", "amber", "ember",
    "silver", "golden", "copper", "bronze", "steel", "iron", "stone",
    "river", "stream", "creek", "lake", "pond", "sea", "wave", "tide"
]

NOUNS_SECOND = [
    "line", "dial", "call", "ring", "bell", "signal", "wave", "pulse",
    "gate", "door", "path", "road", "way", "trail", "route", "lane",
    "link", "node", "hub", "port", "bridge", "tunnel", "channel", "flow"
]

# Number range for virtual number suffix
VIRTUAL_NUMBER_SUFFIX_MIN = 1
VIRTUAL_NUMBER_SUFFIX_MAX = 99


@dataclass
class VirtualNumber:
    """
    Represents a single virtual number.
    
    Stored in RAM only. Deleted on disconnect.
    
    Note: Memo is client-side only. Server never sees memo.
    """
    virtual_id: str                     # "oak-line-01"
    session_id: str                     # Session this number belongs to
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_used_at: Optional[datetime] = None
    call_count: int = 0                 # Number of calls through this identity
    
    def to_dict(self) -> dict:
        """Convert to dict for logging (no sensitive data, no memo)."""
        return {
            "virtual_id": self.virtual_id,
            "session_id": self.session_id,
            "created_at": self.created_at.isoformat(),
            "last_used_at": self.last_used_at.isoformat() if self.last_used_at else None,
            "call_count": self.call_count
        }


class VirtualNumberManager:
    """
    Manages virtual numbers (routing identities).
    
    Responsibilities:
    - Generate virtual numbers (oak-line-01, etc)
    - Register virtual numbers to sessions
    - Lookup sessions by virtual number
    - Track usage statistics
    - Zero-retention cleanup on disconnect
    
    Depends on:
    - routing.RoutingService (for session registration)
    
    Important:
    - Virtual numbers are NOT real phone numbers
    - Virtual numbers are routing identities only
    - Memos are ALWAYS client-side only, NEVER stored on server
    - On disconnect, all virtual numbers deleted from RAM
    """
    
    def __init__(self, routing_service):
        """
        Initialize virtual number manager.
        
        Args:
            routing_service: Routing service instance
        """
        self.routing = routing_service
        
        # Virtual numbers registry
        self._virtual_numbers: Dict[str, VirtualNumber] = {}  # virtual_id -> VirtualNumber
        
        # Session -> virtual numbers mapping
        self._session_virtual_numbers: Dict[str, Set[str]] = {}  # session_id -> set of virtual_ids
        
        self._lock = threading.RLock()
    
    # ====================================================================
    # Virtual Number Generation
    # ====================================================================
    
    def generate_virtual_number(self) -> str:
        """
        Generate a random virtual number.
        
        Format: "{noun1}-{noun2}-{number}"
        Examples: "oak-line-01", "ember-dial-07", "silver-call-12"
        
        Returns:
            str: New virtual number
        """
        noun1 = random.choice(NOUNS_FIRST)
        noun2 = random.choice(NOUNS_SECOND)
        suffix = random.randint(VIRTUAL_NUMBER_SUFFIX_MIN, VIRTUAL_NUMBER_SUFFIX_MAX)
        return f"{noun1}-{noun2}-{suffix:02d}"
    
    # ====================================================================
    # Virtual Number Registration
    # ====================================================================
    
    def register_virtual_number(self, session_id: str, virtual_id: Optional[str] = None) -> Optional[str]:
        """
        Register a virtual number to a session.
        
        If virtual_id not provided, generate a new one.
        Virtual numbers are added to routing service via add_virtual_number.
        
        Args:
            session_id: Session to register to
            virtual_id: Virtual number (optional, generated if not provided)
        
        Returns:
            str: Registered virtual number, or None if session not found
        """
        with self._lock:
            # Verify session exists in routing
            session = self.routing.get_session(session_id)
            if not session:
                return None
            
            # Generate virtual number if not provided
            if virtual_id is None:
                virtual_id = self.generate_virtual_number()
            
            # Create VirtualNumber object
            vnum = VirtualNumber(
                virtual_id=virtual_id,
                session_id=session_id
            )
            
            # Store in registry
            self._virtual_numbers[virtual_id] = vnum
            
            # Add to session mapping
            if session_id not in self._session_virtual_numbers:
                self._session_virtual_numbers[session_id] = set()
            self._session_virtual_numbers[session_id].add(virtual_id)
            
            # Register with routing service
            self.routing.add_virtual_number(session_id, virtual_id)
            
            return virtual_id
    
    def register_multiple_virtual_numbers(self, session_id: str, count: int = 5) -> List[str]:
        """
        Register multiple virtual numbers to a session at once.
        
        Used on session start to assign 5-10 numbers per user.
        
        Args:
            session_id: Session to register to
            count: Number of virtual numbers to generate (default 5, max 10)
        
        Returns:
            List of registered virtual numbers, or empty list if session not found
        """
        count = min(max(count, 1), 10)  # Clamp to 1-10
        vnums = []
        
        for _ in range(count):
            vnum = self.register_virtual_number(session_id)
            if vnum:
                vnums.append(vnum)
        
        return vnums
    
    # ====================================================================
    # Virtual Number Lookup
    # ====================================================================
    
    def get_virtual_number(self, virtual_id: str) -> Optional[VirtualNumber]:
        """
        Get virtual number details.
        
        Args:
            virtual_id: Virtual number ID (oak-line-01, etc)
        
        Returns:
            VirtualNumber object, or None if not found
        """
        with self._lock:
            return self._virtual_numbers.get(virtual_id)
    
    def get_session_virtual_numbers(self, session_id: str) -> List[str]:
        """
        Get all virtual numbers for a session.
        
        Args:
            session_id: Session ID
        
        Returns:
            List of virtual number IDs
        """
        with self._lock:
            vnums = self._session_virtual_numbers.get(session_id, set())
            return sorted(list(vnums))
    
    # ====================================================================
    # Usage Tracking
    # ====================================================================
    
    def record_virtual_number_usage(self, virtual_id: str) -> bool:
        """
        Record a call/usage event for a virtual number.
        
        Updates last_used_at and call_count.
        
        Args:
            virtual_id: Virtual number ID
        
        Returns:
            bool: True if recorded, False if not found
        """
        with self._lock:
            vnum = self._virtual_numbers.get(virtual_id)
            if not vnum:
                return False
            
            vnum.last_used_at = datetime.utcnow()
            vnum.call_count += 1
            return True
    
    def get_virtual_number_stats(self, virtual_id: str) -> Optional[dict]:
        """
        Get statistics for a virtual number.
        
        Args:
            virtual_id: Virtual number ID
        
        Returns:
            Dict with stats (created_at, last_used_at, call_count), or None
        """
        with self._lock:
            vnum = self._virtual_numbers.get(virtual_id)
            return vnum.to_dict() if vnum else None
    
    # ====================================================================
    # Cleanup
    # ====================================================================
    
    def unregister_virtual_number(self, session_id: str, virtual_id: str) -> bool:
        """
        Unregister a virtual number from a session.
        
        Args:
            session_id: Session ID
            virtual_id: Virtual number to remove
        
        Returns:
            bool: True if removed, False if not found
        """
        with self._lock:
            vnum = self._virtual_numbers.pop(virtual_id, None)
            if not vnum:
                return False
            
            if session_id in self._session_virtual_numbers:
                self._session_virtual_numbers[session_id].discard(virtual_id)
            
            # Also remove from routing
            self.routing.remove_virtual_number(session_id, virtual_id)
            return True
    
    def unregister_session_virtual_numbers(self, session_id: str) -> int:
        """
        Delete all virtual numbers for a session on disconnect (zero-retention).
        
        Args:
            session_id: Session ID
        
        Returns:
            int: Number of virtual numbers deleted
        """
        with self._lock:
            vnums = self._session_virtual_numbers.pop(session_id, set())
            count = len(vnums)
            
            for vnum in vnums:
                self._virtual_numbers.pop(vnum, None)
                # Routing service already cleaned up in delete_session
            
            return count
    
    def clear_all(self) -> None:
        """
        Clear all virtual numbers (for shutdown or testing).
        
        Implements zero-retention on server shutdown.
        """
        with self._lock:
            self._virtual_numbers.clear()
            self._session_virtual_numbers.clear()
    
    # ====================================================================
    # Statistics
    # ====================================================================
    
    def stats(self) -> dict:
        """
        Get virtual number system statistics.
        
        Returns:
            Dict with counts and usage info
        """
        with self._lock:
            total_sessions = len(self._session_virtual_numbers)
            total_vnums = len(self._virtual_numbers)
            total_calls = sum(v.call_count for v in self._virtual_numbers.values())
            
            return {
                "total_sessions_with_vnums": total_sessions,
                "total_virtual_numbers": total_vnums,
                "total_calls_through_vnums": total_calls,
                "avg_vnums_per_session": total_vnums / total_sessions if total_sessions > 0 else 0
            }


# Global singleton instance
_instance: Optional[VirtualNumberManager] = None


def get_virtual_number_manager(routing_service=None) -> VirtualNumberManager:
    """
    Get or create the global VirtualNumberManager singleton.
    
    Args:
        routing_service: Routing service instance (required for first init)
    
    Returns:
        VirtualNumberManager: Global virtual number manager instance
    """
    global _instance
    if _instance is None:
        if routing_service is None:
            raise ValueError("routing_service required for initialization")
        _instance = VirtualNumberManager(routing_service)
    return _instance
