from unittest.mock import MagicMock, patch

import docker
import pytest

from docker_volume_analyzer.docker_client import DockerClient
from docker_volume_analyzer.errors import DockerNotAvailableError


def test_list_volumes():
    """
    Test the list_volumes method of DockerClient.
    """
    mock_client = MagicMock()
    mock_client.volumes.list.return_value = [
        MagicMock(name="Volume", id="volume1"),
        MagicMock(name="Volume", id="volume2"),
    ]

    docker_client = DockerClient()
    docker_client.client = mock_client

    volumes = docker_client.list_volumes()

    assert len(volumes) == 2


def test_list_containers():
    """
    Test the list_containers method of DockerClient.
    """
    mock_client = MagicMock()
    mock_client.containers.list.return_value = [
        MagicMock(name="Container", id="container1"),
        MagicMock(name="Container", id="container2"),
    ]

    docker_client = DockerClient()
    docker_client.client = mock_client

    containers = docker_client.list_containers()

    assert len(containers) == 2


def test_run_in_container():
    """
    Test the _run_in_container method of DockerClient.
    """
    mock_client = MagicMock()
    mock_client.containers.run.return_value = b"output"

    docker_client = DockerClient()
    docker_client.client = mock_client

    output = docker_client._run_in_container("ls", "volume_name")

    docker_client.client.containers.run.assert_called_with(
        image="alpine",
        command="ls",
        volumes={"volume_name": {"bind": "/mnt/docker_volume", "mode": "ro"}},
        remove=True,
        stdout=True,
        stderr=False,
    )

    assert output == "output"


def test_run_in_container_error():
    """
    Test the _run_in_container method of DockerClient
    when a ContainerError occurs.
    """
    mock_client = MagicMock()
    mock_client.containers.run.side_effect = docker.errors.ContainerError(
        container=MagicMock(),
        exit_status=1,
        command="ls",
        image="test_image",
        stderr="error",
    )

    docker_client = DockerClient()
    docker_client.client = mock_client

    output = docker_client._run_in_container("ls", "volume_name")

    assert output is None


def test_get_volume_size():
    """
    Test the get_volume_size method of DockerClient.
    """
    mock_client = MagicMock()
    mock_client.containers.run.return_value = b"10M\tuseless information"

    docker_client = DockerClient()
    docker_client.client = mock_client

    size = docker_client.get_volume_size("volume_name")

    assert size == "10M"


def test_docker_not_available_error():
    with patch("docker.from_env", side_effect=docker.errors.DockerException):
        with pytest.raises(DockerNotAvailableError):
            DockerClient()


def test_remove_volume_success():
    """
    Test the remove_volume method of DockerClient when
    the volume is successfully removed.
    """
    mock_client = MagicMock()
    mock_volume = MagicMock()
    mock_client.volumes.get.return_value = mock_volume

    docker_client = DockerClient()
    docker_client.client = mock_client

    docker_client.remove_volume("test_volume")

    mock_client.volumes.get.assert_called_with("test_volume")
    mock_volume.remove.assert_called_with(force=True)


def test_remove_volume_not_found():
    """
    Test the remove_volume method of DockerClient when the volume is not found.
    """
    mock_client = MagicMock()
    mock_client.volumes.get.side_effect = docker.errors.NotFound(
        "Volume not found"
    )

    docker_client = DockerClient()
    docker_client.client = mock_client

    with pytest.raises(
        docker.errors.APIError, match="Volume 'test_volume' not found."
    ):
        docker_client.remove_volume("test_volume")

    mock_client.volumes.get.assert_called_with("test_volume")


def test_remove_volume_api_error():
    """
    Test the remove_volume method of DockerClient when an API error occurs.
    """
    mock_client = MagicMock()
    mock_volume = MagicMock()
    mock_client.volumes.get.return_value = mock_volume
    mock_volume.remove.side_effect = docker.errors.APIError("API error")

    docker_client = DockerClient()
    docker_client.client = mock_client

    with pytest.raises(
        docker.errors.APIError,
        match="Failed to remove volume 'test_volume': API error",
    ):
        docker_client.remove_volume("test_volume")

    mock_client.volumes.get.assert_called_with("test_volume")
    mock_volume.remove.assert_called_with(force=True)


