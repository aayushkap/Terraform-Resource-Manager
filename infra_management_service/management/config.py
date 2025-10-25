import json
import threading
from pathlib import Path
from typing import Dict, Any
import time


class ConfigManager:
    def __init__(self, config_path: str = "scaling_config.json"):
        self.config_path = Path(config_path)
        self.config: Dict[str, Any] = {}
        self._lock = threading.RLock()
        self._last_modified = 0
        self._load_config()

        # Start config watcher thread
        self._watch_thread = threading.Thread(target=self._watch_config, daemon=True)
        self._watch_thread.start()

    def _load_config(self):
        """Load config from JSON file"""
        try:
            if self.config_path.exists():
                with self._lock:
                    self.config = json.loads(self.config_path.read_text())
                    self._last_modified = self.config_path.stat().st_mtime
                    print(f"> Configuration loaded: {self.config}")
        except Exception as e:
            print(f"> Error loading config: {e}")
            self._set_defaults()

    def _set_defaults(self):
        """Set default configuration."""
        with self._lock:
            self.config = {
                "mode": "AUTO",  # AUTO or MANUAL
                "min_containers": 1,
                "max_containers": 10,
                "thresholds": {"cpu": 70.0, "memory": 80.0, "requests_per_minute": 100},
                "scale_down_thresholds": {
                    "cpu": 30.0,
                    "memory": 40.0,
                    "requests_per_minute": 20,
                },
                "sustained_periods": {
                    "scale_up": 3,  # 3 consecutive checks above threshold
                    "scale_down": 5,  # 5 consecutive checks below threshold
                },
                "cooldown_seconds": 60,  # Min time between scaling operations
                "check_interval_seconds": 10,  # How often to evaluate metrics
                "strategy": "combined",  # cpu, memory, requests, combined, all
            }

    def _watch_config(self):
        """Watch for configuration file changes."""
        while True:
            try:
                if self.config_path.exists():
                    current_mtime = self.config_path.stat().st_mtime
                    if current_mtime != self._last_modified:
                        print("> Configuration file changed, reloading...")
                        self._load_config()
            except Exception as e:
                print(f"> Error watching config: {e}")
            time.sleep(2)

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value."""
        with self._lock:
            return self.config.get(key, default)

    def get_nested(self, *keys, default: Any = None) -> Any:
        """Get nested configuration value."""
        with self._lock:
            val = self.config
            for key in keys:
                if isinstance(val, dict):
                    val = val.get(key)
                else:
                    return default
            return val if val is not None else default
