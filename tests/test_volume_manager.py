from unittest.mock import MagicMock

from docker_volume_analyzer.volume_manager import VolumeManager


def make_mock_volume(name: str, mountpoint: str) -> MagicMock:
    volume = MagicMock()
    volume.name = name
    volume.attrs = {"Mountpoint": mountpoint}
    return volume


def test_get_volumes() -> None:
    mock_client = MagicMock()
    mock_client.list_volumes.return_value = [
        make_mock_volume("volume1", "/mnt/volume1"),
        make_mock_volume("volume2", "/mnt/volume2"),
    ]

    volume_manager = VolumeManager()
    volume_manager.client = mock_client

    assert volume_manager.get_volumes() == {
        "volume1": "/mnt/volume1",
        "volume2": "/mnt/volume2",
    }
