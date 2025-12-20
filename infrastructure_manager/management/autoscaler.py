"""
Main orchestrator
"""

import asyncio
import json
from utils.config_service import config
from management.metrics_analyzer import MetricsAnalyzer
from management.scaler_service import ScalerService
from utils.logger_service import Logger

logger = Logger(__file__).get_logger()


class AutoScaler:
    def __init__(self, monitoring_service, terraform_dir: str = "./terraform"):
        self.monitor = monitoring_service
        # self.config.print_config()
        self.analyzer = MetricsAnalyzer(config)
        self.scaler = ScalerService(config, terraform_dir)

        self._running = False

    async def start(self):
        """Start the autoscaling loop."""
        self._running = True
        logger.info("AutoScaler started")

        while self._running:
            try:
                metrics = self.monitor.get_data()
                if not metrics:
                    logger.info("Waiting for metrics data")
                    await asyncio.sleep(5)
                    continue

                decision = self.analyzer.analyze(metrics)
                if decision:
                    logger.info(f"Scaling decision: {decision}")
                    self.scaler.request_scale(decision)

                print("config.config", config.config)
                check_interval = config.get("check_interval_seconds", 5)
                await asyncio.sleep(check_interval)

            except Exception as e:
                logger.error(f"Error in autoscaler loop: {e}")
                await asyncio.sleep(5)

    def stop(self):
        """Stop the autoscaling loop."""
        self._running = False
        logger.info("AutoScaler stopped")
