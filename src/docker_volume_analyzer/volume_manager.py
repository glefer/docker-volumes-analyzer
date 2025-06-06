from typing import List

from docker_volume_analyzer.docker_client import DockerClient
from docker_volume_analyzer.filesystem import FileSystem, parse_find_output


class VolumeManager:
    def __init__(self, docker_client: DockerClient | None = None):
        self.client = docker_client or DockerClient()

    def get_volumes(self, human_readable: bool = True) -> dict:
        """
        Return all Docker volumes name and mountpoint

        Returns:
            dict: Dictionary with volume names as keys
                    and mount points as values.
        """

        volumes = self.client.list_volumes()

        # Fetch containers associated with volumes
        containers_by_volumes = self.get_containers_by_volume()

        # Fetch sizes for all volumes in a single call
        volume_sizes = self.get_volumes_size(
            [volume.name for volume in volumes], human_readable
        )

        # Build the result dictionary
        return {
            volume.name: {
                "name": volume.name,
                "mountpoint": volume.attrs.get("Mountpoint", ""),
                "size": volume_sizes.get(
                    volume.name, "0"
                ),  # Use pre-fetched sizes
                "created_at": volume.attrs.get("CreatedAt", ""),
                "containers": containers_by_volumes.get(volume.name, []),
            }
            for volume in volumes
        }

    def get_containers_by_volume(self) -> dict:
        """
        Return all Docker containers and their volumes.

        Returns:
            dict: Dictionary with volume names as keys and parse_find_output
                    container information (name, mountpoint, etc.) as values.
        """
        containers_by_volumes = {}
        for container in self.client.list_containers():
            for volume in container.attrs.get("Mounts", []):
                volume_name = volume.get("Name")
                if volume_name not in containers_by_volumes:
                    containers_by_volumes[volume_name] = []
                containers_by_volumes[volume_name].append(
                    {
                        "short_id": container.short_id,
                        "container_name": container.name,
                        "mountpoint": volume.get("Destination", ""),
                        "driver": volume.get("Driver", ""),
                        "mode": volume.get("Mode", ""),
                        "rw": volume.get("RW", False),
                    }
                )
        return containers_by_volumes

    def delete_volume(self, volume_name: str) -> bool:
        """
        Delete a Docker volume by its name.

        Args:
            volume_name (str): Name of the Docker volume to delete.

        Returns:
            bool: True if the volume was deleted successfully, False otherwise.
        """
        try:
            self.client.remove_volume(volume_name)
            return True
        except Exception:
            return False

    def get_volume_tree(self, volume_name: str) -> "FileSystem":
        """
        Get a tree structure of the files in a Docker volume.

        Args:
            volume_name (str): Name of the Docker volume.

        Returns:
            dict: A dictionary representing the file tree structure.
        """
        find_result = self.client.get_directory_informations_with_find(
            volume_name, directory=None
        )
        if not find_result:
            return FileSystem()

        return parse_find_output(
            find_result, f"/mnt/{volume_name}"
        ).compute_directory_sizes()

    def get_volumes_size(
        self, volume_names=List[str], human_readable: bool = True
    ) -> dict:
        return self.client.get_volumes_size(volume_names, human_readable)

    def delete_volume_file(self, volume_name: str, file_path: str) -> bool:
        """
        Delete a specific file in a Docker volume.

        Args:
            volume_name (str): Name of the Docker volume.
            file_path (str): Path to the file inside the volume.

        Returns:
            bool: True if the file was deleted successfully, False otherwise.
        """
        try:
            self.client.delete_volume_file(volume_name, file_path)
            return True
        except Exception:
            return False
