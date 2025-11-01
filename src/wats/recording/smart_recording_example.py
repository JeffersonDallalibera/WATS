# WATS_Project/wats_app/recording/smart_recording_example.py

"""
Exemplo de uso do sistema de gravação inteligente.
Demonstra como configurar e usar todas as funcionalidades avançadas.
Integrado com o sistema de configuração config.json do WATS.
"""

import json
import logging
import time
from pathlib import Path

from recording_manager import RecordingManager
from smart_recording_config import get_smart_recording_config, validate_smart_recording_config

# Configure logging
logging.basicConfig(level=logging.INFO)


class MockSettings:
    """Mock settings para demonstração."""

    def __init__(self):
        # Basic recording settings
        self.RECORDING_ENABLED = True
        self.RECORDING_OUTPUT_DIR = str(Path.home() / "Documents" / "WATS_Recordings")

        # Smart recording settings (podem ser sobrescritas pelo config.json)
        self.RECORDING_FPS = 30
        self.RECORDING_QUALITY = 75
        self.RECORDING_RESOLUTION_SCALE = 1.0

        # Window and activity settings
        self.RECORDING_WINDOW_TRACKING_INTERVAL = 1.0
        self.RECORDING_INACTIVITY_TIMEOUT_MINUTES = 5  # 5 minutos para teste
        self.RECORDING_PAUSE_ON_MINIMIZED = True
        self.RECORDING_PAUSE_ON_COVERED = True
        self.RECORDING_PAUSE_ON_INACTIVE = True
        self.RECORDING_CREATE_NEW_FILE_AFTER_PAUSE = True

        # File management
        self.RECORDING_MAX_DURATION_MINUTES = 10  # 10 minutos para teste
        self.RECORDING_MAX_FILE_SIZE_MB = 50  # 50MB para teste

        # Compression settings
        self.RECORDING_COMPRESSION_ENABLED = True
        self.RECORDING_COMPRESSION_CRF = 28

        # File rotation settings
        self.RECORDING_MAX_TOTAL_SIZE_GB = 1.0  # 1GB para teste
        self.RECORDING_MAX_FILE_AGE_DAYS = 7  # 7 dias para teste
        self.RECORDING_CLEANUP_INTERVAL_HOURS = 1  # 1 hora para teste

        # Debug settings
        self.RECORDING_DEBUG_WINDOW_TRACKING = True
        self.RECORDING_DEBUG_ACTIVITY_MONITORING = True

    def validate_recording_config(self):
        """Validação básica das configurações."""
        if not hasattr(self, "RECORDING_OUTPUT_DIR") or not self.RECORDING_OUTPUT_DIR:
            return False

        # Cria diretório se não existir
        Path(self.RECORDING_OUTPUT_DIR).mkdir(parents=True, exist_ok=True)
        return True


class MockWATSConfig:
    """Mock do sistema de configuração do WATS."""

    def __init__(self, config_file_path: str = None):
        self.config_data = {}
        if config_file_path and Path(config_file_path).exists():
            try:
                with open(config_file_path, "r", encoding="utf-8") as f:
                    self.config_data = json.load(f)
                print(f"✓ Loaded configuration from: {config_file_path}")
            except Exception as e:
                print(f"⚠️ Could not load config file: {e}")
                self.config_data = self._get_default_config()
        else:
            self.config_data = self._get_default_config()

    def _get_default_config(self):
        """Configuração padrão quando não há arquivo config.json."""
        return {
            "recording": {
                "enabled": True,
                "output_dir": str(Path.home() / "Documents" / "WATS_Recordings"),
                "fps": 30,
                "quality": 75,
                "smart_recording": {
                    "inactivity_timeout_minutes": 5,
                    "pause_on_minimized": True,
                    "pause_on_covered": True,
                    "debug_window_tracking": True,
                    "debug_activity_monitoring": True,
                },
            }
        }

    def get(self, key, default=None):
        """Simula o get_config() do WATS."""
        return self.config_data.get(key, default)


def demo_config_integration():
    """Demonstra integração com sistema de configuração."""

    print("=== Config.json Integration Demo ===\n")

    # 1. Try to load from config file
    config_file = Path(__file__).parent / "config_example.json"
    mock_config = MockWATSConfig(str(config_file))

    # 2. Create settings
    settings = MockSettings()

    # 3. Get combined configuration
    recording_config_dict = mock_config.get("recording", {})
    config = get_smart_recording_config(recording_config_dict, settings)

    print("📋 Configuration Sources:")
    print(f"   config.json: {config_file.exists()}")
    print("   settings overrides: Yes")
    print()

    print("🔧 Final Smart Recording Configuration:")
    key_configs = [
        "fps",
        "quality",
        "inactivity_timeout_minutes",
        "pause_on_minimized",
        "pause_on_covered",
        "debug_window_tracking",
    ]

    for key in key_configs:
        value = config.get(key, "Not set")
        source = (
            "config.json"
            if key in recording_config_dict.get("smart_recording", {})
            else "defaults/settings"
        )
        print(f"   {key}: {value} (from {source})")

    # 4. Validate configuration
    is_valid, errors = validate_smart_recording_config(config)
    print(f"\n✅ Configuration valid: {is_valid}")
    if errors:
        for error in errors:
            print(f"   ❌ {error}")

    return config, settings


