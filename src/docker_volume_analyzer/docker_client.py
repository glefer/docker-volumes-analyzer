import docker


class DockerClient:
    def __init__(self):
        self.client = docker.from_env()

    def list_volumes(self):
        """Récupère tous les volumes Docker"""
        return self.client.volumes.list()

    def remove_volume(self, volume_name):
        """Supprime un volume"""
        volume = self.client.volumes.get(volume_name)
        volume.remove()
