import json
import threading
from pathlib import Path
from typing import Dict, Any
import time
from utils.logger_service import Logger


logger = Logger(__file__).get_logger()

from pydantic import BaseModel, Field
from typing import Literal


class Thresholds(BaseModel):
    cpu: float = Field(..., ge=0, le=100)
    memory: float = Field(..., ge=0, le=100)
    requests_per_minute: int = Field(..., ge=0)


class SustainedPeriods(BaseModel):
    scale_up: int = Field(..., ge=1)
    scale_down: int = Field(..., ge=1)


class ScalingConfig(BaseModel):
    mode: Literal["AUTO", "MANUAL"] = "AUTO"

    min_containers: int = Field(..., ge=1)
    max_containers: int = Field(..., ge=1)

    thresholds: Thresholds
    scale_down_thresholds: Thresholds

    sustained_periods: SustainedPeriods

    cooldown_seconds: int = Field(..., ge=1)
    check_interval_seconds: int = Field(..., ge=1)

    strategy: Literal["cpu", "memory", "rpm"] = "cpu"

    class Config:
        validate_assignment = True
        extra = "ignore"

    def get(self, key: str, default=None):
        return getattr(self, key, default)


class ConfigManager:
    def __init__(self, config_path: str = "scaling_config.json"):
        self.config_path = Path(config_path).resolve()  # Get absolute path
        self.config: Dict[str, Any] = {}
        self._lock = threading.RLock()
        self._last_modified = 0

        logger.info(f"Looking for config file at: {self.config_path}")
        logger.info(f"Current working directory: {Path.cwd()}")
        logger.info(f"Config file exists: {self.config_path.exists()}")

        self._load_config()

        # Start config watcher thread
        self._watch_thread = threading.Thread(target=self._watch_config, daemon=True)
        self._watch_thread.start()

    def _load_config(self):
        """Load config from JSON file"""
        try:

            if self.config_path.exists():
                with self._lock:
                    config_text = self.config_path.read_text()
                    logger.info(f"Config file content length: {len(config_text)} bytes")

                    if not config_text.strip():
                        logger.warning("Config file is empty, using defaults")
                        self._set_defaults()
                        self._save_config()
                        return

                    self.config = ScalingConfig(**json.loads(config_text))
                    self._last_modified = self.config_path.stat().st_mtime
                    logger.info(f"Configuration loaded successfully: {self.config}")
            else:
                logger.warning(
                    f"Config file not found at {self.config_path}, creating with defaults"
                )
                self._set_defaults()
                self._save_config()
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in config file: {e}")
            self._set_defaults()
            self._save_config()
        except Exception as e:
            logger.error(f"Error loading config: {e}", exc_info=True)
            self._set_defaults()

    def _set_defaults(self):
        """Set default configuration."""
        with self._lock:
            self.config = {
                "mode": "AUTO",
                "container_prefix": "fastapi-server",
                "min_containers": 1,
                "max_containers": 10,
                "thresholds": {"cpu": 70.0, "memory": 80.0, "requests_per_minute": 100},
                "scale_down_thresholds": {
                    "cpu": 30.0,
                    "memory": 40.0,
                    "requests_per_minute": 20,
                },
                "sustained_periods": {"scale_up": 3, "scale_down": 5},
                "cooldown_seconds": 60,
                "check_interval_seconds": 10,
                "strategy": "cpu",
            }
            logger.info(f"Default configuration set: {self.config}")

    def _save_config(self):
        """Save current config to file."""
        try:
            with self._lock:
                # Ensure directory exists
                self.config_path.parent.mkdir(parents=True, exist_ok=True)

                self.config_path.write_text(json.dumps(self.config, indent=2))
                logger.info(f"Configuration saved to {self.config_path}")
        except Exception as e:
            logger.error(f"Error saving config: {e}", exc_info=True)

    def _watch_config(self):
        """Watch for configuration file changes."""
        while True:
            try:
                if self.config_path.exists():
                    current_mtime = self.config_path.stat().st_mtime
                    if current_mtime != self._last_modified:
                        logger.info("Configuration file changed, reloading...")
                        self._load_config()
            except Exception as e:
                logger.error(f"Error watching config: {e}")
            time.sleep(2)

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value."""
        with self._lock:
            value = self.config.get(key, default)
            if value is None and default is not None:
                logger.warning(
                    f"Config key '{key}' not found, using default: {default}"
                )
            return value

    def get_nested(self, *keys, default: Any = None) -> Any:
        """Get nested configuration value."""
        with self._lock:
            val = self.config
            for key in keys:
                if isinstance(val, dict):
                    val = val.get(key)
                else:
                    logger.warning(
                        f"Config path {'.'.join(keys)} not found, using default: {default}"
                    )
                    return default
            return val if val is not None else default


# Run initial singleton instance which will be imported everywhere
config = ConfigManager()
