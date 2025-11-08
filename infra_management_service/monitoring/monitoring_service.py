import docker
import threading
import json
import time
from utils.redis_service import RedisService


class MonitoringService:
    def __init__(
        self,
        base_url="npipe:////./pipe/docker_engine",
        state_validation_interval=15,  # validate container state every 30s
    ):
        self.client = docker.DockerClient(base_url=base_url)
        self.redis = RedisService()
        self.redis.clear_all()
        self.redis.set_system_status("initializing", "Starting monitoring service")

        self.containers_data = {}
        self._lock = threading.Lock()
        self._container_threads = {}
        self._running = False
        self._event_thread = None
        self._validation_thread = None
        self.container_prefix = "fastapi-server"
        self.state_validation_interval = state_validation_interval

    def _get_container_status(self, container_id):
        """Fetch current container status from Docker daemon"""
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
        """Continuously monitor a single container's resource utilization"""
        try:
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

                self.redis.set_container_info(container.id[:12], data)

                # If container died during stats collection, break loop
                if status in ("exited", "stopped", "removed"):
                    break

        except StopIteration:
            # container death
            self._handle_container_death(container)
        except Exception as e:
            self._handle_container_death(container)

    def _handle_container_death(self, container):
        """Handle container death"""
        try:
            current_status = self._get_container_status(container.id)
        except Exception:
            current_status = "removed"

        with self._lock:
            if container.name in self.containers_data:
                self.containers_data[container.name].update(
                    {
                        "status": current_status,
                        "cpu": 0.0,
                        "memory": 0.0,
                        "timestamp": time.time(),
                    }
                )

        self.redis.set_container_info(
            container.id[:12],
            {
                "id": container.id[:12],
                "name": container.name,
                "status": current_status,  # "exited", "stopped", "removed"
                "cpu": 0.0,
                "memory": 0.0,
                "timestamp": time.time(),
                "logs": "",
            },
        )

        self._container_threads.pop(container.id, None)

    def _validate_container_state(self):
        """Reconcile Redis state with actual Docker state"""
        while self._running:
            try:
                time.sleep(self.state_validation_interval)

                actual_containers = {
                    c.id: c
                    for c in self.client.containers.list(all=True)
                    if c.name.startswith(self.container_prefix)
                }

                with self._lock:
                    redis_containers = list(self.containers_data.values())

                for container_info in redis_containers:
                    container_id = container_info["id"]

                    if container_id not in actual_containers:
                        container_info["status"] = "removed"
                        container_info["cpu"] = 0.0
                        container_info["memory"] = 0.0
                        container_info["timestamp"] = time.time()
                        self.redis.set_container_info(container_id, container_info)
                    else:
                        # match status
                        actual_status = actual_containers[container_id].status
                        if container_info["status"] != actual_status:
                            container_info["status"] = actual_status
                            container_info["timestamp"] = time.time()
                            if actual_status != "running":
                                container_info["cpu"] = 0.0
                                container_info["memory"] = 0.0
                            self.redis.set_container_info(container_id, container_info)

            except Exception as e:
                pass

    def _watch_for_new_containers(self):
        """Listen to Docker events"""
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
                        if (
                            container.name.startswith(self.container_prefix)
                            and container.id not in self._container_threads
                        ):
                            with self._lock:
                                self.containers_data[container.name] = {
                                    "id": container.id[:12],
                                    "name": container.name,
                                    "status": "booting",
                                    "cpu": 0.0,
                                    "memory": 0.0,
                                    "timestamp": time.time(),
                                    "logs": "",
                                }
                            self.redis.set_container_info(
                                container.id[:12],
                                {
                                    "id": container.id[:12],
                                    "name": container.name,
                                    "status": "booting",
                                    "cpu": 0.0,
                                    "memory": 0.0,
                                    "timestamp": time.time(),
                                    "logs": "",
                                },
                            )

                            t = threading.Thread(
                                target=self._monitor_container,
                                args=(container,),
                                daemon=True,
                            )
                            t.start()
                            self._container_threads[container.id] = t
                    except Exception:
                        continue

                # On container stop/crash
                elif status in ("die", "stop", "kill"):
                    try:
                        container = self.client.containers.get(container_id)
                        if (
                            container.name.startswith(self.container_prefix)
                            and container.id not in self._container_threads
                        ):

                            container = self.client.containers.get(container_id)
                            self._handle_container_death(container)
                    except Exception:
                        pass

            elif status == "destroy":
                container_name = None
                try:
                    container = self.client.containers.get(container_id)
                    container_name = container.name
                    if not container_name.startswith(self.container_prefix):
                        continue
                except Exception:
                    with self._lock:
                        for name, data in self.containers_data.items():
                            if data.get("id") == container_id[:12]:
                                container_name = name
                                break

                if container_name:
                    # Mark as removed, don't delete from Redis
                    with self._lock:
                        if container_name in self.containers_data:
                            self.containers_data[container_name]["status"] = "removed"
                            self.containers_data[container_name][
                                "timestamp"
                            ] = time.time()

                    self.redis.set_container_info(
                        container_id[:12],
                        {
                            "id": container_id[:12],
                            "name": container_name,
                            "status": "removed",
                            "timestamp": time.time(),
                        },
                    )

                self._container_threads.pop(container_id, None)

    def _calculate_global_metrics(self):
        """Calculate aggregate metrics across all containers."""
        with self._lock:
            containers = list(self.containers_data.values())

        # Filter only running containers for resource metrics
        running = [c for c in containers if c.get("status") == "running"]

        if not running:
            return {
                "total_containers": len(containers),
                "running_containers": 0,
                "stopped_containers": len(
                    [c for c in containers if c.get("status") in ("exited", "stopped")]
                ),
                "removed_containers": len(
                    [c for c in containers if c.get("status") == "removed"]
                ),
                "avg_cpu": 0.0,
                "max_cpu": 0.0,
                "min_cpu": 0.0,
                "total_cpu": 0.0,
                "avg_memory": 0.0,
                "max_memory": 0.0,
                "min_memory": 0.0,
                "total_memory": 0.0,
                "timestamp": time.time(),
            }

        # Calculate CPU stats
        cpu_values = [c.get("cpu", 0.0) for c in running]
        memory_values = [c.get("memory", 0.0) for c in running]

        metrics = {
            # Container counts by status
            "total_containers": len(containers),
            "running_containers": len(running),
            "stopped_containers": len(
                [c for c in containers if c.get("status") in ("exited", "stopped")]
            ),
            "removed_containers": len(
                [c for c in containers if c.get("status") == "removed"]
            ),
            "booting_containers": len(
                [c for c in containers if c.get("status") == "booting"]
            ),
            # CPU metrics
            "avg_cpu": (
                round(sum(cpu_values) / len(cpu_values), 2) if cpu_values else 0.0
            ),
            "max_cpu": round(max(cpu_values), 2) if cpu_values else 0.0,
            "min_cpu": round(min(cpu_values), 2) if cpu_values else 0.0,
            "total_cpu": round(sum(cpu_values), 2),
            # Memory metrics
            "avg_memory": (
                round(sum(memory_values) / len(memory_values), 2)
                if memory_values
                else 0.0
            ),
            "max_memory": round(max(memory_values), 2) if memory_values else 0.0,
            "min_memory": round(min(memory_values), 2) if memory_values else 0.0,
            "total_memory": round(sum(memory_values), 2),
            "timestamp": time.time(),
        }

        return metrics

    def _update_global_metrics(self):
        """Periodically calculate and store global metrics."""
        while self._running:
            try:
                time.sleep(5)  # update every 5 seconds

                metrics = self._calculate_global_metrics()
                self.redis.set_global_metrics(metrics)

            except Exception as e:
                print(f"Failed to update global metrics: {e}")

    def start(self):
        """Begin monitoring existing containers and watching for new"""
        self._running = True

        # Start monitoring all currently running containers
        running_containers = self.client.containers.list(filters={"status": "running"})
        for container in running_containers:
            if container.name.startswith(self.container_prefix):
                t = threading.Thread(
                    target=self._monitor_container, args=(container,), daemon=True
                )
                t.start()
                self._container_threads[container.id] = t

        # track stopped containers
        for container in self.client.containers.list(all=True):
            if container.name.startswith(self.container_prefix):
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

        #  Docker event watcher thread
        self._event_thread = threading.Thread(
            target=self._watch_for_new_containers, daemon=True
        )
        self._event_thread.start()

        # state validation thread
        self._validation_thread = threading.Thread(
            target=self._validate_container_state, daemon=True
        )
        self._validation_thread.start()

        # global metrics thread
        self._global_metrics_thread = threading.Thread(
            target=self._update_global_metrics, daemon=True
        )
        self._global_metrics_thread.start()

        self.redis.set_system_status("initialized", "Monitoring Service Active")

    def stop(self):
        self._running = False
        if self._event_thread:
            self._event_thread.join()
        if self._validation_thread:
            self._validation_thread.join()
        if self._global_metrics_thread:
            self._global_metrics_thread.join()

        for t in self._container_threads.values():
            t.join()

    def get_data(self, clear_after_get=False):
        """Return the latest container stats as JSON"""
        with self._lock:
            data = json.dumps(list(self.containers_data.values()))
            if clear_after_get:
                self.containers_data.clear()
            return data

    def get_global_data(self):
        """Get global metrics as JSON."""
        metrics = self._calculate_global_metrics()
        return json.dumps(metrics)
