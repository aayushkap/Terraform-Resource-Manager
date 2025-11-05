"""
Decision engine
"""

import time
from collections import deque
from typing import Dict, List, Optional
import threading
from utils.logger_service import Logger

logger = Logger(__file__).get_logger()


class MetricsAnalyzer:
    def __init__(self, config_manager):
        self.config = config_manager
        self._lock = threading.RLock() # Allows for recursion depth. Re-entrant.

        # Sliding window for sustained metrics
        self.cpu_history = deque(maxlen=10)
        self.memory_history = deque(maxlen=10)
        self.requests_history = deque(maxlen=10)

        # Consecutive threshold breaches
        self.scale_up_streak = 0
        self.scale_down_streak = 0

        # Cooldown tracking
        self.last_scale_time = 0
        self.current_container_count = 1

    def analyze(self, metrics: List[Dict]) -> Optional[str]:
        """
        Analyze metrics and return scaling decision.
        Returns: 'scale_up', 'scale_down', or None
        """
        logger.info("Beginning Analysis")
        if not metrics or self.config.get("mode") != "AUTO":
            logger.info("Stopping Analysis: Not Auto")
            return None

        if not metrics or self.config.get("mode") != "AUTO":
            logger.info("Stopping Analysis: No Metrics")
            return None

        running = [m for m in metrics if m.get("status") == "running"]
        if not running:
            logger.warning("Stopping Analysis: No running container")
            return None

        with self._lock:
            # Calculate aggregate metrics
            avg_cpu = sum(m.get("cpu", 0) for m in running) / len(running)
            avg_memory = sum(m.get("memory", 0) for m in running) / len(running)
            avg_requests = sum(m.get("req_per_min", 0) for m in running) / len(running)

            # Add to history
            self.cpu_history.append(avg_cpu)
            self.memory_history.append(avg_memory)
            self.requests_history.append(avg_requests)

            # Update current count
            self.current_container_count = len(running)

            # Check cooldown
            if time.time() - self.last_scale_time < self.config.get(
                "cooldown_seconds", 60
            ):
                return None

            # Scaling decision based on strategy
            strategy = self.config.get("strategy", "combined")
            logger.info(f"Using Strategy: {strategy}")
            if strategy == "cpu":
                return self._analyze_cpu()
            elif strategy == "memory":
                return self._analyze_memory()
            elif strategy == "requests":
                return self._analyze_requests()
            elif strategy == "combined":
                return self._analyze_combined()
            elif strategy == "all":
                return self._analyze_all()

            return None

    def _analyze_cpu(self) -> Optional[str]:
        """CPU"""
        if len(self.cpu_history) < 3:
            logger.info(f"No decision: Not enough CPU history")
            return None

        recent_avg = sum(list(self.cpu_history)[-3:]) / 3

        cpu_threshold = self.config.get_nested("thresholds", "cpu", default=70)
        cpu_scale_down = self.config.get_nested(
            "scale_down_thresholds", "cpu", default=30
        )

        logger.info(f"CPU recent_avg: {recent_avg}. cpu_threshold: {cpu_threshold}")

        if recent_avg > cpu_threshold:

            self.scale_up_streak += 1
            self.scale_down_streak = 0

            sustained_up = self.config.get_nested(
                "sustained_periods", "scale_up", default=3
            )
            if self.scale_up_streak >= sustained_up:
                return self._check_and_scale_up()

        elif recent_avg < cpu_scale_down:

            self.scale_down_streak += 1
            self.scale_up_streak = 0

            sustained_down = self.config.get_nested(
                "sustained_periods", "scale_down", default=5
            )
            if self.scale_down_streak >= sustained_down:
                return self._check_and_scale_down()

        else:
            logger.info(f"Stable. Will not scale.")
            self.scale_up_streak = 0
            self.scale_down_streak = 0

        return None

    def _analyze_memory(self) -> Optional[str]:
        """Memory."""
        if len(self.memory_history) < 3:
            return None

        recent_avg = sum(list(self.memory_history)[-3:]) / 3

        mem_threshold = self.config.get_nested("thresholds", "memory", default=80)
        mem_scale_down = self.config.get_nested(
            "scale_down_thresholds", "memory", default=40
        )

        if recent_avg > mem_threshold:
            self.scale_up_streak += 1
            self.scale_down_streak = 0

            sustained_up = self.config.get_nested(
                "sustained_periods", "scale_up", default=3
            )
            if self.scale_up_streak >= sustained_up:
                return self._check_and_scale_up()

        elif recent_avg < mem_scale_down:
            self.scale_down_streak += 1
            self.scale_up_streak = 0

            sustained_down = self.config.get_nested(
                "sustained_periods", "scale_down", default=5
            )
            if self.scale_down_streak >= sustained_down:
                return self._check_and_scale_down()

        else:
            self.scale_up_streak = 0
            self.scale_down_streak = 0

        return None

    def _analyze_requests(self) -> Optional[str]:
        """Requests per minute."""
        if len(self.requests_history) < 3:
            return None

        recent_avg = sum(list(self.requests_history)[-3:]) / 3

        req_threshold = self.config.get_nested(
            "thresholds", "requests_per_minute", default=100
        )
        req_scale_down = self.config.get_nested(
            "scale_down_thresholds", "requests_per_minute", default=20
        )

        if recent_avg > req_threshold:
            self.scale_up_streak += 1
            self.scale_down_streak = 0

            sustained_up = self.config.get_nested(
                "sustained_periods", "scale_up", default=3
            )
            if self.scale_up_streak >= sustained_up:
                return self._check_and_scale_up()

        elif recent_avg < req_scale_down:
            self.scale_down_streak += 1
            self.scale_up_streak = 0

            sustained_down = self.config.get_nested(
                "sustained_periods", "scale_down", default=5
            )
            if self.scale_down_streak >= sustained_down:
                return self._check_and_scale_down()

        else:
            self.scale_up_streak = 0
            self.scale_down_streak = 0

        return None

    def _analyze_combined(self) -> Optional[str]:
        """Weighted combination of CPU and memory."""
        if len(self.cpu_history) < 3 or len(self.memory_history) < 3:
            return None

        recent_cpu = sum(list(self.cpu_history)[-3:]) / 3
        recent_mem = sum(list(self.memory_history)[-3:]) / 3

        # Weighted score of 60% CPU, 40% memory
        combined_score = (recent_cpu * 0.6) + (recent_mem * 0.4)

        cpu_threshold = self.config.get_nested("thresholds", "cpu", default=70)
        mem_threshold = self.config.get_nested("thresholds", "memory", default=80)
        combined_threshold = (cpu_threshold * 0.6) + (mem_threshold * 0.4)

        cpu_scale_down = self.config.get_nested(
            "scale_down_thresholds", "cpu", default=30
        )
        mem_scale_down = self.config.get_nested(
            "scale_down_thresholds", "memory", default=40
        )
        combined_scale_down = (cpu_scale_down * 0.6) + (mem_scale_down * 0.4)

        if combined_score > combined_threshold:
            self.scale_up_streak += 1
            self.scale_down_streak = 0

            sustained_up = self.config.get_nested(
                "sustained_periods", "scale_up", default=3
            )
            if self.scale_up_streak >= sustained_up:
                return self._check_and_scale_up()

        elif combined_score < combined_scale_down:
            self.scale_down_streak += 1
            self.scale_up_streak = 0

            sustained_down = self.config.get_nested(
                "sustained_periods", "scale_down", default=5
            )
            if self.scale_down_streak >= sustained_down:
                return self._check_and_scale_down()

        else:
            self.scale_up_streak = 0
            self.scale_down_streak = 0

        return None

    def _analyze_all(self) -> Optional[str]:
        """Any metric breache"""
        if len(self.cpu_history) < 3:
            return None

        recent_cpu = sum(list(self.cpu_history)[-3:]) / 3
        recent_mem = sum(list(self.memory_history)[-3:]) / 3
        recent_req = (
            sum(list(self.requests_history)[-3:]) / 3 if self.requests_history else 0
        )

        cpu_threshold = self.config.get_nested("thresholds", "cpu", default=70)
        mem_threshold = self.config.get_nested("thresholds", "memory", default=80)
        req_threshold = self.config.get_nested(
            "thresholds", "requests_per_minute", default=100
        )

        breach_up = (
            recent_cpu > cpu_threshold
            or recent_mem > mem_threshold
            or recent_req > req_threshold
        )

        cpu_scale_down = self.config.get_nested(
            "scale_down_thresholds", "cpu", default=30
        )
        mem_scale_down = self.config.get_nested(
            "scale_down_thresholds", "memory", default=40
        )
        req_scale_down = self.config.get_nested(
            "scale_down_thresholds", "requests_per_minute", default=20
        )

        breach_down = (
            recent_cpu < cpu_scale_down
            and recent_mem < mem_scale_down
            and recent_req < req_scale_down
        )

        if breach_up:
            self.scale_up_streak += 1
            self.scale_down_streak = 0

            sustained_up = self.config.get_nested(
                "sustained_periods", "scale_up", default=3
            )
            if self.scale_up_streak >= sustained_up:
                return self._check_and_scale_up()

        elif breach_down:
            self.scale_down_streak += 1
            self.scale_up_streak = 0

            sustained_down = self.config.get_nested(
                "sustained_periods", "scale_down", default=5
            )
            if self.scale_down_streak >= sustained_down:
                return self._check_and_scale_down()

        else:
            self.scale_up_streak = 0
            self.scale_down_streak = 0

        return None

    def _check_and_scale_up(self) -> Optional[str]:
        """Check if we can scale up"""
        max_containers = self.config.get("max_containers", 10)
        if self.current_container_count < max_containers:
            self.last_scale_time = time.time()
            self.scale_up_streak = 0
            return "scale_up"
        else:
            logger.info("Will not Scale up: Max Containers reached.")
        return None

    def _check_and_scale_down(self) -> Optional[str]:
        """Check if we can scale down."""
        min_containers = self.config.get("min_containers", 1)
        if self.current_container_count > min_containers:
            self.last_scale_time = time.time()
            self.scale_down_streak = 0
            return "scale_down"
        else:
            logger.info("Will not Scale down: Min Containers reached.")
        return None
