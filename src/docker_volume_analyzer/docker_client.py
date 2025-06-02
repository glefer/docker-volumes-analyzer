import re
import time
from typing import List, Union

import docker
from docker.errors import NotFound
from docker.models.containers import Container

from docker_volume_analyzer.errors import DockerNotAvailableError


class DockerClient:

    _SIZE_RE = re.compile(r"^\d+(\.\d+)?[KMGTP]?$")

    def __init__(self):
        try:
            self.client = docker.from_env()
            self._volume_size_cache = {}
            self._cache_timeout = 60
        except docker.errors.DockerException as e:
            raise DockerNotAvailableError from e

    def list_volumes(self) -> List[docker.models.volumes.Volume]:
        """
        Returns all Docker volume objects.
        """
        return self.client.volumes.list()

    def list_containers(self) -> List[Container]:
        """
        Returns all Docker container objects (running and stopped),
        skipping containers that may have been removed during the process.
        """
        containers: List[Container] = []
        for summary in self.client.api.containers(all=True):
            try:
                container = self.client.containers.get(summary["Id"])
                containers.append(container)
            except NotFound:
                continue
        return containers

    def _run_in_container(
        self,
        command: Union[str, List[str]],
        volumes_name: Union[str, List[str]],
        mode: str = "ro",
    ) -> Union[str, None]:
        """
        Helper to run a command in a temporary
        Alpine container with volume mounted.

        Args:
            command (str | list): Shell command to execute.
            volume_name (str): Name of the Docker volume.
            mode (str): Volume mount mode ("ro" or "rw").

        Returns:
            str | None: Output of the command or None if failed.
        """

        if isinstance(volumes_name, str):
            volumes_binding = {
                volumes_name: {"bind": f"/mnt/{volumes_name}", "mode": mode}
            }
        elif isinstance(volumes_name, list):
            volumes_binding = {
                name: {"bind": f"/mnt/{name}", "mode": mode}
                for name in volumes_name
            }
        else:
            raise ValueError(
                "volumes_name must be a string or a list of strings"
            )

        try:
            output = self.client.containers.run(
                image="alpine",
                command=command,
                volumes=volumes_binding,
                remove=True,
                stdout=True,
                stderr=False,
            )
            return output.decode().strip()
        except docker.errors.ContainerError as e:
            print(f"[Docker Error] Command failed: {e}")
            return None

    def get_volume_size(self, volume_name: Union[str, List[str]]) -> str:
        """
        Gets human-readable size of a volume using 'du -sh'.

        Args:
            volume_name (str): Docker volume name.

        Returns:
            str: Size as a human-readable string (e.g., '4.0K', '1.2G').
        """
        output = self._run_in_container(
            ["sh", "-c", "du -sh /mnt/docker_volume"], volume_name
        )
        return output.split()[0] if output else "0"

    def remove_volume(self, volume_name: str) -> None:
        """
        Removes a Docker volume by name.

        Args:
            volume_name (str): Name of the Docker volume to remove.

        Raises:
            docker.errors.APIError: If the volume cannot be removed.
        """
        try:
            volume = self.client.volumes.get(volume_name)
            volume.remove(force=True)
        except docker.errors.NotFound as e:
            raise docker.errors.APIError(
                f"Volume '{volume_name}' not found."
            ) from e
        except docker.errors.APIError as e:
            raise docker.errors.APIError(
                f"Failed to remove volume '{volume_name}': {e}"
            ) from e

    def get_directory_informations_with_find(
        self, volume_name: str, directory: str | None = None
    ) -> Union[str, None]:
        """
        Gets directory information using 'find' command.

        Args:
            volume_name (str): Docker volume name.
            directory (str): Directory path inside the volume.

        Returns:
            str | None: Output of the 'find' with stat command
            or None if failed.
        """
        path = (
            f"/mnt/{volume_name}/{directory}"
            if directory
            else f"/mnt/{volume_name}"
        )

        command = [
            "sh",
            "-c",
            f"find {path} -exec stat -c '%F|%n|%s|%A|%U|%G|%Y' {{}} \\;",
        ]
        output = self._run_in_container(command, volume_name)
        return output if output else None

    def get_volumes_size(
        self, volumes_name: Union[str, List[str]], human_readable: bool = True
    ):
        if isinstance(volumes_name, str):
            volumes_name = [volumes_name]

        current_time = time.time()
        cached_results = {}
        volumes_to_query = []

        for volume in volumes_name:
            cache_entry = self._volume_size_cache.get(volume)
            if (
                cache_entry
                and current_time - cache_entry["timestamp"]
                < self._cache_timeout
            ):
                cached_results[volume] = cache_entry["size"]
            else:
                volumes_to_query.append(volume)

        if volumes_to_query:
            paths = " ".join(f"/mnt/{v}" for v in volumes_to_query)
            cmd = ["sh", "-c", f"du -s{'h' if human_readable else ''} {paths}"]
            output = self._run_in_container(cmd, volumes_to_query)

            results = {}
            for volume in volumes_to_query:
                results[volume] = "0"  # Default size is "0"
            if output:
                for line, volume in zip(output.splitlines(), volumes_to_query):
                    parts = line.split(maxsplit=1)
                    if len(parts) >= 1 and self._SIZE_RE.match(parts[0]):
                        results[volume] = parts[0]

            for volume, size in results.items():
                self._volume_size_cache[volume] = {
                    "size": size,
                    "timestamp": current_time,
                }

            cached_results.update(results)

        return cached_results
