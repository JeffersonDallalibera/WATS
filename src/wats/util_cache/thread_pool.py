"""
Thread Pool Manager for WATS Application.

Provides centralized thread pool management for background operations,
preventing thread explosion and improving resource utilization.
"""

import logging
import threading
from concurrent.futures import ThreadPoolExecutor, Future
from typing import Callable, Optional, Any
from functools import wraps


class WASTThreadPool:
    """
    Centralized thread pool manager for WATS application.
    
    Benefits:
    - Prevents thread explosion
    - Automatic thread lifecycle management
    - Better resource utilization
    - Graceful shutdown handling
    """
    
    def __init__(
        self,
        max_workers_io: int = 5,
        max_workers_cpu: int = 3,
        thread_name_prefix: str = "WATS"
    ):
        """
        Initialize thread pool manager.
        
        Args:
            max_workers_io: Max threads for I/O-bound operations (DB, network)
            max_workers_cpu: Max threads for CPU-bound operations (processing)
            thread_name_prefix: Prefix for thread names
        """
        self.max_workers_io = max_workers_io
        self.max_workers_cpu = max_workers_cpu
        
        # Separate pools for different workload types
        self._io_pool = ThreadPoolExecutor(
            max_workers=max_workers_io,
            thread_name_prefix=f"{thread_name_prefix}-IO"
        )
        
        self._cpu_pool = ThreadPoolExecutor(
            max_workers=max_workers_cpu,
            thread_name_prefix=f"{thread_name_prefix}-CPU"
        )
        
        self._lock = threading.RLock()
        self._active_futures: set[Future] = set()
        self._shutdown = False
        
        logging.info(
            f"ThreadPool initialized: IO={max_workers_io}, CPU={max_workers_cpu}"
        )
    
    def submit_io_task(
        self,
        fn: Callable,
        *args,
        callback: Optional[Callable[[Future], None]] = None,
        **kwargs
    ) -> Future:
        """
        Submit an I/O-bound task (database, network, file I/O).
        
        Args:
            fn: Function to execute
            *args: Positional arguments
            callback: Optional callback when task completes
            **kwargs: Keyword arguments
            
        Returns:
            Future object
        """
        if self._shutdown:
            raise RuntimeError("ThreadPool is shut down")
        
        future = self._io_pool.submit(fn, *args, **kwargs)
        
        with self._lock:
            self._active_futures.add(future)
        
        # Add done callback to track completion
        def done_callback(f: Future):
            with self._lock:
                self._active_futures.discard(f)
            
            # Call user callback if provided
            if callback:
                try:
                    callback(f)
                except Exception as e:
                    logging.error(f"Error in user callback: {e}", exc_info=True)
        
        future.add_done_callback(done_callback)
        return future
    
    def submit_cpu_task(
        self,
        fn: Callable,
        *args,
        callback: Optional[Callable[[Future], None]] = None,
        **kwargs
    ) -> Future:
        """
        Submit a CPU-bound task (data processing, calculations).
        
        Args:
            fn: Function to execute
            *args: Positional arguments
            callback: Optional callback when task completes
            **kwargs: Keyword arguments
            
        Returns:
            Future object
        """
        if self._shutdown:
            raise RuntimeError("ThreadPool is shut down")
        
        future = self._cpu_pool.submit(fn, *args, **kwargs)
        
        with self._lock:
            self._active_futures.add(future)
        
        def done_callback(f: Future):
            with self._lock:
                self._active_futures.discard(f)
            
            if callback:
                try:
                    callback(f)
                except Exception as e:
                    logging.error(f"Error in user callback: {e}", exc_info=True)
        
        future.add_done_callback(done_callback)
        return future
    
    def get_active_task_count(self) -> int:
        """Get number of currently active tasks."""
        with self._lock:
            return len(self._active_futures)
    
    def shutdown(self, wait: bool = True, timeout: Optional[float] = None):
        """
        Shutdown the thread pools.
        
        Args:
            wait: If True, wait for all tasks to complete
            timeout: Maximum time to wait (seconds)
        """
        if self._shutdown:
            return
        
        self._shutdown = True
        active_count = self.get_active_task_count()
        
        logging.info(
            f"Shutting down ThreadPool... "
            f"Active tasks: {active_count}, Wait: {wait}"
        )
        
        try:
            self._io_pool.shutdown(wait=wait, cancel_futures=not wait)
            self._cpu_pool.shutdown(wait=wait, cancel_futures=not wait)
            logging.info("ThreadPool shut down successfully")
        except Exception as e:
            logging.error(f"Error during ThreadPool shutdown: {e}")
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.shutdown(wait=True, timeout=10.0)
    
    def __del__(self):
        """Destructor."""
        if not self._shutdown:
            self.shutdown(wait=False)


# Global thread pool instance
_global_thread_pool: Optional[WASTThreadPool] = None
_pool_lock = threading.Lock()


def get_thread_pool() -> WASTThreadPool:
    """
    Get or create the global thread pool instance.
    
    Returns:
        Global WASTThreadPool instance
    """
    global _global_thread_pool
    
    if _global_thread_pool is None:
        with _pool_lock:
            if _global_thread_pool is None:
                _global_thread_pool = WASTThreadPool(
                    max_workers_io=5,
                    max_workers_cpu=3
                )
    
    return _global_thread_pool


def shutdown_thread_pool(wait: bool = True, timeout: Optional[float] = 10.0):
    """
    Shutdown the global thread pool.
    
    Args:
        wait: If True, wait for all tasks to complete
        timeout: Maximum time to wait (seconds)
    """
    global _global_thread_pool
    
    if _global_thread_pool is not None:
        with _pool_lock:
            if _global_thread_pool is not None:
                _global_thread_pool.shutdown(wait=wait, timeout=timeout)
                _global_thread_pool = None


def async_io_task(callback_attr: Optional[str] = None):
    """
    Decorator to run a method as an async I/O task.
    
    Args:
        callback_attr: Optional attribute name for result callback
        
    Example:
        @async_io_task(callback_attr='_on_data_loaded')
        def load_data(self):
            return self.db.get_data()
    """
    def decorator(fn: Callable):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            pool = get_thread_pool()
            
            # Determine callback
            callback = None
            if callback_attr and args:
                callback_fn = getattr(args[0], callback_attr, None)
                if callback_fn:
                    def callback(future: Future):
                        try:
                            result = future.result()
                            callback_fn(result)
                        except Exception as e:
                            logging.error(f"Error in async task: {e}", exc_info=True)
            
            return pool.submit_io_task(fn, *args, callback=callback, **kwargs)
        
        return wrapper
    return decorator


def async_cpu_task(callback_attr: Optional[str] = None):
    """
    Decorator to run a method as an async CPU task.
    
    Args:
        callback_attr: Optional attribute name for result callback
    """
    def decorator(fn: Callable):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            pool = get_thread_pool()
            
            callback = None
            if callback_attr and args:
                callback_fn = getattr(args[0], callback_attr, None)
                if callback_fn:
                    def callback(future: Future):
                        try:
                            result = future.result()
                            callback_fn(result)
                        except Exception as e:
                            logging.error(f"Error in async task: {e}", exc_info=True)
            
            return pool.submit_cpu_task(fn, *args, callback=callback, **kwargs)
        
        return wrapper
    return decorator
