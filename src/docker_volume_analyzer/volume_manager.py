from docker_volume_analyzer.docker_client import DockerClient


class VolumeManager:
    def __init__(self):
        self.client = DockerClient()

    def get_volumes(self):
        """Retourne les volumes en appliquant les filtres de config.yaml"""
        volumes = self.client.list_volumes()
        return {v.name: v.attrs.get("Mountpoint") for v in volumes}