def demo_smart_recording_with_config():
    """Demonstração completa com integração de configuração."""

    print("=== WATS Smart Recording with Config.json ===\n")

    # 1. Load and validate configuration
    config, settings = demo_config_integration()

    if not validate_smart_recording_config(config)[0]:
        print("❌ Configuration validation failed")
        return

    print()

    # 2. Initialize recording manager (will use config.json)
    print("Initializing RecordingManager with config.json integration...")
    recording_manager = RecordingManager(settings)

    # Set up callbacks for events
    def on_started(session_id):
        print(f"🎬 Recording STARTED for session: {session_id}")

    def on_stopped(session_id):
        print(f"🛑 Recording STOPPED for session: {session_id}")

    def on_paused(reason):
        print(f"⏸️  Recording PAUSED: {reason}")

    def on_resumed(reason):
        print(f"▶️  Recording RESUMED: {reason}")

    def on_error(session_id, error):
        print(f"❌ Recording ERROR for {session_id}: {error}")

    recording_manager.set_callbacks(
        on_started=on_started,
        on_stopped=on_stopped,
        on_paused=on_paused,
        on_resumed=on_resumed,
        on_error=on_error,
    )

    # Mock the get_config function for the recording manager
    import sys
    from types import ModuleType

    # Create mock config module
    mock_config_module = ModuleType("mock_config")
    mock_config_module.get_config = lambda: MockWATSConfig().config_data

    # Temporarily add to sys.modules (for demonstration)
    sys.modules["src.wats.config"] = mock_config_module

    if not recording_manager.initialize():
        print("❌ Failed to initialize recording manager")
        return

    print("✓ RecordingManager initialized with config.json integration")
    print()

    # 3. Rest of demo continues as before...
    connection_info = {
        "ip": "192.168.1.100:3389",
        "name": "Test-Server-RDP",
        "user": "test_user",
        "con_codigo": 12345,
        "connection_type": "rdp",
        "protocol": "RDP",
    }

    session_id = f"demo_session_{int(time.time())}"

    print(f"Starting intelligent recording for session: {session_id}")
    print(f"Target RDP: {connection_info['name']} ({connection_info['ip']})")
    print(f"Using timeout: {config['inactivity_timeout_minutes']} minutes")
    print()

    # Continue with the demo...
    if recording_manager.start_session_recording(session_id, connection_info):
        print("✓ Smart recording started with config.json settings!")
        print("   (Configuration loaded from config.json + settings overrides)")
        print()

        # Monitor for a short time
        print("Monitoring recording status (10 seconds)...")
        for i in range(10):
            status = recording_manager.get_recording_status()

            if status.get("is_recording"):
                state = status.get("state", "unknown")
                duration = status.get("total_duration", 0)
                print(f"[{i+1:2d}s] State: {state} | Duration: {duration:.1f}s")
            else:
                print(f"[{i+1:2d}s] Recording not active")

            time.sleep(1)

        print("\nStopping recording...")
        if recording_manager.stop_session_recording():
            print("✓ Recording stopped successfully")

    else:
        print("❌ Failed to start recording")

    # Cleanup
    recording_manager.shutdown()

    print("\n=== Demo Complete ===")
    print("Configuration was loaded from:")
    print("  1. config.json (if available)")
    print("  2. Settings object overrides")
    print("  3. Default values as fallback")
    """Demonstração do sistema de gravação inteligente."""

    print("=== WATS Smart Recording System Demo ===\n")

    # 1. Create settings and validate configuration
    settings = MockSettings()
    config = get_smart_recording_config(settings)

    is_valid, errors = validate_smart_recording_config(config)
    if not is_valid:
        print(f"Configuration errors: {errors}")
        return

    print("✓ Configuration validated successfully")
    print(f"✓ Recording output directory: {settings.RECORDING_OUTPUT_DIR}")
    print(f"✓ Inactivity timeout: {config['inactivity_timeout_minutes']} minutes")
    print(f"✓ Window tracking interval: {config['window_tracking_interval']} seconds")
    print()

    # 2. Initialize recording manager
    print("Initializing RecordingManager...")
    recording_manager = RecordingManager(settings)

    # Set up callbacks for events
    def on_started(session_id):
        print(f"🎬 Recording STARTED for session: {session_id}")

    def on_stopped(session_id):
        print(f"🛑 Recording STOPPED for session: {session_id}")

    def on_paused(reason):
        print(f"⏸️  Recording PAUSED: {reason}")

    def on_resumed(reason):
        print(f"▶️  Recording RESUMED: {reason}")

    def on_error(session_id, error):
        print(f"❌ Recording ERROR for {session_id}: {error}")

    recording_manager.set_callbacks(
        on_started=on_started,
        on_stopped=on_stopped,
        on_paused=on_paused,
        on_resumed=on_resumed,
        on_error=on_error,
    )

    if not recording_manager.initialize():
        print("❌ Failed to initialize recording manager")
        return

    print("✓ RecordingManager initialized successfully")
    print()

    # 3. Create mock connection info
    connection_info = {
        "ip": "192.168.1.100:3389",
        "name": "Test-Server-RDP",
        "user": "test_user",
        "con_codigo": 12345,
        "connection_type": "rdp",
        "protocol": "RDP",
    }

    session_id = f"demo_session_{int(time.time())}"

    print(f"Starting intelligent recording for session: {session_id}")
    print(f"Target RDP: {connection_info['name']} ({connection_info['ip']})")
    print()

    # 4. Start recording
    if recording_manager.start_session_recording(session_id, connection_info):
        print("✓ Smart recording started successfully!")
        print()

        # 5. Monitor recording status
        print("Monitoring recording status...")
        print("(Recording will automatically pause/resume based on window state and user activity)")
        print()

        try:
            for i in range(30):  # Monitor for 30 seconds
                status = recording_manager.get_recording_status()

                if status.get("is_recording"):
                    recording_info = status
                    state = recording_info.get("state", "unknown")
                    duration = recording_info.get("total_duration", 0)
                    segments = recording_info.get("segments_count", 0)

                    print(
                        f"[{i+1:2d}s] State: {state} | Duration: {duration:.1f}s | Segments: {segments}"
                    )

                    # Show window and activity info if available
                    window_info = recording_info.get("window_info")
                    if window_info:
                        window_state = window_info.get("state", "unknown")
                        print(f"      Window: {window_state}")

                    activity_info = recording_info.get("activity_info")
                    if activity_info:
                        is_active = activity_info.get("is_active", False)
                        time_since_activity = activity_info.get("time_since_last_activity", 0)
                        print(
                            f"      Activity: {'Active' if is_active else 'Inactive'} "
                            f"(last: {time_since_activity:.1f}s ago)"
                        )
                else:
                    print(f"[{i+1:2d}s] Recording not active")

                time.sleep(1)

        except KeyboardInterrupt:
            print("\nKeyboard interrupt received")

        print("\nStopping recording...")

        # 6. Stop recording
        if recording_manager.stop_session_recording():
            print("✓ Recording stopped successfully")
        else:
            print("❌ Error stopping recording")

    else:
        print("❌ Failed to start recording")

    # 7. Get final status and cleanup info
    print("\n=== Final Status ===")
    final_status = recording_manager.get_recording_status()
    print(f"Recording enabled: {final_status.get('enabled')}")
    print(f"Is recording: {final_status.get('is_recording')}")

    if "storage" in final_status:
        storage = final_status["storage"]
        print(f"Total files: {storage.get('total_files', 0)}")
        print(f"Total size: {storage.get('total_size_mb', 0):.2f} MB")

    # 8. Shutdown
    print("\nShutting down recording manager...")
    recording_manager.shutdown()
    print("✓ Shutdown complete")

    print("\n=== Demo Complete ===")
    print(f"Check recording files in: {settings.RECORDING_OUTPUT_DIR}")