def test_get_directory_informations_with_find():
    """
    Test the get_directory_informations_with_find method of DockerClient.
    """
    mock_client = MagicMock()
    mock_client.containers.run.return_value = (
        b"directory|/mnt/docker_volume/test_dir|4096"
        b"|drwxr-xr-x|user|group|1633024800\n"
        b"file|/mnt/docker_volume/test_dir/file.txt|1024"
        b"|-rw-r--r--|user|group|1633024800"
    )

    docker_client = DockerClient()
    docker_client.client = mock_client

    output = docker_client.get_directory_informations_with_find(
        "test_volume", "test_dir"
    )

    docker_client.client.containers.run.assert_called_with(
        image="alpine",
        command=[
            "sh",
            "-c",
            "find /mnt/docker_volume/test_dir -exec stat "
            "-c '%F|%n|%s|%A|%U|%G|%Y' {} \\;",
        ],
        volumes={"test_volume": {"bind": "/mnt/docker_volume", "mode": "ro"}},
        remove=True,
        stdout=True,
        stderr=False,
    )

    assert output == (
        "directory|/mnt/docker_volume/test_dir|4096"
        "|drwxr-xr-x|user|group|1633024800\n"
        "file|/mnt/docker_volume/test_dir/file.txt|1024"
        "|-rw-r--r--|user|group|1633024800"
    )


def test_get_directory_informations_with_find_no_directory():
    """
    Test the get_directory_informations_with_find method of DockerClient
    when no directory is specified.
    """
    mock_client = MagicMock()
    mock_client.containers.run.return_value = (
        b"directory|/mnt/docker_volume|4096"
        b"|drwxr-xr-x|user|group|1633024800\n"
        b"file|/mnt/docker_volume/file.txt|1024"
        b"|-rw-r--r--|user|group|1633024800"
    )

    docker_client = DockerClient()
    docker_client.client = mock_client

    output = docker_client.get_directory_informations_with_find("test_volume")

    docker_client.client.containers.run.assert_called_with(
        image="alpine",
        command=[
            "sh",
            "-c",
            "find /mnt/docker_volume -exec stat "
            "-c '%F|%n|%s|%A|%U|%G|%Y' {} \\;",
        ],
        volumes={"test_volume": {"bind": "/mnt/docker_volume", "mode": "ro"}},
        remove=True,
        stdout=True,
        stderr=False,
    )

    assert output == (
        "directory|/mnt/docker_volume|4096"
        "|drwxr-xr-x|user|group|1633024800\n"
        "file|/mnt/docker_volume/file.txt|1024"
        "|-rw-r--r--|user|group|1633024800"
    )


def test_get_directory_informations_with_find_error():
    """
    Test the get_directory_informations_with_find method of DockerClient
    when an error occurs.
    """
    mock_client = MagicMock()
    mock_client.containers.run.side_effect = docker.errors.ContainerError(
        container=MagicMock(),
        exit_status=1,
        command="find",
        image="alpine",
        stderr="error",
    )

    docker_client = DockerClient()
    docker_client.client = mock_client

    output = docker_client.get_directory_informations_with_find(
        "test_volume", "test_dir"
    )

    docker_client.client.containers.run.assert_called_with(
        image="alpine",
        command=[
            "sh",
            "-c",
            "find /mnt/docker_volume/test_dir -exec stat "
            "-c '%F|%n|%s|%A|%U|%G|%Y' {} \\;",
        ],
        volumes={"test_volume": {"bind": "/mnt/docker_volume", "mode": "ro"}},
        remove=True,
        stdout=True,
        stderr=False,
    )

    assert output is None
