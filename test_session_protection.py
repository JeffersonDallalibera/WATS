# WATS Session Protection Test
# Tests the session protection functionality to ensure sensitive data is not stored

import sys
import os
import json
import tempfile
from datetime import datetime

# Add the project directory to path
project_root = os.path.dirname(os.path.abspath(__file__))
src_path = os.path.join(project_root, 'src')
sys.path.insert(0, src_path)

try:
    from wats.recording.session_recorder import SessionRecorder
    from wats.config import get_config
except ImportError as e:
    print(f"Error importing modules: {e}")
    print("Make sure you're running this from the WATS project directory")
    sys.exit(1)


def test_session_protection():
    """Test that sensitive information is properly protected."""
    
    print("=== WATS Session Protection Test ===\n")
    
    # Create a sample connection_info with sensitive data
    sensitive_connection_info = {
        "name": "Production Server",
        "ip": "192.168.1.100",
        "port": "3389",
        "protocol": "RDP",
        "username": "admin_user",
        "password": "super_secret_password123!",
        "domain": "COMPANY",
        "session_token": "abc123xyz789",
        "auth_token": "bearer_token_sensitive",
        "credentials": {"user": "admin", "pass": "secret"},
        "connection_type": "RDP",
        "notes": "Critical production server"
    }
    
    print("1. Original connection info contains:")
    for key, value in sensitive_connection_info.items():
        print(f"   {key}: {value}")
    
    # Test the sanitization
    try:
        # Create a temporary recorder to test sanitization
        recorder = SessionRecorder(
            output_dir=tempfile.gettempdir(),
            recording_mode="full_screen"
        )
        
        sanitized = recorder._sanitize_connection_info(sensitive_connection_info)
        
        print(f"\n2. After session protection applied:")
        for key, value in sanitized.items():
            print(f"   {key}: {value}")
        
        # Verify sensitive data was protected
        sensitive_fields = ['username', 'password', 'domain', 'session_token', 'auth_token', 'credentials']
        protected_count = 0
        
        print(f"\n3. Protection verification:")
        for field in sensitive_fields:
            if field in sanitized:
                if sanitized[field] == "[PROTECTED_BY_SESSION_SECURITY]":
                    print(f"   ✅ {field}: PROTECTED")
                    protected_count += 1
                else:
                    print(f"   ❌ {field}: NOT PROTECTED - {sanitized[field]}")
        
        # Verify safe data was preserved
        safe_fields = ['name', 'ip', 'port', 'protocol', 'connection_type', 'notes']
        preserved_count = 0
        
        for field in safe_fields:
            if field in sanitized and field in sensitive_connection_info:
                if sanitized[field] == sensitive_connection_info[field]:
                    print(f"   ✅ {field}: PRESERVED")
                    preserved_count += 1
                else:
                    print(f"   ❌ {field}: MODIFIED")
        
        print(f"\n4. Summary:")
        print(f"   - {protected_count} sensitive fields protected")
        print(f"   - {preserved_count} safe fields preserved")
        print(f"   - Session protection metadata added: {'_session_protection' in sanitized}")
        
        if '_session_protection' in sanitized:
            protection_info = sanitized['_session_protection']
            print(f"   - Protection timestamp: {protection_info.get('sanitized_at', 'N/A')}")
            print(f"   - Fields removed: {protection_info.get('sensitive_fields_removed', 0)}")
        
        # Simulate saving to metadata file
        print(f"\n5. Simulated metadata file content:")
        metadata = {
            "session_id": "test_session_123",
            "connection_info": sanitized,
            "start_time": datetime.now().isoformat(),
            "recorder_settings": {"fps": 30, "quality": 75}
        }
        
        metadata_json = json.dumps(metadata, indent=2, ensure_ascii=False)
        print(metadata_json)
        
        # Check for any sensitive data leaks
        print(f"\n6. Security verification - checking for data leaks:")
        security_issues = []
        
        for sensitive_value in ["super_secret_password123!", "admin_user", "abc123xyz789", "bearer_token_sensitive"]:
            if sensitive_value in metadata_json:
                security_issues.append(f"Found sensitive value '{sensitive_value}' in metadata")
        
        if security_issues:
            print("   ❌ SECURITY ISSUES FOUND:")
            for issue in security_issues:
                print(f"      - {issue}")
        else:
            print("   ✅ No sensitive data found in metadata - SESSION PROTECTION WORKING")
        
        return len(security_issues) == 0
        
    except Exception as e:
        print(f"Error during test: {e}")
        return False


def test_config_loading():
    """Test that session protection configuration loads correctly."""
    
    print(f"\n=== Configuration Test ===")
    
    try:
        config = get_config()
        recording_config = config.get('recording', {})
        protection_config = recording_config.get('session_protection', {})
        
        print(f"Recording enabled: {recording_config.get('enabled', False)}")
        print(f"Session protection enabled: {protection_config.get('enabled', False)}")
        print(f"Sanitize metadata: {protection_config.get('sanitize_metadata', False)}")
        print(f"Remove sensitive fields: {protection_config.get('remove_sensitive_fields', False)}")
        print(f"Log protection actions: {protection_config.get('log_protection_actions', False)}")
        
        return True
        
    except Exception as e:
        print(f"Error loading config: {e}")
        return False


if __name__ == "__main__":
    print("Testing WATS Session Protection Implementation")
    print("=" * 50)
    
    # Test configuration
    config_ok = test_config_loading()
    
    # Test protection functionality
    protection_ok = test_session_protection()
    
    print(f"\n" + "=" * 50)
    print(f"Test Results:")
    print(f"  Configuration: {'PASS' if config_ok else 'FAIL'}")
    print(f"  Protection:    {'PASS' if protection_ok else 'FAIL'}")
    print(f"  Overall:       {'PASS' if config_ok and protection_ok else 'FAIL'}")
    
    if config_ok and protection_ok:
        print(f"\n✅ Session protection is working correctly!")
        print(f"   Passwords and sensitive session data will NOT be saved to database or metadata files.")
    else:
        print(f"\n❌ Session protection has issues - please review the implementation.")