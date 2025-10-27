#!/usr/bin/env python3
"""
Test script for WATS API Upload System
Tests the complete recording upload functionality with mock server responses.
"""

import json
import logging
import sys
import time
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import tempfile
import os

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))

from src.wats.api import (
    RecordingUploadClient, UploadManager, UploadTask, UploadStatus,
    ApiIntegrationManager, ApiError, NetworkError, AuthenticationError
)


class TestRecordingUploadClient(unittest.TestCase):
    """Test the RecordingUploadClient class."""
    
    def setUp(self):
        self.client = RecordingUploadClient(
            api_base_url="https://test-api.company.com",
            api_token="test_token_123",
            timeout=30,
            max_retries=2
        )
        
        # Create test files
        self.test_dir = Path(tempfile.mkdtemp())
        self.video_file = self.test_dir / "test_session_123_TestServer_20241026_150000.mp4"
        self.metadata_file = self.test_dir / "test_session_123_metadata.json"
        
        # Create test video file (dummy content)
        with open(self.video_file, 'wb') as f:
            f.write(b"fake video content for testing" * 1000)  # ~30KB
        
        # Create test metadata file
        metadata = {
            "session_id": "test_session_123",
            "connection_info": {
                "con_codigo": 123,
                "ip": "192.168.1.100",
                "name": "Test Server",
                "user": "testuser",
                "connection_type": "RDP",
                "wats_user": "jefferson.silva",
                "wats_user_machine": "DESKTOP-TEST",
                "wats_user_ip": "192.168.1.50"
            },
            "start_time": "2024-10-26T15:00:00.123456",
            "recorder_settings": {
                "fps": 10,
                "quality": 23,
                "resolution_scale": 1.0,
                "max_file_size_mb": 100,
                "max_duration_minutes": 30
            }
        }
        
        with open(self.metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
    
    def tearDown(self):
        # Clean up test files
        import shutil
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    @patch('requests.Session.get')
    def test_connection_test_success(self, mock_get):
        """Test successful connection test."""
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        result = self.client.test_connection()
        self.assertTrue(result)
        mock_get.assert_called_once()
    
    @patch('requests.Session.get')
    def test_connection_test_failure(self, mock_get):
        """Test failed connection test."""
        import requests
        mock_get.side_effect = requests.exceptions.ConnectionError("Connection failed")
        
        result = self.client.test_connection()
        self.assertFalse(result)
    
    @patch('requests.Session.post')
    def test_upload_recording_success(self, mock_post):
        """Test successful recording upload."""
        # Mock API responses
        responses = [
            # Create session response
            Mock(json=lambda: {
                'session_id': 'upload_session_123',
                'metadata_upload_url': 'https://test-api.company.com/upload/metadata',
                'video_upload_url': 'https://test-api.company.com/upload/video'
            }),
            # Metadata upload response
            Mock(json=lambda: {'file_id': 'metadata_456'}),
            # Video upload response  
            Mock(json=lambda: {'file_id': 'video_789'}),
            # Finalize response
            Mock(json=lambda: {
                'file_id': 'recording_final_101112',
                'upload_url': 'https://storage.company.com/recordings/recording_final_101112',
                'status': 'completed'
            })
        ]
        
        for response in responses:
            response.raise_for_status.return_value = None
        
        mock_post.side_effect = responses
        
        result = self.client.upload_recording(
            self.video_file, 
            self.metadata_file,
            progress_callback=lambda sent, total: None
        )
        
        self.assertEqual(result['file_id'], 'recording_final_101112')
        self.assertEqual(result['status'], 'completed')
        self.assertEqual(mock_post.call_count, 4)
    
    def test_upload_missing_files(self):
        """Test upload with missing files."""
        missing_video = self.test_dir / "missing_video.mp4"
        missing_metadata = self.test_dir / "missing_metadata.json"
        
        with self.assertRaises(FileNotFoundError):
            self.client.upload_recording(missing_video, self.metadata_file)
        
        with self.assertRaises(FileNotFoundError):
            self.client.upload_recording(self.video_file, missing_metadata)


class TestUploadManager(unittest.TestCase):
    """Test the UploadManager class."""
    
    def setUp(self):
        self.mock_client = Mock(spec=RecordingUploadClient)
        self.test_dir = Path(tempfile.mkdtemp())
        self.state_file = self.test_dir / "test_upload_state.json"
        
        self.manager = UploadManager(
            upload_client=self.mock_client,
            max_retries=2,
            max_concurrent_uploads=1,
            state_file=self.state_file
        )
        
        # Create test files
        self.video_file = self.test_dir / "test_recording.mp4"
        self.metadata_file = self.test_dir / "test_metadata.json"
        
        with open(self.video_file, 'w') as f:
            f.write("test video content")
        
        with open(self.metadata_file, 'w') as f:
            json.dump({"session_id": "test_123"}, f)
    
    def tearDown(self):
        self.manager.stop()
        import shutil
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def test_queue_upload(self):
        """Test queuing an upload."""
        task_id = self.manager.queue_upload(self.video_file, self.metadata_file)
        
        self.assertIsNotNone(task_id)
        self.assertIn("upload_", task_id)
        
        status = self.manager.get_queue_status()
        self.assertEqual(status['queue_size'], 1)
    
    def test_upload_task_creation(self):
        """Test upload task creation and properties."""
        # Start the manager to process tasks
        self.manager.start()
        
        task_id = self.manager.queue_upload(self.video_file, self.metadata_file)
        
        # Wait a moment for processing
        time.sleep(0.2)
        
        task = self.manager.get_task_status(task_id)
        self.assertIsNotNone(task, f"Task {task_id} should exist in manager")


class TestApiIntegrationManager(unittest.TestCase):
    """Test the ApiIntegrationManager class."""
    
    def setUp(self):
        # Mock settings
        self.mock_settings = Mock()
        self.mock_settings.API_ENABLED = True
        self.mock_settings.API_BASE_URL = "https://test-api.company.com"
        self.mock_settings.API_TOKEN = "test_token_123"
        self.mock_settings.API_UPLOAD_TIMEOUT = 60
        self.mock_settings.API_MAX_RETRIES = 3
        self.mock_settings.API_MAX_CONCURRENT_UPLOADS = 2
        self.mock_settings.API_DELETE_AFTER_UPLOAD = False
        self.mock_settings.API_UPLOAD_OLDER_RECORDINGS = True
        self.mock_settings.API_MAX_FILE_AGE_DAYS = 30
        self.mock_settings.USER_DATA_DIR = tempfile.mkdtemp()
        self.mock_settings.validate_api_config.return_value = True
        
        # Create test files
        self.test_dir = Path(tempfile.mkdtemp())
        self.video_file = self.test_dir / "test_recording.mp4"
        self.metadata_file = self.test_dir / "test_metadata.json"
        
        with open(self.video_file, 'w') as f:
            f.write("test video content")
        
        with open(self.metadata_file, 'w') as f:
            json.dump({"session_id": "test_123"}, f)
    
    def tearDown(self):
        import shutil
        shutil.rmtree(self.test_dir, ignore_errors=True)
        shutil.rmtree(self.mock_settings.USER_DATA_DIR, ignore_errors=True)
    
    @patch('wats_app.api.api_integration.RecordingUploadClient')
    @patch('wats_app.api.api_integration.UploadManager')
    def test_initialization_success(self, mock_upload_manager_class, mock_client_class):
        """Test successful initialization."""
        # Mock successful client initialization
        mock_client = Mock()
        mock_client.test_connection.return_value = True
        mock_client_class.return_value = mock_client
        
        # Mock successful manager initialization
        mock_manager = Mock()
        mock_upload_manager_class.return_value = mock_manager
        
        integration = ApiIntegrationManager(self.mock_settings)
        
        self.assertTrue(integration.is_initialized)
        mock_client.test_connection.assert_called_once()
        mock_manager.start.assert_called_once()
    
    @patch('wats_app.api.api_integration.RecordingUploadClient')
    def test_initialization_connection_failure(self, mock_client_class):
        """Test initialization with connection failure."""
        # Mock failed client connection
        mock_client = Mock()
        mock_client.test_connection.return_value = False
        mock_client_class.return_value = mock_client
        
        integration = ApiIntegrationManager(self.mock_settings)
        
        self.assertFalse(integration.is_initialized)
    
    def test_disabled_api(self):
        """Test behavior when API is disabled."""
        self.mock_settings.API_ENABLED = False
        # Mock the validation to ensure it's not called when disabled
        self.mock_settings.validate_api_config = Mock(return_value=True)
        
        integration = ApiIntegrationManager(self.mock_settings)
        
        # Should still be "initialized" but with no actual components
        self.assertTrue(integration.is_initialized)
        self.assertIsNone(integration.upload_client)
        self.assertIsNone(integration.upload_manager)
        self.assertIsNone(integration.upload_client)
        self.assertIsNone(integration.upload_manager)


class TestApiErrorHandling(unittest.TestCase):
    """Test error handling in API components."""
    
    def test_api_error_types(self):
        """Test different API error types."""
        # Test base ApiError
        error = ApiError("Test error", 500)
        self.assertEqual(error.message, "Test error")
        self.assertEqual(error.status_code, 500)
        
        # Test specific error types
        auth_error = AuthenticationError("Auth failed")
        self.assertEqual(auth_error.status_code, 401)
        
        network_error = NetworkError("Network failed")
        self.assertEqual(network_error.status_code, 0)


def run_api_system_tests():
    """Run comprehensive API system tests."""
    print("🚀 WATS API Upload System - Test Suite")
    print("=" * 50)
    
    # Configure logging for tests
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add test classes
    test_classes = [
        TestRecordingUploadClient,
        TestUploadManager,
        TestApiIntegrationManager,
        TestApiErrorHandling
    ]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Print summary
    print("\n" + "=" * 50)
    print("📊 Test Results Summary:")
    print(f"✅ Tests run: {result.testsRun}")
    print(f"❌ Failures: {len(result.failures)}")
    print(f"💥 Errors: {len(result.errors)}")
    
    if result.failures:
        print("\n🔍 Failures:")
        for test, failure in result.failures:
            print(f"  - {test}: {failure}")
    
    if result.errors:
        print("\n💥 Errors:")
        for test, error in result.errors:
            print(f"  - {test}: {error}")
    
    success = len(result.failures) == 0 and len(result.errors) == 0
    
    if success:
        print("\n🎉 ALL TESTS PASSED! API upload system is working correctly.")
    else:
        print("\n⚠️  Some tests failed. Please review the issues above.")
    
    return success


def test_configuration_examples():
    """Test and demonstrate configuration examples."""
    print("\n🔧 API Configuration Examples:")
    print("-" * 30)
    
    # Example 1: Basic configuration
    print("Example 1 - Basic API Configuration:")
    basic_config = {
        "api": {
            "enabled": True,
            "base_url": "https://storage.company.com/api",
            "api_token": "your_api_token_here",
            "auto_upload": True,
            "upload_timeout": 60,
            "max_retries": 3,
            "max_concurrent_uploads": 2,
            "delete_after_upload": False,
            "upload_older_recordings": True,
            "max_file_age_days": 30
        }
    }
    print(json.dumps(basic_config, indent=2))
    
    # Example 2: High-volume configuration
    print("\nExample 2 - High-Volume Configuration:")
    high_volume_config = {
        "api": {
            "enabled": True,
            "base_url": "https://enterprise-storage.company.com/api",
            "api_token": "enterprise_token_here",
            "auto_upload": True,
            "upload_timeout": 120,
            "max_retries": 5,
            "max_concurrent_uploads": 4,
            "delete_after_upload": True,
            "upload_older_recordings": True,
            "max_file_age_days": 90
        }
    }
    print(json.dumps(high_volume_config, indent=2))
    
    # Example 3: Minimal configuration
    print("\nExample 3 - Minimal Configuration (disabled):")
    minimal_config = {
        "api": {
            "enabled": False
        }
    }
    print(json.dumps(minimal_config, indent=2))


if __name__ == "__main__":
    print("🧪 Starting WATS API Upload System Tests...")
    
    # Run configuration examples
    test_configuration_examples()
    
    # Run comprehensive tests
    success = run_api_system_tests()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)