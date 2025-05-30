import random
from typing import List
from unittest.mock import MagicMock, patch

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

    volume_manager = VolumeManager()
    volume_manager.client = mock_client

    assert volume_manager.get_volumes() == expected


def test_delete_volume_success() -> None:
    volume_name = "test_volume"

    mock_client = MagicMock()
    mock_client.remove_volume.return_value = True

    volume_manager = VolumeManager()
    volume_manager.client = mock_client

    assert volume_manager.delete_volume(volume_name) is True
    mock_client.remove_volume.assert_called_once_with(volume_name)


def test_delete_volume_failure() -> None:
    volume_name = "non_existent_volume"

    mock_client = MagicMock()

    mock_client.remove_volume.side_effect = Exception("Volume not found")

    volume_manager = VolumeManager()
    volume_manager.client = mock_client

    assert volume_manager.delete_volume(volume_name) is False
    mock_client.remove_volume.assert_called_once_with(volume_name)


def test_get_volume_tree_success() -> None:
    volume_name = "test_volume"
    mock_find_output = [
        {"path": "/file1.txt", "size": 100},
        {"path": "/dir1/file2.txt", "size": 200},
        {"path": "/dir1/file3.txt", "size": 300},
        {"path": "/dir2/file4.txt", "size": 400},
    ]
    expected_tree = {
        "name": "/",
        "size": 1000,
        "childrens": [
            {"name": "file1.txt", "size": 100, "childrens": []},
            {
                "name": "dir1",
                "size": 500,
                "childrens": [
                    {"name": "file2.txt", "size": 200, "childrens": []},
                    {"name": "file3.txt", "size": 300, "childrens": []},
                ],
            },
            {
                "name": "dir2",
                "size": 400,
                "childrens": [
                    {"name": "file4.txt", "size": 400, "childrens": []},
                ],
            },
        ],
    }

    mock_client = MagicMock()
    (mock_client.get_directory_informations_with_find).return_value = (
        mock_find_output
    )

    mock_parse_find_output = MagicMock()
    (
        mock_parse_find_output.return_value.compute_directory_sizes
    ).return_value = expected_tree

    volume_manager = VolumeManager()
    volume_manager.client = mock_client

    with patch(
        "docker_volume_analyzer.volume_manager.parse_find_output",
        mock_parse_find_output,
    ):
        assert volume_manager.get_volume_tree(volume_name) == expected_tree
        (
            mock_client.get_directory_informations_with_find
        ).assert_called_once_with(volume_name, directory=None)
        mock_parse_find_output.assert_called_once_with(mock_find_output)


def test_get_volume_tree_empty() -> None:
    volume_name = "empty_volume"

    mock_client = MagicMock()
    mock_client.get_directory_informations_with_find.return_value = []

    volume_manager = VolumeManager()
    volume_manager.client = mock_client

    assert volume_manager.get_volume_tree(volume_name) == {}
    mock_client.get_directory_informations_with_find.assert_called_once_with(
        volume_name, directory=None
    )
