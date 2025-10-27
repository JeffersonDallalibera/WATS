# WATS_Project/wats_app/api/api_integration.py

"""
Integration manager for the recording upload API system.
Coordinates between recording manager and upload manager.
"""

import logging
import time
from pathlib import Path
from typing import Optional, Dict, Any, Callable, List

from .upload_client import RecordingUploadClient
from .upload_manager import UploadManager, UploadTask, UploadStatus
from .exceptions import ApiError, NetworkError, AuthenticationError


class ApiIntegrationManager:
    """
    Manages integration between WATS recording system and external API.
    
    Features:
    - Automatic upload of completed recordings
    - Manual upload triggering
    - Upload status monitoring
    - Error handling and retry logic
    - Progress callbacks for UI updates
    """
    
    def __init__(self, settings):
        """
        Initialize the API integration manager.
        
        Args:
            settings: WATS settings instance with API configuration
        """
        self.settings = settings
        self.upload_client: Optional[RecordingUploadClient] = None
        self.upload_manager: Optional[UploadManager] = None
        self.is_initialized = False
        
        # Callbacks for UI updates
        self.on_upload_started: Optional[Callable[[str, str], None]] = None  # (task_id, filename)
        self.on_upload_progress: Optional[Callable[[str, int], None]] = None  # (task_id, progress)
        self.on_upload_completed: Optional[Callable[[str, str], None]] = None  # (task_id, server_file_id)
        self.on_upload_failed: Optional[Callable[[str, str], None]] = None  # (task_id, error)
        
        # Initialize components (handles both enabled and disabled cases)
        self.initialize()
    
    def initialize(self) -> bool:
        """
        Initialize the API components.
        
        Returns:
            True if initialization successful, False otherwise
        """
        if self.is_initialized:
            logging.debug("API integration already initialized")
            return True
        
        try:
            if not self.settings.API_ENABLED:
                logging.info("API upload is disabled")
                self.is_initialized = True  # Still mark as initialized even when disabled
                return True
            
            # Validate API configuration
            if not self.settings.validate_api_config():
                logging.error("API configuration validation failed")
                return False
            
            # Initialize upload client
            self.upload_client = RecordingUploadClient(
                api_base_url=self.settings.API_BASE_URL,
                api_token=self.settings.API_TOKEN,
                timeout=self.settings.API_UPLOAD_TIMEOUT,
                max_retries=self.settings.API_MAX_RETRIES
            )
            
            # Test connection
            if not self.upload_client.test_connection():
                logging.error("Failed to connect to upload API")
                return False
            
            # Initialize upload manager
            state_file = Path(self.settings.USER_DATA_DIR) / 'upload_state.json'
            self.upload_manager = UploadManager(
                upload_client=self.upload_client,
                max_retries=self.settings.API_MAX_RETRIES,
                max_concurrent_uploads=self.settings.API_MAX_CONCURRENT_UPLOADS,
                state_file=state_file
            )
            
            # Set up callbacks
            self.upload_manager.on_upload_started = self._on_upload_started_internal
            self.upload_manager.on_upload_progress = self._on_upload_progress_internal
            self.upload_manager.on_upload_completed = self._on_upload_completed_internal
            self.upload_manager.on_upload_failed = self._on_upload_failed_internal
            
            # Start upload manager
            self.upload_manager.start()
            
            self.is_initialized = True
            logging.info("API integration initialized successfully")
            return True
            
        except Exception as e:
            logging.error(f"Failed to initialize API integration: {e}")
            return False
    
    def shutdown(self):
        """Shutdown the API integration manager."""
        if not self.is_initialized:
            return
        
        try:
            if self.upload_manager:
                self.upload_manager.stop()
            
            if self.upload_client:
                self.upload_client.close()
            
            self.is_initialized = False
            logging.info("API integration shutdown complete")
            
        except Exception as e:
            logging.error(f"Error during API integration shutdown: {e}")
    
    def upload_recording(self, video_file: Path, metadata_file: Path) -> Optional[str]:
        """
        Queue a recording for upload.
        
        Args:
            video_file: Path to the video file
            metadata_file: Path to the metadata file
            
        Returns:
            Upload task ID if queued successfully, None otherwise
        """
        if not self.is_initialized or not self.upload_manager:
            logging.warning("Cannot upload: API integration not initialized")
            return None
        
        try:
            task_id = self.upload_manager.queue_upload(video_file, metadata_file)
            logging.info(f"Recording queued for upload: {video_file.name} (task: {task_id})")
            return task_id
            
        except Exception as e:
            logging.error(f"Failed to queue upload: {e}")
            return None
    
    def get_upload_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get the status of an upload task."""
        if not self.is_initialized or not self.upload_manager:
            return None
        
        task = self.upload_manager.get_task_status(task_id)
        if not task:
            return None
        
        return {
            'task_id': task.id,
            'status': task.status.value,
            'progress': task.progress,
            'video_file': str(task.video_file),
            'created_at': task.created_at.isoformat(),
            'retry_count': task.retry_count,
            'last_error': task.last_error,
            'server_file_id': task.server_file_id
        }
    
    def get_queue_status(self) -> Dict[str, Any]:
        """Get overall upload queue status."""
        if not self.is_initialized or not self.upload_manager:
            return {
                'queue_size': 0,
                'active_uploads': 0,
                'completed_uploads': 0,
                'failed_uploads': 0,
                'is_running': False
            }
        
        return self.upload_manager.get_queue_status()
    
    def retry_failed_upload(self, task_id: str) -> bool:
        """Retry a failed upload."""
        if not self.is_initialized or not self.upload_manager:
            return False
        
        return self.upload_manager.retry_failed_upload(task_id)
    
    def cancel_upload(self, task_id: str) -> bool:
        """Cancel an upload."""
        if not self.is_initialized or not self.upload_manager:
            return False
        
        return self.upload_manager.cancel_upload(task_id)
    
    def upload_older_recordings(self, recordings_dir: Path, max_age_days: Optional[int] = None) -> List[str]:
        """
        Upload older recordings from the recordings directory.
        
        Args:
            recordings_dir: Directory containing recordings
            max_age_days: Maximum age of recordings to upload (None = use config)
            
        Returns:
            List of task IDs for queued uploads
        """
        if not self.is_initialized or not self.upload_manager:
            logging.warning("Cannot upload older recordings: API integration not initialized")
            return []
        
        if not self.settings.API_UPLOAD_OLDER_RECORDINGS:
            logging.info("Upload of older recordings is disabled")
            return []
        
        max_age = max_age_days or self.settings.API_MAX_FILE_AGE_DAYS
        cutoff_time = time.time() - (max_age * 24 * 60 * 60)
        
        task_ids = []
        processed_count = 0
        
        try:
            # Find video files
            for video_file in recordings_dir.glob("*.mp4"):
                try:
                    # Check file age
                    if video_file.stat().st_mtime < cutoff_time:
                        continue
                    
                    # Look for corresponding metadata file
                    metadata_file = video_file.with_suffix('.json')
                    if not metadata_file.exists():
                        # Try alternative naming pattern
                        session_id = video_file.stem.split('_')[0]
                        metadata_file = recordings_dir / f"{session_id}_metadata.json"
                    
                    if not metadata_file.exists():
                        logging.warning(f"No metadata file found for {video_file.name}")
                        continue
                    
                    # Queue for upload
                    task_id = self.upload_recording(video_file, metadata_file)
                    if task_id:
                        task_ids.append(task_id)
                        processed_count += 1
                    
                except Exception as e:
                    logging.error(f"Error processing {video_file.name}: {e}")
            
            if processed_count > 0:
                logging.info(f"Queued {processed_count} older recordings for upload")
            else:
                logging.info("No older recordings found to upload")
            
        except Exception as e:
            logging.error(f"Error scanning for older recordings: {e}")
        
        return task_ids
    
    def cleanup_uploaded_files(self) -> int:
        """
        Clean up local files that have been successfully uploaded.
        
        Returns:
            Number of files deleted
        """
        if not self.is_initialized or not self.upload_manager:
            return 0
        
        if not self.settings.API_DELETE_AFTER_UPLOAD:
            return 0
        
        deleted_count = 0
        
        try:
            # Get completed uploads
            with self.upload_manager.lock:
                completed_tasks = list(self.upload_manager.completed_uploads.values())
            
            for task in completed_tasks:
                try:
                    # Only delete if upload was successful and files still exist
                    if task.status == UploadStatus.COMPLETED and task.server_file_id:
                        files_to_delete = [task.video_file, task.metadata_file]
                        
                        for file_path in files_to_delete:
                            if file_path.exists():
                                file_path.unlink()
                                deleted_count += 1
                                logging.debug(f"Deleted uploaded file: {file_path.name}")
                
                except Exception as e:
                    logging.error(f"Error deleting uploaded files for task {task.id}: {e}")
            
            if deleted_count > 0:
                logging.info(f"Cleaned up {deleted_count} uploaded files")
            
        except Exception as e:
            logging.error(f"Error during uploaded files cleanup: {e}")
        
        return deleted_count
    
    # Internal callback methods
    def _on_upload_started_internal(self, task: UploadTask):
        """Internal callback for upload started."""
        if self.on_upload_started:
            try:
                self.on_upload_started(task.id, task.video_file.name)
            except Exception as e:
                logging.error(f"Error in upload_started callback: {e}")
    
    def _on_upload_progress_internal(self, task: UploadTask):
        """Internal callback for upload progress."""
        if self.on_upload_progress:
            try:
                self.on_upload_progress(task.id, task.progress)
            except Exception as e:
                logging.error(f"Error in upload_progress callback: {e}")
    
    def _on_upload_completed_internal(self, task: UploadTask):
        """Internal callback for upload completed."""
        if self.on_upload_completed:
            try:
                self.on_upload_completed(task.id, task.server_file_id or "unknown")
            except Exception as e:
                logging.error(f"Error in upload_completed callback: {e}")
    
    def _on_upload_failed_internal(self, task: UploadTask):
        """Internal callback for upload failed."""
        if self.on_upload_failed:
            try:
                self.on_upload_failed(task.id, task.last_error or "Unknown error")
            except Exception as e:
                logging.error(f"Error in upload_failed callback: {e}")
    
    def __del__(self):
        """Destructor to ensure proper cleanup."""
        if self.is_initialized:
            self.shutdown()