def show_configuration_options():
    """Mostra todas as opções de configuração disponíveis."""

    print("=== Smart Recording Configuration Options ===\n")

    config = get_smart_recording_config()

    categories = {
        "Window Tracking": [
            "window_tracking_interval",
            "window_reacquisition_attempts",
            "window_reacquisition_delay",
        ],
        "Activity Monitoring": [
            "inactivity_timeout_minutes",
            "activity_detection_interval",
            "mouse_sensitivity",
        ],
        "Recording Behavior": [
            "pause_on_minimized",
            "pause_on_covered",
            "pause_on_inactive",
            "create_new_file_after_pause",
            "create_new_file_after_inactivity",
        ],
        "File Management": [
            "max_file_duration_minutes",
            "max_file_size_mb",
            "segment_naming_pattern",
        ],
        "Performance": [
            "fps",
            "quality",
            "resolution_scale",
            "compression_enabled",
            "compression_crf",
            "compression_preset",
        ],
        "Debug Options": [
            "debug_window_tracking",
            "debug_activity_monitoring",
            "save_activity_log",
            "save_window_state_log",
        ],
    }

    for category, settings in categories.items():
        print(f"{category}:")
        for setting in settings:
            value = config.get(setting, "Not set")
            print(f"  {setting}: {value}")
        print()


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        if sys.argv[1] == "config":
            show_configuration_options()
        elif sys.argv[1] == "config-demo":
            demo_config_integration()
        elif sys.argv[1] == "full":
            demo_smart_recording_with_config()
        else:
            print("Usage:")
            print("  python smart_recording_example.py           - Run basic demo")
            print("  python smart_recording_example.py config    - Show config options")
            print("  python smart_recording_example.py config-demo - Test config loading")
            print("  python smart_recording_example.py full      - Full demo with config.json")
    else:
        demo_smart_recording_with_config()
