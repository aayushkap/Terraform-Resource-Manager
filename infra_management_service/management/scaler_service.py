import subprocess
import threading
import queue
import docker
from typing import Optional
import time


class ScalerService:
    def __init__(self, config_manager, terraform_dir: str = "./terraform"):
        self.config = config_manager
        self.terraform_dir = terraform_dir

        self.docker_client = docker.DockerClient(
            base_url="npipe:////./pipe/docker_engine"
        )

        self.scaling_queue = queue.Queue()
        self._worker_thread = threading.Thread(target=self._scaling_worker, daemon=True)
        self._worker_thread.start()

        self._lock = threading.Lock()

    def _get_running_container_count(self, prefix: str = "fastapi-server") -> int:
        """Get actual count of running containers matching the prefix."""
        try:
            containers = self.docker_client.containers.list(
                filters={"status": "running"}
            )
            matching = [c for c in containers if c.name.startswith(prefix)]
            return len(matching)
        except Exception as e:
            print(f">  Error querying Docker: {e}")
            return 0

    def request_scale(self, action: str):
        """Add scaling request to queue."""
        self.scaling_queue.put(action)
        print(f"> Scaling request queued: {action}")

    def _scaling_worker(self):
        """Worker thread that processes scaling requests."""
        while True:
            try:
                action = self.scaling_queue.get(timeout=1)
                self._execute_scale(action)
                self.scaling_queue.task_done()
            except queue.Empty:
                continue
            except Exception as e:
                print(f"> Error in scaling worker: {e}")

    def _execute_scale(self, action: str):
        """Execute the scaling operation."""
        with self._lock:
            # Get ACTUAL current count from Docker
            current_count = self._get_running_container_count()
            print(f"> Current running containers: {current_count}")

            if action == "scale_up":
                new_count = current_count + 1
            elif action == "scale_down":
                new_count = current_count - 1
            else:
                print(f"> Unknown action: {action}")
                return

            # Bounds checking
            min_count = self.config.get("min_containers", 1)
            max_count = self.config.get("max_containers", 10)
            new_count = max(min_count, min(new_count, max_count))

            if new_count == current_count:
                print(
                    f">  Already at boundary (min={min_count}, max={max_count}), skipping {action}"
                )
                return

            print(f"> Executing {action}: {current_count} -> {new_count} containers")

            # Execute Terraform
            success = self._run_terraform(new_count)

            if success:
                print(f"> Scaling complete: {new_count} containers should be running")

                time.sleep(5)  # Wait for containers to start/stop
                actual_count = self._get_running_container_count()
                if actual_count == new_count:
                    print(f"> Verified: {actual_count} containers running")
                else:
                    print(
                        f">  Warning: Expected {new_count} but found {actual_count} containers"
                    )
            else:
                print(f"> Scaling failed")

    def _run_terraform(self, server_count: int) -> bool:
        """Run Terraform apply command."""
        try:
            cmd = [
                "docker-compose",
                "run",
                "--rm",
                "terraform",
                "apply",
                f"-var=server_count={server_count}",
                "-auto-approve",
            ]

            result = subprocess.run(
                cmd,
                cwd=self.terraform_dir,
                capture_output=True,
                text=True,
                timeout=300,  # 5 min timeout
            )

            if result.returncode == 0:
                return True
            else:
                print(f"> Terraform error: {result.stderr}")
                return False

        except subprocess.TimeoutExpired:
            print("> Terraform command timed out")
            return False
        except Exception as e:
            print(f"> Error running Terraform: {e}")
            return False

    def get_current_count(self) -> int:
        """Get current container count from Docker."""
        with self._lock:
            return self._get_running_container_count()
