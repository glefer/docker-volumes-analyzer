from typing import List, Union

import docker

from docker_volume_analyzer.errors import DockerNotAvailableError


class DockerClient:
    def __init__(self):
        try:
            self.client = docker.from_env()
        except docker.errors.DockerException as e:
            raise DockerNotAvailableError from e

    def list_volumes(self) -> List[docker.models.volumes.Volume]:
        """
        Returns all Docker volume objects.
        """
        return self.client.volumes.list()

    def list_containers(self) -> List[docker.models.containers.Container]:
        """
        Returns all running Docker container objects.
        """
        return self.client.containers.list(all=True)

    def _run_in_container(
        self,
        command: Union[str, List[str]],
        volume_name: str,
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
        try:
            output = self.client.containers.run(
                image="alpine",
                command=command,
                volumes={
                    volume_name: {"bind": "/mnt/docker_volume", "mode": mode}
                },
                remove=True,
                stdout=True,
                stderr=False,
            )
            return output.decode().strip()
        except docker.errors.ContainerError as e:
            print(f"[Docker Error] Command failed: {e}")
            return None

    def get_volume_size(self, volume_name: str) -> str:
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
