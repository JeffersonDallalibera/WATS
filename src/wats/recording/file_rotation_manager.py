# WATS_Project/wats_app/recording/file_rotation_manager.py

import os
import time
import threading
import logging
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

class FileRotationManager:
    """
    Manages file rotation and cleanup for session recordings.
    Features:
    - Automatic cleanup of old recordings
    - File size and age monitoring
    - Storage quota management
    - Metadata tracking
    """
    
    def __init__(self, recordings_dir: str, max_total_size_gb: float = 10.0,
                 max_file_age_days: int = 30, cleanup_interval_hours: int = 6):
        """
        Initialize the file rotation manager.
        
        Args:
            recordings_dir: Directory containing recordings
            max_total_size_gb: Maximum total size for all recordings (GB)
            max_file_age_days: Maximum age for recordings before deletion (days)
            cleanup_interval_hours: Interval between cleanup runs (hours)
        """
        self.recordings_dir = Path(recordings_dir)
        self.recordings_dir.mkdir(parents=True, exist_ok=True)
        
        self.max_total_size = max_total_size_gb * 1024 * 1024 * 1024  # Convert to bytes
        self.max_file_age = max_file_age_days * 24 * 60 * 60  # Convert to seconds
        self.cleanup_interval = cleanup_interval_hours * 60 * 60  # Convert to seconds
        
        # Cleanup state
        self.cleanup_thread: Optional[threading.Thread] = None
        self.stop_cleanup = threading.Event()
        self.last_cleanup_time = 0
        
        # Statistics
        self.stats = {
            "total_files": 0,
            "total_size_bytes": 0,
            "last_cleanup": None,
            "files_deleted_last_cleanup": 0,
            "space_freed_last_cleanup": 0
        }
        
        logging.info(f"FileRotationManager initialized - Dir: {self.recordings_dir}, "
                    f"Max size: {max_total_size_gb}GB, Max age: {max_file_age_days} days")

    def start_automatic_cleanup(self):
        """Start the automatic cleanup process."""
        if self.cleanup_thread and self.cleanup_thread.is_alive():
            logging.warning("Cleanup thread already running")
            return
            
        self.stop_cleanup.clear()
        self.cleanup_thread = threading.Thread(
            target=self._cleanup_loop,
            daemon=True,
            name="FileRotationManager-Cleanup"
        )
        self.cleanup_thread.start()
        logging.info("Started automatic cleanup thread")

    def stop_automatic_cleanup(self):
        """Stop the automatic cleanup process."""
        if self.cleanup_thread:
            self.stop_cleanup.set()
            self.cleanup_thread.join(timeout=5.0)
            logging.info("Stopped automatic cleanup thread")

    def _cleanup_loop(self):
        """Main cleanup loop running in a separate thread."""
        while not self.stop_cleanup.is_set():
            try:
                current_time = time.time()
                
                # Check if it's time for cleanup
                if current_time - self.last_cleanup_time >= self.cleanup_interval:
                    self.cleanup_recordings()
                    self.last_cleanup_time = current_time
                
                # Wait before next check (check every minute)
                if not self.stop_cleanup.wait(60):
                    continue
                    
            except Exception as e:
                logging.error(f"Error in cleanup loop: {e}")
                # Wait a bit before retrying
                if not self.stop_cleanup.wait(300):  # 5 minutes
                    continue

    def cleanup_recordings(self) -> Dict[str, Any]:
        """
        Perform cleanup of old and excessive recordings.
        
        Returns:
            Dictionary with cleanup statistics
        """
        try:
            logging.info("Starting recording cleanup")
            
            files_deleted = 0
            space_freed = 0
            
            # Get all recording files with their info
            recording_files = self._get_recording_files_info()
            
            # Sort by modification time (oldest first)
            recording_files.sort(key=lambda x: x['mtime'])
            
            current_time = time.time()
            
            # Phase 1: Delete files older than max_file_age
            for file_info in recording_files[:]:  # Copy list to allow removal
                if current_time - file_info['mtime'] > self.max_file_age:
                    if self._delete_recording_file(file_info):
                        files_deleted += 1
                        space_freed += file_info['size']
                        recording_files.remove(file_info)
            
            # Phase 2: Delete oldest files if total size exceeds limit
            total_size = sum(f['size'] for f in recording_files)
            
            while total_size > self.max_total_size and recording_files:
                file_info = recording_files.pop(0)  # Remove oldest
                if self._delete_recording_file(file_info):
                    files_deleted += 1
                    space_freed += file_info['size']
                    total_size -= file_info['size']
            
            # Update statistics
            self.stats.update({
                "total_files": len(recording_files),
                "total_size_bytes": total_size,
                "last_cleanup": datetime.now().isoformat(),
                "files_deleted_last_cleanup": files_deleted,
                "space_freed_last_cleanup": space_freed
            })
            
            # Save statistics
            self._save_statistics()
            
            if files_deleted > 0:
                logging.info(f"Cleanup completed: deleted {files_deleted} files, "
                           f"freed {space_freed / (1024*1024):.1f} MB")
            else:
                logging.info("Cleanup completed: no files deleted")
                
            return {
                "files_deleted": files_deleted,
                "space_freed_mb": space_freed / (1024 * 1024),
                "total_files_remaining": len(recording_files),
                "total_size_mb": total_size / (1024 * 1024)
            }
            
        except Exception as e:
            logging.error(f"Error during cleanup: {e}")
            return {"error": str(e)}

    def _get_recording_files_info(self) -> List[Dict[str, Any]]:
        """Get information about all recording files."""
        files_info = []
        
        try:
            for file_path in self.recordings_dir.glob("*.mp4"):
                try:
                    stat = file_path.stat()
                    files_info.append({
                        "path": file_path,
                        "name": file_path.name,
                        "size": stat.st_size,
                        "mtime": stat.st_mtime,
                        "ctime": stat.st_ctime
                    })
                except Exception as e:
                    logging.error(f"Error getting info for {file_path}: {e}")
                    
        except Exception as e:
            logging.error(f"Error listing recording files: {e}")
            
        return files_info

    def _delete_recording_file(self, file_info: Dict[str, Any]) -> bool:
        """
        Delete a recording file and its associated metadata.
        
        Args:
            file_info: Dictionary with file information
            
        Returns:
            True if deleted successfully, False otherwise
        """
        try:
            file_path = file_info['path']
            
            # Delete the video file
            file_path.unlink()
            
            # Delete associated metadata file
            metadata_file = file_path.with_suffix('.json')
            if metadata_file.exists():
                metadata_file.unlink()
            
            # Delete associated log file if exists
            log_file = file_path.with_suffix('.log')
            if log_file.exists():
                log_file.unlink()
            
            logging.debug(f"Deleted recording file: {file_path.name}")
            return True
            
        except Exception as e:
            logging.error(f"Error deleting file {file_info.get('name', 'unknown')}: {e}")
            return False

    def _save_statistics(self):
        """Save cleanup statistics to a file."""
        try:
            stats_file = self.recordings_dir / "cleanup_stats.json"
            with open(stats_file, 'w', encoding='utf-8') as f:
                json.dump(self.stats, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logging.error(f"Error saving statistics: {e}")

    def get_storage_info(self) -> Dict[str, Any]:
        """
        Get current storage information.
        
        Returns:
            Dictionary with storage statistics
        """
        try:
            recording_files = self._get_recording_files_info()
            total_size = sum(f['size'] for f in recording_files)
            total_files = len(recording_files)
            
            # Calculate age distribution
            current_time = time.time()
            age_distribution = {
                "less_than_1_day": 0,
                "1_to_7_days": 0,
                "7_to_30_days": 0,
                "more_than_30_days": 0
            }
            
            for file_info in recording_files:
                age_days = (current_time - file_info['mtime']) / (24 * 60 * 60)
                if age_days < 1:
                    age_distribution["less_than_1_day"] += 1
                elif age_days < 7:
                    age_distribution["1_to_7_days"] += 1
                elif age_days < 30:
                    age_distribution["7_to_30_days"] += 1
                else:
                    age_distribution["more_than_30_days"] += 1
            
            return {
                "total_files": total_files,
                "total_size_bytes": total_size,
                "total_size_mb": total_size / (1024 * 1024),
                "total_size_gb": total_size / (1024 * 1024 * 1024),
                "max_size_gb": self.max_total_size / (1024 * 1024 * 1024),
                "size_usage_percent": (total_size / self.max_total_size) * 100 if self.max_total_size > 0 else 0,
                "age_distribution": age_distribution,
                "cleanup_stats": self.stats.copy()
            }
            
        except Exception as e:
            logging.error(f"Error getting storage info: {e}")
            return {"error": str(e)}

    def force_cleanup_by_age(self, max_age_days: int) -> Dict[str, Any]:
        """
        Force cleanup of files older than specified age.
        
        Args:
            max_age_days: Maximum age in days
            
        Returns:
            Cleanup results
        """
        try:
            files_deleted = 0
            space_freed = 0
            max_age_seconds = max_age_days * 24 * 60 * 60
            current_time = time.time()
            
            recording_files = self._get_recording_files_info()
            
            for file_info in recording_files:
                if current_time - file_info['mtime'] > max_age_seconds:
                    if self._delete_recording_file(file_info):
                        files_deleted += 1
                        space_freed += file_info['size']
            
            logging.info(f"Force cleanup by age ({max_age_days} days): "
                        f"deleted {files_deleted} files, freed {space_freed / (1024*1024):.1f} MB")
            
            return {
                "files_deleted": files_deleted,
                "space_freed_mb": space_freed / (1024 * 1024)
            }
            
        except Exception as e:
            logging.error(f"Error in force cleanup: {e}")
            return {"error": str(e)}

    def force_cleanup_by_size(self, target_size_gb: float) -> Dict[str, Any]:
        """
        Force cleanup to achieve target total size.
        
        Args:
            target_size_gb: Target total size in GB
            
        Returns:
            Cleanup results
        """
        try:
            files_deleted = 0
            space_freed = 0
            target_size_bytes = target_size_gb * 1024 * 1024 * 1024
            
            recording_files = self._get_recording_files_info()
            # Sort by modification time (oldest first)
            recording_files.sort(key=lambda x: x['mtime'])
            
            total_size = sum(f['size'] for f in recording_files)
            
            while total_size > target_size_bytes and recording_files:
                file_info = recording_files.pop(0)  # Remove oldest
                if self._delete_recording_file(file_info):
                    files_deleted += 1
                    space_freed += file_info['size']
                    total_size -= file_info['size']
            
            logging.info(f"Force cleanup by size ({target_size_gb}GB): "
                        f"deleted {files_deleted} files, freed {space_freed / (1024*1024):.1f} MB")
            
            return {
                "files_deleted": files_deleted,
                "space_freed_mb": space_freed / (1024 * 1024),
                "final_size_gb": total_size / (1024 * 1024 * 1024)
            }
            
        except Exception as e:
            logging.error(f"Error in force cleanup by size: {e}")
            return {"error": str(e)}

    def __del__(self):
        """Destructor to ensure proper cleanup."""
        self.stop_automatic_cleanup()