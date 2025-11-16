"""
Version tracking utility for AgentSDR
Automatically generates version numbers based on git commits
"""
import subprocess
import os
from datetime import datetime
from functools import lru_cache

class VersionTracker:
    """Tracks application version based on git commits"""

    def __init__(self):
        self.base_version = "1.0"
        self.project_name = "AgentSDR"

    @lru_cache(maxsize=1)
    def get_git_commit_count(self):
        """Get total number of git commits"""
        try:
            result = subprocess.run(
                ['git', 'rev-list', '--count', 'HEAD'],
                capture_output=True,
                text=True,
                cwd=os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            )
            if result.returncode == 0:
                return int(result.stdout.strip())
        except Exception:
            pass
        return 0

    @lru_cache(maxsize=1)
    def get_last_commit_date(self):
        """Get the date of the last commit"""
        try:
            result = subprocess.run(
                ['git', 'log', '-1', '--format=%cd', '--date=format:%Y-%m-%d %H:%M'],
                capture_output=True,
                text=True,
                cwd=os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except Exception:
            pass
        return datetime.now().strftime('%Y-%m-%d %H:%M')

    @lru_cache(maxsize=1)
    def get_last_commit_hash(self):
        """Get short hash of last commit"""
        try:
            result = subprocess.run(
                ['git', 'rev-parse', '--short', 'HEAD'],
                capture_output=True,
                text=True,
                cwd=os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except Exception:
            pass
        return "dev"

    def get_version_number(self):
        """
        Generate version number based on git commits
        Format: 1.{commit_count}
        Example: 1.0, 1.1, 1.2, etc.
        """
        commit_count = self.get_git_commit_count()
        if commit_count > 0:
            return f"1.{commit_count}"
        return self.base_version

    def get_version_info(self):
        """Get complete version information"""
        return {
            'version': self.get_version_number(),
            'date': self.get_last_commit_date(),
            'hash': self.get_last_commit_hash(),
            'project_name': self.project_name
        }

    def get_version_string(self):
        """Get formatted version string for display"""
        info = self.get_version_info()
        return f"v{info['version']} • {info['date']} • {info['hash']}"

# Global instance
version_tracker = VersionTracker()

def get_version():
    """Convenience function to get version info"""
    return version_tracker.get_version_info()

def get_version_string():
    """Convenience function to get version string"""
    return version_tracker.get_version_string()
