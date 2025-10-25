import docker
import threading
import json
import time


class MonitoringService:
    def __init__(
        self,
        base_url="npipe:////./pipe/docker_engine",
        cleanup_removed=True,
    ):
        self.client = docker.DockerClient(base_url=base_url)
        self.containers_data = {}  # keyed by container name
        self._lock = threading.Lock()
        self._container_threads = {}  # keyed by container ID
        self._running = False
        self._event_thread = None
        self.cleanup_removed = cleanup_removed

    def _get_container_status(self, container_id):
        """Fetch current container status from Docker daemon."""
        try:
            container = self.client.containers.get(container_id)
            container.reload()
            return container.attrs["State"]["Status"]
        except docker.errors.NotFound:
            return "removed"
        except Exception:
            return "unknown"

    def _get_container_logs(self, container_id, tail=20):
        """Fetch recent container logs."""
        try:
            container = self.client.containers.get(container_id)
            logs = container.logs(tail=tail, timestamps=False).decode("utf-8")
            return logs.strip()
        except Exception:
            return ""

    def _monitor_container(self, container):
        """Continuously monitor a single container's resource stats."""
        try:
            # stream=True gives us continuous stats updates (~1 second intervals)
            stats_stream = container.stats(stream=True)

            for raw_stats in stats_stream:
                if not self._running or container.id not in self._container_threads:
                    break

                if isinstance(raw_stats, bytes):
                    raw_stats = raw_stats.decode("utf-8")
                stats = json.loads(raw_stats)

                # CPU calculation
                cpu_total = stats["cpu_stats"]["cpu_usage"]["total_usage"]
                cpu_precpu_total = stats["precpu_stats"]["cpu_usage"].get(
                    "total_usage", 0
                )
                cpu_delta = cpu_total - cpu_precpu_total

                system_total = stats["cpu_stats"].get("system_cpu_usage", 0)
                precpu_system_total = stats["precpu_stats"].get("system_cpu_usage", 0)
                system_delta = system_total - precpu_system_total

                online_cpus = stats["cpu_stats"].get("online_cpus", 1)

                # Proper CPU percentage calculation
                if system_delta > 0 and cpu_delta > 0:
                    cpu_percent = (cpu_delta / system_delta) * online_cpus * 100.0
                else:
                    cpu_percent = 0.0

                # Memory calculation
                mem_usage = stats["memory_stats"].get("usage", 0)
                mem_limit = stats["memory_stats"].get("limit", 1)
                mem_percent = (mem_usage / mem_limit) * 100

                status = self._get_container_status(container.id)
                logs = self._get_container_logs(container.id, tail=10)

                data = {
                    "id": container.id[:12],
                    "name": container.name,
                    "status": status,
                    "cpu": round(cpu_percent, 2),
                    "memory": round(mem_percent, 2),
                    "timestamp": time.time(),
                    "logs": logs,
                }

                with self._lock:
                    self.containers_data[container.name] = data

                # `Note:` Do not add sleep here, it messes with the Docker stream and ruins the CPU calculation.

        except Exception as e:
            # On exception mark container with last known status
            with self._lock:
                if container.name in self.containers_data:
                    self.containers_data[container.name]["status"] = (
                        self._get_container_status(container.id)
                    )

    def _watch_for_new_containers(self):
        """Listen to Docker events and start/stop monitoring accordingly."""
        events = self.client.events(decode=True)
        for event in events:
            if not self._running:
                break

            if event.get("Type") == "container":
                status = event.get("status")
                container_id = event.get("id")

                # On start of new containers
                if status in ("start", "create"):
                    try:
                        container = self.client.containers.get(container_id)
                        if container.id not in self._container_threads:
                            t = threading.Thread(
                                target=self._monitor_container,
                                args=(container,),
                                daemon=True,
                            )
                            t.start()
                            self._container_threads[container.id] = t
                    except Exception:
                        continue

                # On container stop
                elif status in ("die", "stop", "kill"):
                    try:
                        container = self.client.containers.get(container_id)
                        with self._lock:
                            if container.name in self.containers_data:
                                self.containers_data[container.name][
                                    "status"
                                ] = "exited"
                                self.containers_data[container.name]["cpu"] = 0.0
                                self.containers_data[container.name]["memory"] = 0.0
                                self.containers_data[container.name][
                                    "timestamp"
                                ] = time.time()
                    except Exception:
                        pass
                    self._container_threads.pop(container_id, None)

                elif status == "destroy":
                    try:
                        container = self.client.containers.get(container_id)
                        container_name = container.name
                    except Exception:
                        container_name = None
                        with self._lock:
                            for name, data in self.containers_data.items():
                                if data.get("id") == container_id[:12]:
                                    container_name = name
                                    break

                    if container_name:
                        if self.cleanup_removed:
                            with self._lock:
                                self.containers_data.pop(container_name, None)
                        else:
                            with self._lock:
                                if container_name in self.containers_data:
                                    self.containers_data[container_name][
                                        "status"
                                    ] = "removed"
                                    self.containers_data[container_name][
                                        "timestamp"
                                    ] = time.time()

                    self._container_threads.pop(container_id, None)

    def start(self):
        """Start monitoring existing containers and watch for new ones."""
        self._running = True

        # Start monitoring all currently running containers
        for container in self.client.containers.list():
            t = threading.Thread(
                target=self._monitor_container, args=(container,), daemon=True
            )
            t.start()
            self._container_threads[container.id] = t

        # Also track stopped containers (without monitoring thread)
        for container in self.client.containers.list(all=True):
            if (
                container.status != "running"
                and container.name not in self.containers_data
            ):
                with self._lock:
                    self.containers_data[container.name] = {
                        "id": container.id[:12],
                        "name": container.name,
                        "status": container.status,
                        "cpu": 0.0,
                        "memory": 0.0,
                        "timestamp": time.time(),
                        "logs": "",
                    }

        # Start Docker event watcher thread
        self._event_thread = threading.Thread(
            target=self._watch_for_new_containers, daemon=True
        )
        self._event_thread.start()

    def stop(self):
        self._running = False
        if self._event_thread:
            self._event_thread.join()

        for t in self._container_threads.values():
            t.join()

    def get_data(self, clear_after_get=False):
        """Return the latest container stats as JSON."""
        with self._lock:
            data = json.dumps(list(self.containers_data.values()))
            if clear_after_get:
                self.containers_data.clear()
            return data
