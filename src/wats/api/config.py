# WATS_Project/wats_app/api/config.py

"""
Configuration for the recording upload API system.
"""

import logging
from typing import Any, Dict


class ApiConfig:
    """Configuration for the upload API."""

    def __init__(self, config_data: Dict[str, Any]):
        """
        Initialize API configuration from config data.

        Args:
            config_data: Dictionary containing API configuration
        """
        api_config = config_data.get("api", {})

        # API endpoint settings
        self.ENABLED: bool = api_config.get("enabled", False)
        self.BASE_URL: str = api_config.get("base_url", "")
        self.API_TOKEN: str = api_config.get("api_token", "")

        # Upload settings
        self.AUTO_UPLOAD: bool = api_config.get("auto_upload", False)
        self.UPLOAD_TIMEOUT: int = api_config.get("upload_timeout", 60)
        self.MAX_RETRIES: int = api_config.get("max_retries", 3)
        self.MAX_CONCURRENT_UPLOADS: int = api_config.get("max_concurrent_uploads", 2)

        # File management
        self.DELETE_AFTER_UPLOAD: bool = api_config.get("delete_after_upload", False)
        self.UPLOAD_OLDER_RECORDINGS: bool = api_config.get("upload_older_recordings", True)
        self.MAX_FILE_AGE_DAYS: int = api_config.get("max_file_age_days", 30)

        # Progress and monitoring
        self.PROGRESS_CALLBACK_ENABLED: bool = api_config.get("progress_callback_enabled", True)
        self.STATUS_CHECK_INTERVAL: int = api_config.get("status_check_interval", 30)

        # Validation
        self._validate_config()

        if self.ENABLED:
            logging.info("API upload configuration loaded successfully")
        else:
            logging.info("API upload is disabled")

    def _validate_config(self):
        """Validate the configuration values."""
        if self.ENABLED:
            if not self.BASE_URL:
                raise ValueError("API base_url is required when API is enabled")
            if not self.API_TOKEN:
                raise ValueError("API token is required when API is enabled")

            if not self.BASE_URL.startswith(("http://", "https://")):
                raise ValueError("API base_url must start with http:// or https://")

        if self.UPLOAD_TIMEOUT < 10:
            logging.warning("Upload timeout is very low, uploads may fail")

        if self.MAX_RETRIES < 0:
            self.MAX_RETRIES = 0

        if self.MAX_CONCURRENT_UPLOADS < 1:
            self.MAX_CONCURRENT_UPLOADS = 1
        elif self.MAX_CONCURRENT_UPLOADS > 5:
            logging.warning("High concurrent upload count may impact performance")

    def is_enabled(self) -> bool:
        """Check if API upload is enabled and properly configured."""
        return self.ENABLED and bool(self.BASE_URL) and bool(self.API_TOKEN)

    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return {
            "enabled": self.ENABLED,
            "base_url": self.BASE_URL,
            "api_token": "***" if self.API_TOKEN else "",  # Mask token for logging
            "auto_upload": self.AUTO_UPLOAD,
            "upload_timeout": self.UPLOAD_TIMEOUT,
            "max_retries": self.MAX_RETRIES,
            "max_concurrent_uploads": self.MAX_CONCURRENT_UPLOADS,
            "delete_after_upload": self.DELETE_AFTER_UPLOAD,
            "upload_older_recordings": self.UPLOAD_OLDER_RECORDINGS,
            "max_file_age_days": self.MAX_FILE_AGE_DAYS,
            "progress_callback_enabled": self.PROGRESS_CALLBACK_ENABLED,
            "status_check_interval": self.STATUS_CHECK_INTERVAL,
        }


def get_default_api_config() -> Dict[str, Any]:
    """Get default API configuration structure."""
    return {
        "api": {
            "enabled": False,
            "base_url": "",
            "api_token": "",
            "auto_upload": False,
            "upload_timeout": 60,
            "max_retries": 3,
            "max_concurrent_uploads": 2,
            "delete_after_upload": False,
            "upload_older_recordings": True,
            "max_file_age_days": 30,
            "progress_callback_enabled": True,
            "status_check_interval": 30,
        }
    }
