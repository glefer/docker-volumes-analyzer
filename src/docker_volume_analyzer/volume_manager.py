from docker_volume_analyzer.docker_client import DockerClient


class VolumeManager:
    def __init__(self):
        self.client = DockerClient()

    def get_volumes(self):
        """
        Return all Docker volumes name and mountpoint

        Returns:
            dict: Dictionary with volume names as keys
                    and mount points as values.
        """
        volumes = self.client.list_volumes()
        return {v.name: v.attrs.get("Mountpoint") for v in volumes}

    def get_volume_files(self, volume_name, prefix="/mnt/docker_volume"):
        """
        Get all files in a Docker volume.

        Args:
            volume_name (str): Name of the Docker volume.
            prefix (str): Prefix to remove from the file paths.

        Returns:
            dict: Tree structure of files in the volume.
        """
        return self.build_tree_structure(
            self.client.get_docker_volume_file_paths(volume_name), prefix
        )

    def build_tree_structure(
        self, file_paths: list[str], prefix="/mnt/docker_volume"
    ) -> dict:
        """Builds a tree structure from a list of file paths.

        Args:
            file_paths (list[str]): List of file paths.
            prefix (str): Common prefix to remove from each path.

        Returns:
            dict: Tree structure represented as a dictionary.
        """
        tree = {}
        for path in file_paths:
            # S'assurer que le chemin commence bien par le préfixe
            if path.startswith(prefix):
                relative_path = path[len(prefix) :].lstrip("/")  # noqa: E203
            else:
                relative_path = path.lstrip(
                    "/"
                )  # Préfixe non trouvé, traiter quand même

            if not relative_path:
                continue  # Éviter les chemins égaux au préfixe seul

            parts = relative_path.split("/")
            current = tree
            for part in parts[:-1]:
                if part not in current or current[part] is None:
                    current[part] = {}
                current = current[part]
            current[parts[-1]] = (
                None  # Dernier élément : fichier ou répertoire vide
            )

        return tree

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
        return self.client.delete_file_from_volume(volume_name, file_path)
