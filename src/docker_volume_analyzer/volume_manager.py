from docker_volume_analyzer.docker_client import DockerClient


class VolumeManager:
    def __init__(self):
        self.client = DockerClient()

    def get_volumes(self) -> dict:
        """
        Return all Docker volumes name and mountpoint

        Returns:
            dict: Dictionary with volume names as keys
                    and mount points as values.
        """

        containers_by_volumes = self.get_containers_by_volume()

        return {
            idx: {
                "name": volume.name,
                "mountpoint": volume.attrs.get("Mountpoint", ""),
                "size": self.get_volume_size(volume.name),
                "created_at": volume.attrs.get("CreatedAt", ""),
                "containers": containers_by_volumes.get(volume.name, []),
            }
            for idx, volume in enumerate(self.client.list_volumes())
        }

    def get_containers_by_volume(self) -> dict:
        """
        Return all Docker containers and their volumes.

        Returns:
            dict: Dictionary with volume names as keys and
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
                        "container_name": container.name,
                        "mountpoint": volume.get("Destination", ""),
                        "driver": volume.get("Driver", ""),
                        "mode": volume.get("Mode", ""),
                        "rw": volume.get("RW", False),
                    }
                )
        return containers_by_volumes

    def get_volume_size(self, volume_name: str) -> int:
        """
        Get the size of a Docker volume.

        Args:
            volume_name (str): Name of the Docker volume.

        Returns:
            int: Size of the volume in bytes.
        """
        return self.client.get_volume_size(volume_name)
