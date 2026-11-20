"""
NSBM EduSphere — Application Configuration
Re-exports centralized validated settings for backward compatibility
"""
from backend.core.config import Settings, AppEnvironment, get_settings

# Global instance
settings = get_settings()
