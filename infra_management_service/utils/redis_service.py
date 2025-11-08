"""
Redis for state management
"""

import redis
import json
import time
from typing import Dict, List, Optional, Any
from utils.logger_service import Logger

logger = Logger(__file__).get_logger()


class RedisService:
    def __init__(self, host: str = "localhost", port: int = 6379, db: int = 0):
        """Initialize Redis connection."""
        try:
            self.client = redis.Redis(
                host=host,
                port=port,
                db=db,
                decode_responses=True,
                socket_connect_timeout=5,
            )
            self.client.ping()
            logger.info(f"Connected to Redis. {host}:{port}")
        except redis.ConnectionError as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise

    def set_system_status(self, status: str, action: str = "", details: Dict = None):
        """Set current system state."""
        state = {
            "status": status,
            "current_action": action,
            "last_update": time.time(),
            "details": details or {},
        }
        self.client.set("system:state", json.dumps(state))
        self.add_system_event(f"{status}: {action}" if action else status, details)

    def add_system_event(self, event: str, details: Dict = None):
        """Add system event to history."""
        event_data = {
            "timestamp": time.time(),
            "event": event,
            "details": details or {},
        }
        self.client.lpush("system:events", json.dumps(event_data))
        self.client.ltrim("system:events", 0, 99)  # Keep last 500 events

    def set_container_info(self, container_id: str, info: Dict):
        """Store container information."""
        key = f"container:{container_id}:info"
        self.client.set(key, json.dumps(info))
        self.client.sadd("containers:active", container_id)

        # Add to history
        history_key = f"container:{container_id}:history"
        event = {
            "timestamp": time.time(),
            "status": info.get("status"),
            "cpu": info.get("cpu"),
            "memory": info.get("memory"),
        }
        self.client.lpush(history_key, json.dumps(event))
        self.client.ltrim(history_key, 0, 99)  # Keep last 100 events

    def get_container_info(self, container_id: str) -> Optional[Dict]:
        """Get container information."""
        key = f"container:{container_id}:info"
        data = self.client.get(key)
        return json.loads(data) if data else None

    def remove_container(self, container_id: str):
        """Remove container from active set and delete all related keys."""
        self.client.srem("containers:active", container_id)
        key = f"container:{container_id}:info"
        history_key = f"container:{container_id}:history"
        self.client.delete(key)
        self.client.delete(history_key)
        logger.info(f"Removed container {container_id} from Redis")

    def get_all_containers(self) -> List[Dict]:
        """Get all active containers."""
        container_ids = self.client.smembers("containers:active")
        containers = []
        for cid in container_ids:
            info = self.get_container_info(cid)
            if info:
                containers.append(info)
        return containers

    def set_global_metrics(self, metrics: Dict):
        """Store current metrics and add full entry to unlimited history."""
        self.client.set("global:metrics", json.dumps(metrics))

        # Add to unlimited history
        history_entry = {"timestamp": time.time(), **metrics}
        self.client.lpush("test", json.dumps(history_entry))
        self.client.ltrim("test", 0, 99)  # keep latest 99 entries


    def get_global_metrics(self) -> Optional[Dict]:
        """Get latest global metrics snapshot."""
        data = self.client.get("global:metrics")
        return json.loads(data) if data else None

    def get_global_metrics_history(self, limit: int = 100) -> List[Dict]:
        """Get historical metrics with optional limit."""
        history = self.client.lrange("global:metrics:history:all", 0, limit - 1)
        return [json.loads(entry) for entry in history]

    def get_all_global_metrics_history(self) -> List[Dict]:
        """Get ALL historical metrics (no limit)."""
        count = self.client.llen("global:metrics:history:all")
        history = self.client.lrange("global:metrics:history:all", 0, count)
        return [json.loads(entry) for entry in history]

    def get_history_stats(self) -> Dict:
        """Get info about stored histories."""
        return {
            "global_metrics_history_count": self.client.llen(
                "global:metrics:history:all"
            ),
            "system_events_count": self.client.llen("system:events"),
        }

    def set_container_count(self, count: int):
        """Set current container count."""
        self.client.set("containers:count", count)

    def get_container_count(self) -> int:
        """Get current container count."""
        count = self.client.get("containers:count")
        return int(count) if count else 0

    def get_system_state(self) -> Dict:
        """Get current system state."""
        data = self.client.get("system:state")
        return json.loads(data) if data else {}

    def get_system_events(self, limit: int = 50) -> List[Dict]:
        """Get recent system events."""
        events = self.client.lrange("system:events", 0, limit - 1)
        return [json.loads(e) for e in events]

    def add_scaling_event(
        self,
        action: str,
        from_count: int,
        to_count: int,
        success: bool,
        details: Dict = None,
    ):
        """Record a scaling operation."""
        event = {
            "timestamp": time.time(),
            "action": action,
            "from_count": from_count,
            "to_count": to_count,
            "success": success,
            "details": details or {},
        }
        self.client.lpush("scaling:history", json.dumps(event))
        self.client.ltrim("scaling:history", 0, 99)  # Keep last 100 scaling events

        # Store last action
        self.client.set("scaling:last_action", json.dumps(event))

    def get_scaling_history(self, limit: int = 20) -> List[Dict]:
        """Get scaling history."""
        events = self.client.lrange("scaling:history", 0, limit - 1)
        return [json.loads(e) for e in events]

    def get_last_scaling_action(self) -> Optional[Dict]:
        """Get last scaling action."""
        data = self.client.get("scaling:last_action")
        return json.loads(data) if data else None

    def set_current_metrics(self, metrics: Dict):
        """Store current metrics."""
        self.client.set("metrics:current", json.dumps(metrics))

        # Store in history
        if "avg_cpu" in metrics:
            self.client.lpush("metrics:history:cpu", metrics["avg_cpu"])
            self.client.ltrim("metrics:history:cpu", 0, 99)

        if "avg_memory" in metrics:
            self.client.lpush("metrics:history:memory", metrics["avg_memory"])
            self.client.ltrim("metrics:history:memory", 0, 99)

    def get_current_metrics(self) -> Dict:
        """Get current metrics."""
        data = self.client.get("metrics:current")
        return json.loads(data) if data else {}

    def get_metrics_history(self, metric: str, limit: int = 50) -> List[float]:
        """Get metrics history."""
        key = f"metrics:history:{metric}"
        values = self.client.lrange(key, 0, limit - 1)
        return [float(v) for v in values]

    def set_analysis_state(self, state: Dict):
        """Store analysis state."""
        self.client.set("analysis:state", json.dumps(state))

    def get_analysis_state(self) -> Dict:
        """Get analysis state."""
        data = self.client.get("analysis:state")
        return json.loads(data) if data else {}

    def set_analysis_thresholds(self, thresholds: Dict):
        """Store current thresholds."""
        self.client.set("analysis:thresholds", json.dumps(thresholds))

    def get_analysis_thresholds(self) -> Dict:
        """Get current thresholds."""
        data = self.client.get("analysis:thresholds")
        return json.loads(data) if data else {}

    def clear_all(self):
        """Clear all autoscaler data."""
        patterns = [
            "container:*",
            "containers:*",
            "system:*",
            "scaling:*",
            "metrics:*",
            "analysis:*",
        ]
        for pattern in patterns:
            keys = self.client.keys(pattern)
            if keys:
                self.client.delete(*keys)
        logger.info("Redis data cleared")

    def get_stats(self) -> Dict:
        """Get Redis statistics."""
        return {
            "containers_active": self.client.scard("containers:active"),
            "system_events": self.client.llen("system:events"),
            "scaling_history": self.client.llen("scaling:history"),
            "memory_used": self.client.info("memory")["used_memory_human"],
        }
