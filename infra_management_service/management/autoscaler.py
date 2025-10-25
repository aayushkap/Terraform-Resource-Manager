"""
Main orchestrator
"""

import asyncio
import json
from config import ConfigManager
from metrics_analyzer import MetricsAnalyzer
from scaler_service import ScalerService


class AutoScaler:
    def __init__(self, monitoring_service, terraform_dir: str = "./terraform"):
        self.monitor = monitoring_service
        self.config = ConfigManager()
        self.analyzer = MetricsAnalyzer(self.config)
        self.scaler = ScalerService(self.config, terraform_dir)

        self._running = False

    async def start(self):
        """Start the autoscaling loop."""
        self._running = True
        print("> AutoScaler started")

        while self._running:
            try:
                metrics = self.monitor.get_data()
                if not metrics:
                    print("> Waiting for metrics data")
                    await asyncio.sleep(5)
                    continue

                decision = self.analyzer.analyze(metrics)
                if decision:
                    print(f"> Scaling decision: {decision}")
                    self.scaler.request_scale(decision)

                check_interval = self.config.get("check_interval_seconds", 5)
                await asyncio.sleep(check_interval)

            except Exception as e:
                print(f"> Error in autoscaler loop: {e}")
                await asyncio.sleep(5)

    def stop(self):
        """Stop the autoscaling loop."""
        self._running = False
        print("> AutoScaler stopped")
