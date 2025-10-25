"""
Centralized Docker service for querying container info and running CLI commands.
"""

import docker
import subprocess
from typing import List, Dict, Optional, Tuple
import time


class DockerService:
    def __init__(self, base_url: str = "npipe:////./pipe/docker_engine"):
        """
        Initialize Docker service.
        """
        self.base_url = base_url
        self.client = docker.DockerClient(base_url=base_url)

    def get_running_containers(
        self, name_prefix: Optional[str] = None
    ) -> List[docker.models.containers.Container]:
        """
        Get list of running containers.
        """
        try:
            containers = self.client.containers.list(filters={"status": "running"})
            if name_prefix:
                containers = [c for c in containers if c.name.startswith(name_prefix)]
            return containers
        except Exception as e:
            print(f"> Error getting running containers: {e}")
            return []

    def get_all_containers(
        self, name_prefix: Optional[str] = None
    ) -> List[docker.models.containers.Container]:
        """
        Get list of all containers (running + stopped).
        """
        try:
            containers = self.client.containers.list(all=True)
            if name_prefix:
                containers = [c for c in containers if c.name.startswith(name_prefix)]

            return containers
        except Exception as e:
            print(f"> Error getting all containers: {e}")
            return []

    def get_container_count(
        self, name_prefix: Optional[str] = None, status: str = "running"
    ) -> int:
        """
        Get count of containers matching criteria.
        """
        try:
            filters = {}
            if status:
                filters["status"] = status

            containers = self.client.containers.list(filters=filters, all=True)

            if name_prefix:
                containers = [c for c in containers if c.name.startswith(name_prefix)]

            return len(containers)
        except Exception as e:
            print(f"> Error counting containers: {e}")
            return 0

    def get_container_by_id(
        self, container_id: str
    ) -> Optional[docker.models.containers.Container]:
        """
        Get container by ID.

        :param container_id: Container ID (full or short)
        :return: Container object or None
        """
        try:
            return self.client.containers.get(container_id)
        except docker.errors.NotFound:
            print(f">  Container {container_id} not found")
            return None
        except Exception as e:
            print(f"> Error getting container {container_id}: {e}")
            return None

    def get_container_by_name(
        self, name: str
    ) -> Optional[docker.models.containers.Container]:
        """
        Get container by exact name.
        """
        try:
            containers = self.client.containers.list(all=True, filters={"name": name})
            return containers[0] if containers else None
        except Exception as e:
            print(f"> Error getting container by name {name}: {e}")
            return None

    def get_container_status(self, container_id: str) -> str:
        """
        Get current status of a container.
        """
        try:
            container = self.client.containers.get(container_id)
            container.reload()
            return container.attrs["State"]["Status"]
        except docker.errors.NotFound:
            return "removed"
        except Exception as e:
            print(f"> Error getting container status: {e}")
            return "unknown"

    def get_container_logs(
        self, container_id: str, tail: int = 100, timestamps: bool = False
    ) -> str:
        """
        Get recent logs from a container.
        """
        try:
            container = self.client.containers.get(container_id)
            logs = container.logs(tail=tail, timestamps=timestamps).decode("utf-8")
            return logs.strip()
        except Exception as e:
            print(f"> Error getting logs for {container_id}: {e}")
            return ""

    def run_docker_command(
        self, args: List[str], capture_output: bool = True, timeout: int = 60
    ) -> Tuple[bool, str, str]:
        """
        Run a docker CLI command.

        :param args: Command arguments (e.g., ["ps", "-a"])
        :param capture_output: Whether to capture stdout/stderr
        :param timeout: Command timeout in seconds
        :return: (success, stdout, stderr)
        """
        try:
            result = subprocess.run(
                ["docker"] + args,
                capture_output=capture_output,
                text=True,
                timeout=timeout,
                check=False,
            )

            success = result.returncode == 0
            return success, result.stdout, result.stderr

        except subprocess.TimeoutExpired:
            return False, "", "Command timed out"
        except Exception as e:
            return False, "", str(e)

    def run_docker_compose_command(
        self,
        args: List[str],
        working_dir: str = ".",
        capture_output: bool = True,
        timeout: int = 300,
    ) -> Tuple[bool, str, str]:
        """
        Run a docker-compose CLI command.

        :param args: Command arguments (e.g., ["up", "-d"])
        :param working_dir: Directory containing docker-compose.yml
        :param capture_output: Whether to capture stdout/stderr
        :param timeout: Command timeout in seconds
        :return: (success, stdout, stderr)
        """
        try:
            result = subprocess.run(
                ["docker-compose"] + args,
                cwd=working_dir,
                capture_output=capture_output,
                text=True,
                timeout=timeout,
                check=False,
            )

            success = result.returncode == 0
            return success, result.stdout, result.stderr

        except subprocess.TimeoutExpired:
            return False, "", "Command timed out"
        except Exception as e:
            return False, "", str(e)

    def start_container(self, container_id: str) -> bool:
        """Start a stopped container."""
        try:
            container = self.client.containers.get(container_id)
            container.start()
            return True
        except Exception as e:
            print(f"> Error starting container {container_id}: {e}")
            return False

    def stop_container(self, container_id: str, timeout: int = 10) -> bool:
        """Stop a running container."""
        try:
            container = self.client.containers.get(container_id)
            container.stop(timeout=timeout)
            return True
        except Exception as e:
            print(f"> Error stopping container {container_id}: {e}")
            return False

    def restart_container(self, container_id: str, timeout: int = 10) -> bool:
        """Restart a container."""
        try:
            container = self.client.containers.get(container_id)
            container.restart(timeout=timeout)
            return True
        except Exception as e:
            print(f"> Error restarting container {container_id}: {e}")
            return False

    def remove_container(self, container_id: str, force: bool = False) -> bool:
        """Remove a container."""
        try:
            container = self.client.containers.get(container_id)
            container.remove(force=force)
            return True
        except Exception as e:
            print(f"> Error removing container {container_id}: {e}")
            return False

    def get_docker_info(self) -> Dict:
        """Get Docker system information."""
        try:
            return self.client.info()
        except Exception as e:
            print(f"> Error getting Docker info: {e}")
            return {}

    def ping(self) -> bool:
        """Check if Docker daemon is accessible."""
        try:
            self.client.ping()
            return True
        except Exception as e:
            print(f"> Docker daemon not accessible: {e}")
            return False
