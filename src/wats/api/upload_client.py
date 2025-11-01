# WATS_Project/wats_app/api/upload_client.py

"""
Client for uploading recording files to external storage API.
Handles authentication, file upload, retry logic, and progress tracking.
"""

import json
import logging
from pathlib import Path
from typing import Any, Callable, Dict, Optional

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from .exceptions import AuthenticationError, NetworkError, ServerError, UploadError


class RecordingUploadClient:
    """
    Client for uploading WATS recording files to external storage.

    Features:
    - Authentication with API tokens
    - Progress tracking for uploads
    - Automatic retry on failure
    - Chunked upload for large files
    - Metadata validation
    """

    def __init__(self, api_base_url: str, api_token: str, timeout: int = 60, max_retries: int = 3):
        """
        Initialize the upload client.

        Args:
            api_base_url: Base URL of the upload API (e.g., "https://storage.company.com/api")
            api_token: Authentication token for the API
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
        """
        self.api_base_url = api_base_url.rstrip("/")
        self.api_token = api_token
        self.timeout = timeout
        self.max_retries = max_retries

        # Configure session with retry strategy
        self.session = requests.Session()
        retry_strategy = Retry(
            total=max_retries,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS", "POST"],  # Updated parameter name
            backoff_factor=1,
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

        # Set authentication headers
        self.session.headers.update(
            {"Authorization": f"Bearer {api_token}", "User-Agent": "WATS-RecordingUploader/1.0"}
        )

        logging.info(f"RecordingUploadClient initialized for {api_base_url}")

    def test_connection(self) -> bool:
        """
        Test connection to the API server.

        Returns:
            True if connection successful, False otherwise
        """
        try:
            response = self.session.get(f"{self.api_base_url}/health", timeout=self.timeout)
            response.raise_for_status()

            logging.info("API connection test successful")
            return True

        except requests.exceptions.RequestException as e:
            logging.error(f"API connection test failed: {e}")
            return False

    def upload_recording(
        self,
        video_file: Path,
        metadata_file: Path,
        progress_callback: Optional[Callable[[int, int], None]] = None,
    ) -> Dict[str, Any]:
        """
        Upload a recording file with its metadata.

        Args:
            video_file: Path to the video file
            metadata_file: Path to the metadata JSON file
            progress_callback: Optional callback function for progress updates (bytes_sent, total_bytes)

        Returns:
            Dict containing upload result with file_id, upload_url, etc.

        Raises:
            ApiError: On API-related errors
            FileNotFoundError: If files don't exist
        """
        if not video_file.exists():
            raise FileNotFoundError(f"Video file not found: {video_file}")
        if not metadata_file.exists():
            raise FileNotFoundError(f"Metadata file not found: {metadata_file}")

        # Load and validate metadata
        try:
            with open(metadata_file, "r", encoding="utf-8") as f:
                metadata = json.load(f)
        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            raise UploadError(f"Invalid metadata file: {e}")

        # Get file info
        video_size = video_file.stat().st_size
        metadata_size = metadata_file.stat().st_size
        total_size = video_size + metadata_size

        logging.info(f"Starting upload: {video_file.name} ({video_size:,} bytes)")

        try:
            # Step 1: Create upload session
            upload_session = self._create_upload_session(metadata, video_size)

            # Step 2: Upload metadata file
            self._upload_file(
                metadata_file,
                upload_session["metadata_upload_url"],
                progress_callback=lambda sent, total: (
                    progress_callback(sent, total_size) if progress_callback else None
                ),
            )

            # Step 3: Upload video file
            self._upload_file(
                video_file,
                upload_session["video_upload_url"],
                progress_callback=lambda sent, total: (
                    progress_callback(metadata_size + sent, total_size)
                    if progress_callback
                    else None
                ),
            )

            # Step 4: Finalize upload
            final_result = self._finalize_upload(upload_session["session_id"])

            logging.info(f"Upload completed successfully: {final_result.get('file_id')}")
            return final_result

        except requests.exceptions.Timeout:
            raise NetworkError("Upload timeout - server took too long to respond")
        except requests.exceptions.ConnectionError:
            raise NetworkError("Connection failed - unable to reach upload server")
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 401:
                raise AuthenticationError("Invalid API token")
            elif e.response.status_code == 403:
                raise AuthenticationError("Insufficient permissions")
            elif e.response.status_code >= 400 and e.response.status_code < 500:
                raise UploadError(f"Client error: {e.response.text}")
            else:
                raise ServerError(f"Server error: {e.response.text}", e.response.status_code)
        except Exception as e:
            raise UploadError(f"Unexpected upload error: {e}")

    def _create_upload_session(self, metadata: Dict[str, Any], file_size: int) -> Dict[str, Any]:
        """Create a new upload session on the server."""
        payload = {
            "session_id": metadata.get("session_id"),
            "connection_info": metadata.get("connection_info", {}),
            "file_size": file_size,
            "metadata": metadata,
        }

        response = self.session.post(
            f"{self.api_base_url}/uploads/create-session", json=payload, timeout=self.timeout
        )
        response.raise_for_status()

        result = response.json()
        logging.debug(f"Upload session created: {result.get('session_id')}")
        return result

    def _upload_file(
        self,
        file_path: Path,
        upload_url: str,
        progress_callback: Optional[Callable[[int, int], None]] = None,
    ) -> Dict[str, Any]:
        """Upload a file to the specified URL with progress tracking."""
        file_size = file_path.stat().st_size

        with open(file_path, "rb") as f:
            if progress_callback:
                # Create a custom file-like object that reports progress
                file_obj = ProgressFileWrapper(f, file_size, progress_callback)
            else:
                file_obj = f

            files = {"file": (file_path.name, file_obj, "application/octet-stream")}

            response = self.session.post(
                upload_url, files=files, timeout=self.timeout * 2  # Double timeout for file uploads
            )
            response.raise_for_status()

            result = response.json()
            logging.debug(f"File uploaded: {file_path.name} -> {result.get('file_id')}")
            return result

    def _finalize_upload(self, session_id: str) -> Dict[str, Any]:
        """Finalize the upload session."""
        response = self.session.post(
            f"{self.api_base_url}/uploads/{session_id}/finalize", timeout=self.timeout
        )
        response.raise_for_status()

        result = response.json()
        logging.debug(f"Upload finalized: {session_id}")
        return result

    def get_upload_status(self, session_id: str) -> Dict[str, Any]:
        """Get the status of an upload session."""
        response = self.session.get(
            f"{self.api_base_url}/uploads/{session_id}/status", timeout=self.timeout
        )
        response.raise_for_status()

        return response.json()

    def delete_recording(self, file_id: str) -> bool:
        """Delete a recording from the server."""
        try:
            response = self.session.delete(
                f"{self.api_base_url}/recordings/{file_id}", timeout=self.timeout
            )
            response.raise_for_status()

            logging.info(f"Recording deleted: {file_id}")
            return True

        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                logging.warning(f"Recording not found for deletion: {file_id}")
                return True  # Already deleted
            raise ServerError(
                f"Failed to delete recording: {e.response.text}", e.response.status_code
            )

    def list_recordings(self, limit: int = 50, offset: int = 0) -> Dict[str, Any]:
        """List recordings from the server."""
        params = {"limit": limit, "offset": offset}

        response = self.session.get(
            f"{self.api_base_url}/recordings", params=params, timeout=self.timeout
        )
        response.raise_for_status()

        return response.json()

    def close(self):
        """Close the session and cleanup resources."""
        if self.session:
            self.session.close()
            logging.debug("Upload client session closed")


class ProgressFileWrapper:
    """
    Wrapper for file objects that reports upload progress.
    """

    def __init__(self, file_obj, total_size: int, progress_callback: Callable[[int, int], None]):
        self.file_obj = file_obj
        self.total_size = total_size
        self.progress_callback = progress_callback
        self.bytes_read = 0

    def read(self, size: int = -1) -> bytes:
        """Read data and report progress."""
        data = self.file_obj.read(size)
        self.bytes_read += len(data)

        if self.progress_callback:
            self.progress_callback(self.bytes_read, self.total_size)

        return data

    def __getattr__(self, name):
        """Delegate other attributes to the wrapped file object."""
        return getattr(self.file_obj, name)
