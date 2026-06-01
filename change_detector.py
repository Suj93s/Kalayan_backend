"""Smart update detection using content hashing."""

import json
import hashlib
from pathlib import Path
from typing import Dict, Optional


class ChangeDetector:
    """Detects if website content has changed using SHA256 hashing."""
    
    def __init__(self, state_file: str = ".update_state.json"):
        self.state_file = Path(state_file)
        self.state = self._load_state()
    
    def _load_state(self) -> Dict:
        """Load previous state from file."""
        if self.state_file.exists():
            try:
                with open(self.state_file, 'r') as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}
    
    def _save_state(self) -> None:
        """Save current state to file."""
        with open(self.state_file, 'w') as f:
            json.dump(self.state, f, indent=2)
    
    def compute_hash(self, content: str) -> str:
        """Compute SHA256 hash of content."""
        return hashlib.sha256(content.encode()).hexdigest()
    
    def has_changed(self, website_key: str, content: str) -> bool:
        """
        Check if content has changed for a website.
        Returns True if content is new or has changed.
        """
        new_hash = self.compute_hash(content)
        old_hash = self.state.get(f"{website_key}_hash")
        
        if old_hash is None:
            # First time seeing this website
            return True
        
        return new_hash != old_hash
    
    def update_hash(self, website_key: str, content: str) -> None:
        """Update stored hash for a website."""
        new_hash = self.compute_hash(content)
        self.state[f"{website_key}_hash"] = new_hash
        self.state[f"{website_key}_updated"] = self._get_timestamp()
        self._save_state()
    
    def _get_timestamp(self) -> str:
        """Get current ISO timestamp."""
        from datetime import datetime
        return datetime.utcnow().isoformat()
    
    def get_last_update(self, website_key: str) -> Optional[str]:
        """Get timestamp of last update for a website."""
        return self.state.get(f"{website_key}_updated")
