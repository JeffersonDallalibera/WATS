# WATS_Project/wats_app/api/upload_manager.py

"""
Manager for orchestrating recording uploads with retry logic,
queue management, and integration with the recording system.
"""

import json
import logging
import threading
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from queue import Empty, Queue
from typing import Any, Callable, Dict, List, Optional

from .exceptions import NetworkError
from .upload_client import RecordingUploadClient


class UploadStatus(Enum):
    """Status of an upload task."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"


@dataclass
class UploadTask:
    """Represents an upload task."""

    id: str
    video_file: Path
    metadata_file: Path
    created_at: datetime
    status: UploadStatus = UploadStatus.PENDING
    retry_count: int = 0
    last_error: Optional[str] = None
    progress: int = 0  # 0-100
    server_file_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        data = asdict(self)
        data["created_at"] = self.created_at.isoformat()
        data["status"] = self.status.value
        data["video_file"] = str(self.video_file)
        data["metadata_file"] = str(self.metadata_file)
        return data


class UploadManager:
    """
    Manages the upload queue and coordinates recording uploads.

    Features:
    - Asynchronous upload queue
    - Automatic retry with exponential backoff
    - Progress tracking and callbacks
    - Persistent upload state
    - Bandwidth throttling support
    """

    def __init__(
        self,
        upload_client: RecordingUploadClient,
        max_retries: int = 3,
        max_concurrent_uploads: int = 2,
        state_file: Optional[Path] = None,
    ):
        """
        Initialize the upload manager.

        Args:
            upload_client: Configured upload client
            max_retries: Maximum retry attempts per upload
            max_concurrent_uploads: Maximum simultaneous uploads
            state_file: File to persist upload state
        """
        self.upload_client = upload_client
        self.max_retries = max_retries
        self.max_concurrent_uploads = max_concurrent_uploads
        self.state_file = state_file

        # Upload queue and tracking
        self.upload_queue: Queue[UploadTask] = Queue()
        self.active_uploads: Dict[str, UploadTask] = {}
        self.completed_uploads: Dict[str, UploadTask] = {}
        self.failed_uploads: Dict[str, UploadTask] = {}

        # Threading
        self.worker_threads: List[threading.Thread] = []
        self.running = False
        self.lock = threading.Lock()

        # Callbacks
        self.on_upload_started: Optional[Callable[[UploadTask], None]] = None
        self.on_upload_progress: Optional[Callable[[UploadTask], None]] = None
        self.on_upload_completed: Optional[Callable[[UploadTask], None]] = None
        self.on_upload_failed: Optional[Callable[[UploadTask], None]] = None

        # Load previous state
        self._load_state()

        logging.info(f"UploadManager initialized with {max_concurrent_uploads} workers")

    def start(self):
        """Start the upload manager and worker threads."""
        if self.running:
            logging.warning("UploadManager is already running")
            return

        self.running = True

        # Start worker threads
        for i in range(self.max_concurrent_uploads):
            thread = threading.Thread(
                target=self._worker_thread, name=f"UploadWorker-{i+1}", daemon=True
            )
            thread.start()
            self.worker_threads.append(thread)

        logging.info(f"UploadManager started with {len(self.worker_threads)} workers")

    def stop(self, timeout: float = 30.0):
        """Stop the upload manager and wait for threads to finish."""
        if not self.running:
            return

        self.running = False

        # Wait for threads to finish
        for thread in self.worker_threads:
            thread.join(timeout=timeout)

        # Save state
        self._save_state()

        logging.info("UploadManager stopped")

    def queue_upload(self, video_file: Path, metadata_file: Path) -> str:
        """
        Queue a recording for upload.

        Args:
            video_file: Path to the video file
            metadata_file: Path to the metadata file

        Returns:
            Upload task ID
        """
        task_id = f"upload_{int(time.time())}_{video_file.stem}"

        task = UploadTask(
            id=task_id,
            video_file=video_file,
            metadata_file=metadata_file,
            created_at=datetime.now(),
        )

        self.upload_queue.put(task)

        logging.info(f"Queued upload: {task_id} ({video_file.name})")
        return task_id

    def get_task_status(self, task_id: str) -> Optional[UploadTask]:
        """Get the status of an upload task."""
        with self.lock:
            # Check active uploads
            if task_id in self.active_uploads:
                return self.active_uploads[task_id]

            # Check completed uploads
            if task_id in self.completed_uploads:
                return self.completed_uploads[task_id]

            # Check failed uploads
            if task_id in self.failed_uploads:
                return self.failed_uploads[task_id]

            return None

    def get_queue_status(self) -> Dict[str, Any]:
        """Get overall queue status."""
        with self.lock:
            return {
                "queue_size": self.upload_queue.qsize(),
                "active_uploads": len(self.active_uploads),
                "completed_uploads": len(self.completed_uploads),
                "failed_uploads": len(self.failed_uploads),
                "is_running": self.running,
            }

    def retry_failed_upload(self, task_id: str) -> bool:
        """Retry a failed upload."""
        with self.lock:
            if task_id not in self.failed_uploads:
                return False

            task = self.failed_uploads.pop(task_id)
            task.status = UploadStatus.PENDING
            task.retry_count = 0
            task.last_error = None
            task.progress = 0

            self.upload_queue.put(task)

            logging.info(f"Retrying failed upload: {task_id}")
            return True

    def cancel_upload(self, task_id: str) -> bool:
        """Cancel an upload (only if not started)."""
        with self.lock:
            # Can only cancel pending uploads
            if task_id in self.active_uploads:
                logging.warning(f"Cannot cancel active upload: {task_id}")
                return False

            # Remove from failed uploads
            if task_id in self.failed_uploads:
                self.failed_uploads.pop(task_id)
                logging.info(f"Cancelled failed upload: {task_id}")
                return True

        return False

    def _worker_thread(self):
        """Worker thread that processes upload tasks."""
        thread_name = threading.current_thread().name
        logging.debug(f"Upload worker {thread_name} started")

        while self.running:
            try:
                # Get next task from queue (with timeout to check if we should stop)
                try:
                    task = self.upload_queue.get(timeout=1.0)
                except Empty:
                    continue

                # Process the upload task
                self._process_upload_task(task)
                self.upload_queue.task_done()

            except Exception as e:
                logging.error(f"Error in upload worker {thread_name}: {e}")

        logging.debug(f"Upload worker {thread_name} stopped")

    def _process_upload_task(self, task: UploadTask):
        """Process a single upload task."""
        task_id = task.id

        try:
            # Move to active uploads
            with self.lock:
                self.active_uploads[task_id] = task
                task.status = UploadStatus.IN_PROGRESS

            # Callback: upload started
            if self.on_upload_started:
                try:
                    self.on_upload_started(task)
                except Exception as e:
                    logging.error(f"Error in upload_started callback: {e}")

            # Progress callback
            def progress_callback(bytes_sent: int, total_bytes: int):
                progress = int((bytes_sent / total_bytes) * 100) if total_bytes > 0 else 0
                task.progress = progress

                if self.on_upload_progress:
                    try:
                        self.on_upload_progress(task)
                    except Exception as e:
                        logging.error(f"Error in upload_progress callback: {e}")

            # Perform the upload
            result = self.upload_client.upload_recording(
                task.video_file, task.metadata_file, progress_callback=progress_callback
            )

            # Upload successful
            task.status = UploadStatus.COMPLETED
            task.progress = 100
            task.server_file_id = result.get("file_id")

            with self.lock:
                self.active_uploads.pop(task_id, None)
                self.completed_uploads[task_id] = task

            # Callback: upload completed
            if self.on_upload_completed:
                try:
                    self.on_upload_completed(task)
                except Exception as e:
                    logging.error(f"Error in upload_completed callback: {e}")

            logging.info(f"Upload completed: {task_id}")

        except Exception as e:
            # Upload failed
            self._handle_upload_failure(task, str(e))

    def _handle_upload_failure(self, task: UploadTask, error_message: str):
        """Handle upload failure with retry logic."""
        task.last_error = error_message
        task.retry_count += 1

        logging.warning(f"Upload failed (attempt {task.retry_count}): {task.id} - {error_message}")

        # Check if we should retry
        if task.retry_count < self.max_retries and isinstance(error_message, (NetworkError, str)):
            # Calculate backoff delay
            delay = min(2**task.retry_count, 60)  # Exponential backoff, max 60s

            task.status = UploadStatus.RETRYING

            # Schedule retry
            def retry_task():
                time.sleep(delay)
                if self.running:
                    self.upload_queue.put(task)

            retry_thread = threading.Thread(target=retry_task, daemon=True)
            retry_thread.start()

            logging.info(f"Retrying upload {task.id} in {delay} seconds")
        else:
            # Max retries reached or non-retryable error
            task.status = UploadStatus.FAILED

            with self.lock:
                self.active_uploads.pop(task.id, None)
                self.failed_uploads[task.id] = task

            # Callback: upload failed
            if self.on_upload_failed:
                try:
                    self.on_upload_failed(task)
                except Exception as e:
                    logging.error(f"Error in upload_failed callback: {e}")

    def _save_state(self):
        """Save upload state to disk."""
        if not self.state_file:
            return

        try:
            state = {
                "completed_uploads": {k: v.to_dict() for k, v in self.completed_uploads.items()},
                "failed_uploads": {k: v.to_dict() for k, v in self.failed_uploads.items()},
                "saved_at": datetime.now().isoformat(),
            }

            with open(self.state_file, "w", encoding="utf-8") as f:
                json.dump(state, f, indent=2, ensure_ascii=False)

            logging.debug(f"Upload state saved to {self.state_file}")

        except Exception as e:
            logging.error(f"Failed to save upload state: {e}")

    def _load_state(self):
        """Load upload state from disk."""
        if not self.state_file or not self.state_file.exists():
            return

        try:
            with open(self.state_file, "r", encoding="utf-8") as f:
                state = json.load(f)

            # Load completed uploads
            for task_id, task_data in state.get("completed_uploads", {}).items():
                task_data["created_at"] = datetime.fromisoformat(task_data["created_at"])
                task_data["status"] = UploadStatus(task_data["status"])
                task_data["video_file"] = Path(task_data["video_file"])
                task_data["metadata_file"] = Path(task_data["metadata_file"])

                task = UploadTask(**task_data)
                self.completed_uploads[task_id] = task

            # Load failed uploads
            for task_id, task_data in state.get("failed_uploads", {}).items():
                task_data["created_at"] = datetime.fromisoformat(task_data["created_at"])
                task_data["status"] = UploadStatus(task_data["status"])
                task_data["video_file"] = Path(task_data["video_file"])
                task_data["metadata_file"] = Path(task_data["metadata_file"])

                task = UploadTask(**task_data)
                self.failed_uploads[task_id] = task

            logging.info(
                f"Upload state loaded: {len(self.completed_uploads)} completed, {len(self.failed_uploads)} failed"
            )

        except Exception as e:
            logging.error(f"Failed to load upload state: {e}")

    def cleanup_old_tasks(self, days_to_keep: int = 7):
        """Remove old completed/failed tasks from memory and state."""
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        removed_count = 0

        with self.lock:
            # Clean completed uploads
            to_remove = [
                task_id
                for task_id, task in self.completed_uploads.items()
                if task.created_at < cutoff_date
            ]
            for task_id in to_remove:
                self.completed_uploads.pop(task_id)
                removed_count += 1

            # Clean failed uploads
            to_remove = [
                task_id
                for task_id, task in self.failed_uploads.items()
                if task.created_at < cutoff_date
            ]
            for task_id in to_remove:
                self.failed_uploads.pop(task_id)
                removed_count += 1

        if removed_count > 0:
            logging.info(f"Cleaned up {removed_count} old upload tasks")
            self._save_state()

    def __del__(self):
        """Destructor to ensure proper cleanup."""
        if self.running:
            self.stop()
