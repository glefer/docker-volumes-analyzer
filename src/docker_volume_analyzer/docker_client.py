import docker


class DockerClient:
    def __init__(self):
        self.client = docker.from_env()

    def list_volumes(self):
        """
        Get all Docker volumes.

        Returns:
            list: List of Docker volume objects.
        """
        return self.client.volumes.list()

    def get_docker_volume_file_paths(self, volume_name: str) -> list[str]:
        """
        Mounts a volume in an Alpine container and executes
        find /mnt/docker_volume command.

        Args:
            volume_name (str): Name of the Docker volume.

        Returns:
            list[str]: List of file paths in the volume.
        """
        try:
            container = self.client.containers.run(
                image="alpine",
                command=["sh", "-c", "find /mnt/docker_volume | sort"],
                volumes={
                    volume_name: {"bind": "/mnt/docker_volume", "mode": "ro"}
                },
                remove=True,
                stdout=True,
                stderr=False,
            )
            lines = container.decode().strip().split("\n")
            return lines
        except docker.errors.ContainerError as e:
            print(f"Erreur lors de l'exécution dans le conteneur : {e}")
            return []

    def delete_file_from_volume(
        self, volume_name: str, file_path: str
    ) -> bool:
        """
        Delete a file from a Docker volume.

        Args:
            volume_name (str): Name of the Docker volume.
            file_path (str): Path of the file to delete.

        Returns:
            bool: True if the file was deleted successfully, False otherwise.
        """
        file_path = f"/mnt/docker_volume/{file_path}"
        try:
            self.client.containers.run(
                image="alpine",
                command=["rm", file_path],
                volumes={
                    volume_name: {"bind": "/mnt/docker_volume", "mode": "rw"}
                },
                remove=True,
                stdout=True,
                stderr=False,
            )
            return True
        except docker.errors.ContainerError as e:
            print(f"Erreur lors de la suppression du fichier : {e}")
            return False
