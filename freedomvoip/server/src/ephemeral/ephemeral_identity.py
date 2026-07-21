"""
Ephemeral Identity System (Blueprint v6)

Per-session random human-readable identities.
Never tied to IMEI, IMSI, MAC, IP, SIM, model, OS, or phone number.
Deleted immediately on disconnect.

Examples:
- "ember-wolf"
- "quiet-river"
- "silver-fern"

Zero retention principle: identities exist only in RAM and are purged on session end.
"""

import random
import uuid
from typing import Dict, Optional

# Adjectives for identity generation
ADJECTIVES = [
    "quiet", "silver", "golden", "swift", "bold", "calm", "bright",
    "dark", "wild", "wise", "calm", "keen", "rare", "soft", "warm",
    "cool", "fresh", "clear", "deep", "high", "low", "left", "right",
    "inner", "outer", "true", "fair", "green", "blue", "red", "amber",
    "coral", "ember", "jade", "iron", "stone", "cloud", "dawn", "dusk"
]

# Animals for identity generation
ANIMALS = [
    "wolf", "raven", "fox", "hawk", "deer", "bear", "eagle", "lynx",
    "puma", "otter", "seal", "whale", "shark", "salmon", "trout",
    "river", "stream", "stone", "tree", "owl", "swan", "crane",
    "fern", "moss", "pine", "sage", "rose", "lily", "oak", "elm",
    "maple", "cedar", "birch", "ash", "thorn", "willow", "reed"
]


class EphemeralIdentity:
    """
    Manages zero-retention ephemeral identities for sessions.
    
    Each session gets a unique random name on connect.
    Name is stored in RAM only and deleted on disconnect.
    """
    
    def __init__(self):
        """Initialize identity store (RAM only, not persisted)."""
        self._identities: Dict[str, str] = {}
        self._reverse_lookup: Dict[str, str] = {}
    
    def generate_name(self) -> str:
        """
        Generate a random human-readable ephemeral identity.
        
        Format: "{adjective}-{animal}"
        Example: "ember-wolf", "quiet-river"
        
        Returns:
            str: New random identity name
        """
        adjective = random.choice(ADJECTIVES)
        animal = random.choice(ANIMALS)
        return f"{adjective}-{animal}"
    
    def assign_to_session(self, session_id: str) -> str:
        """
        Assign a new ephemeral identity to a session.
        
        If session already has an identity, return existing one.
        Otherwise, generate new identity and store in RAM.
        
        Args:
            session_id: Unique session identifier
        
        Returns:
            str: Ephemeral identity name assigned to session
        """
        # Check if session already has identity
        if session_id in self._identities:
            return self._identities[session_id]
        
        # Generate new identity
        identity_name = self.generate_name()
        
        # Store mapping (RAM only)
        self._identities[session_id] = identity_name
        self._reverse_lookup[identity_name] = session_id
        
        return identity_name
    
    def get_identity(self, session_id: str) -> Optional[str]:
        """
        Get the ephemeral identity for a session.
        
        Args:
            session_id: Unique session identifier
        
        Returns:
            str: Ephemeral identity name, or None if not found
        """
        return self._identities.get(session_id)
    
    def get_session_from_identity(self, identity_name: str) -> Optional[str]:
        """
        Reverse lookup: get session ID from identity name.
        
        Args:
            identity_name: Ephemeral identity name
        
        Returns:
            str: Session ID, or None if not found
        """
        return self._reverse_lookup.get(identity_name)
    
    def delete_identity(self, session_id: str) -> None:
        """
        Delete an ephemeral identity on disconnect.
        
        Implements zero-retention: identity purged from RAM immediately.
        
        Args:
            session_id: Unique session identifier
        """
        identity_name = self._identities.pop(session_id, None)
        if identity_name:
            self._reverse_lookup.pop(identity_name, None)
    
    def list_active_identities(self) -> Dict[str, str]:
        """
        List all active session identities (for debugging/monitoring only).
        
        WARNING: In production, this should be restricted or disabled.
        
        Returns:
            Dict mapping session_id → identity_name
        """
        return dict(self._identities)
    
    def clear_all(self) -> None:
        """
        Clear all identities (for shutdown or testing).
        
        Implements zero-retention on server shutdown.
        """
        self._identities.clear()
        self._reverse_lookup.clear()


# Global singleton instance
_instance: Optional[EphemeralIdentity] = None


def get_ephemeral_identity() -> EphemeralIdentity:
    """
    Get or create the global EphemeralIdentity singleton.
    
    Returns:
        EphemeralIdentity: Global identity manager instance
    """
    global _instance
    if _instance is None:
        _instance = EphemeralIdentity()
    return _instance
