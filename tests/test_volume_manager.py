import random
from typing import List
from unittest.mock import MagicMock

from docker_volume_analyzer.volume_manager import VolumeManager


def make_mock_volume(name: str, mountpoint: str, created_at: str) -> MagicMock:
    volume = MagicMock()
    volume.name = name
    volume.attrs = {
        "Name": name,
        "Mountpoint": mountpoint,
        "CreatedAt": created_at,
    }
    return volume


def make_mock_container_with_mounts(
    short_id: str, name: str, mounts: List[dict]
) -> MagicMock:
    container = MagicMock()
    container.short_id = short_id
    container.name = name
    container.attrs = {"Mounts": mounts}
    return container


def generate_test_data(num_volumes: int, max_containers_per_volume: int):
    """Génère un ensemble de volumes et conteneurs liés aléatoirement."""

    volumes = []
    containers = []
    expected = {}

    for i in range(num_volumes):
        vol_name = f"volume{i}"
        mountpoint = f"/mnt/{vol_name}"
        created_at = f"2023-01-{i+1:02d}T00:00:00Z"
        size = (i + 1) * 10

        volume = make_mock_volume(vol_name, mountpoint, created_at)
        volumes.append(volume)

        volume_containers = []
        num_containers = random.randint(1, max_containers_per_volume)

        for j in range(num_containers):
            cont_name = f"container{i}_{j}"
            short_id = f"{i:02d}{j:02d}"
            mount = {
                "Name": vol_name,
                "Destination": mountpoint,
                "Driver": "local",
                "Mode": "rw",
                "RW": True,
            }
            container = make_mock_container_with_mounts(
                short_id, cont_name, [mount]
            )
            containers.append(container)

            volume_containers.append(
                {
                    "short_id": short_id,
                    "container_name": cont_name,
                    "mountpoint": mountpoint,
                    "driver": "local",
                    "mode": "rw",
                    "rw": True,
                }
            )

        expected[vol_name] = {
            "name": vol_name,
            "mountpoint": mountpoint,
            "size": size,
            "created_at": created_at,
            "containers": volume_containers,
        }

    return volumes, containers, expected


def test_get_volumes() -> None:
    num_volumes = 30
    volumes, containers, expected = generate_test_data(
        num_volumes, max_containers_per_volume=5
    )

    mock_client = MagicMock()
    mock_client.list_volumes.return_value = volumes
    mock_client.list_containers.return_value = containers
    mock_client.get_volume_size.side_effect = (
        lambda name: int(name.replace("volume", "")) * 10 + 10
    )

    # Injecte dans VolumeManager
    volume_manager = VolumeManager()
    volume_manager.client = mock_client

    assert volume_manager.get_volumes() == expected


def test_delete_volume_success() -> None:
    volume_name = "test_volume"

    mock_client = MagicMock()
    mock_client.remove_volume.return_value = True

    # Injecte dans VolumeManager
    volume_manager = VolumeManager()
    volume_manager.client = mock_client

    assert volume_manager.delete_volume(volume_name) is True
    mock_client.remove_volume.assert_called_once_with(volume_name)


def test_delete_volume_failure() -> None:
    volume_name = "non_existent_volume"

    mock_client = MagicMock()

    mock_client.remove_volume.side_effect = Exception("Volume not found")

    # Injecte dans VolumeManager
    volume_manager = VolumeManager()
    volume_manager.client = mock_client

    assert volume_manager.delete_volume(volume_name) is False
    mock_client.remove_volume.assert_called_once_with(volume_name)
