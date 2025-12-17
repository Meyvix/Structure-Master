"""
Stracture-Master - Profile Manager Module
Manages configuration profiles for different extraction/build scenarios.
"""

import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field, asdict
from datetime import datetime

from ..config import Config, ExportFormat, LogLevel
from .logger import Logger


@dataclass
class Profile:
    """Configuration profile."""
    name: str
    description: str = ''
    created: str = field(default_factory=lambda: datetime.now().isoformat())
    modified: str = field(default_factory=lambda: datetime.now().isoformat())
    
    # Scan settings
    recursive: bool = True
    include_hidden: bool = False
    follow_symlinks: bool = False
    auto_detect_project: bool = True
    ignore_patterns: List[str] = field(default_factory=list)
    
    # Content extraction settings
    extract_content: bool = True
    include_binary_metadata: bool = True
    max_file_size_mb: float = 100.0
    
    # Export settings
    export_format: str = 'json'
    pretty_output: bool = True
    compress_output: bool = False
    encrypt_output: bool = False
    
    # Build settings
    force_overwrite: bool = False
    dry_run: bool = False
    
    # Logging
    log_level: str = 'info'
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Profile':
        # Handle unknown fields gracefully
        valid_fields = {f.name for f in cls.__dataclass_fields__.values()}
        filtered = {k: v for k, v in data.items() if k in valid_fields}
        return cls(**filtered)


class ProfileManager:
    """
    Manages configuration profiles.
    """
    
    # Default profiles
    DEFAULT_PROFILES = {
        'full': Profile(
            name='full',
            description='Full extraction with all content and metadata',
            recursive=True,
            include_hidden=True,
            extract_content=True,
            include_binary_metadata=True,
            max_file_size_mb=100.0,
            export_format='json',
            pretty_output=True,
            log_level='debug',
        ),
        'minimal': Profile(
            name='minimal',
            description='Minimal extraction - structure only, no content',
            recursive=True,
            include_hidden=False,
            extract_content=False,
            include_binary_metadata=False,
            export_format='txt',
            pretty_output=True,
            log_level='info',
        ),
        'backup': Profile(
            name='backup',
            description='Optimized for backup - compressed and encrypted',
            recursive=True,
            include_hidden=True,
            extract_content=True,
            include_binary_metadata=True,
            max_file_size_mb=500.0,
            export_format='zip',
            compress_output=True,
            encrypt_output=True,
            log_level='info',
        ),
        'security-audit': Profile(
            name='security-audit',
            description='Security-focused scan for sensitive data detection',
            recursive=True,
            include_hidden=True,
            extract_content=True,
            include_binary_metadata=False,
            export_format='json',
            pretty_output=True,
            log_level='debug',
        ),
    }
    
    def __init__(self, profiles_dir: Optional[Path] = None):
        """
        Initialize profile manager.
        
        Args:
            profiles_dir: Directory for storing profiles
        """
        self.logger = Logger.get_instance()
        self.profiles_dir = profiles_dir or Config.get_paths().profiles
        self.profiles_dir.mkdir(parents=True, exist_ok=True)
        
        # Cache for loaded profiles
        self._cache: Dict[str, Profile] = {}
        
        # Ensure default profiles exist
        self._create_default_profiles()
    
    def _create_default_profiles(self) -> None:
        """Create default profile files if they don't exist."""
        for name, profile in self.DEFAULT_PROFILES.items():
            profile_path = self.profiles_dir / f"{name}.json"
            if not profile_path.exists():
                self.save(profile)
    
    def list_profiles(self) -> List[str]:
        """List all available profile names."""
        profiles = []
        
        # Get from directory
        for file_path in self.profiles_dir.glob('*.json'):
            profiles.append(file_path.stem)
        
        return sorted(set(profiles))
    
    def get(self, name: str) -> Optional[Profile]:
        """
        Get a profile by name.
        
        Args:
            name: Profile name
            
        Returns:
            Profile or None if not found
        """
        # Check cache
        if name in self._cache:
            return self._cache[name]
        
        # Check file
        profile_path = self.profiles_dir / f"{name}.json"
        if profile_path.exists():
            profile = self.load(profile_path)
            if profile:
                self._cache[name] = profile
                return profile
        
        # Check default profiles
        if name in self.DEFAULT_PROFILES:
            return self.DEFAULT_PROFILES[name]
        
        return None
    
    def load(self, filepath: Path) -> Optional[Profile]:
        """
        Load a profile from file.
        
        Args:
            filepath: Path to profile file
            
        Returns:
            Profile or None if load failed
        """
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return Profile.from_dict(data)
        except Exception as e:
            self.logger.error(f"Failed to load profile from {filepath}: {e}")
            return None
    
    def save(self, profile: Profile, filepath: Optional[Path] = None) -> bool:
        """
        Save a profile to file.
        
        Args:
            profile: Profile to save
            filepath: Optional custom path (default: profiles_dir/name.json)
            
        Returns:
            True if saved successfully
        """
        try:
            profile.modified = datetime.now().isoformat()
            
            if filepath is None:
                filepath = self.profiles_dir / f"{profile.name}.json"
            
            filepath.parent.mkdir(parents=True, exist_ok=True)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(profile.to_dict(), f, indent=2, ensure_ascii=False)
            
            # Update cache
            self._cache[profile.name] = profile
            
            return True
        except Exception as e:
            self.logger.error(f"Failed to save profile: {e}")
            return False
    
    def create(self, name: str, base: Optional[str] = None, **kwargs) -> Profile:
        """
        Create a new profile.
        
        Args:
            name: New profile name
            base: Optional base profile to inherit from
            **kwargs: Profile settings
            
        Returns:
            New Profile
        """
        if base and base in self._cache:
            # Copy from base
            base_profile = self.get(base)
            profile_data = base_profile.to_dict() if base_profile else {}
        else:
            profile_data = {}
        
        # Override with new values
        profile_data['name'] = name
        profile_data['created'] = datetime.now().isoformat()
        profile_data['modified'] = datetime.now().isoformat()
        profile_data.update(kwargs)
        
        profile = Profile.from_dict(profile_data)
        self.save(profile)
        
        return profile
    
    def delete(self, name: str) -> bool:
        """
        Delete a profile.
        
        Args:
            name: Profile name to delete
            
        Returns:
            True if deleted successfully
        """
        profile_path = self.profiles_dir / f"{name}.json"
        
        try:
            if profile_path.exists():
                profile_path.unlink()
            
            if name in self._cache:
                del self._cache[name]
            
            return True
        except Exception as e:
            self.logger.error(f"Failed to delete profile {name}: {e}")
            return False
    
    def duplicate(self, source_name: str, new_name: str) -> Optional[Profile]:
        """
        Duplicate a profile.
        
        Args:
            source_name: Name of profile to duplicate
            new_name: Name for the new profile
            
        Returns:
            New Profile or None if source not found
        """
        source = self.get(source_name)
        if not source:
            return None
        
        return self.create(
            new_name,
            description=f"Copy of {source_name}",
            **{k: v for k, v in source.to_dict().items() 
               if k not in ('name', 'created', 'modified', 'description')}
        )
    
    def get_profile_info(self, name: str) -> Optional[Dict[str, Any]]:
        """Get profile information without loading full profile."""
        profile = self.get(name)
        if not profile:
            return None
        
        return {
            'name': profile.name,
            'description': profile.description,
            'created': profile.created,
            'modified': profile.modified,
        }
    
    def clear_cache(self) -> None:
        """Clear the profile cache."""
        self._cache.clear()


# Create singleton instance
profile_manager = ProfileManager()
