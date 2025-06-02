import time
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
    mock_client.api.containers.return_value = [
        {"Id": "container1"},
        {"Id": "container2"},
    ]
    mock_client.containers.get.side_effect = lambda container_id: MagicMock(
        name="Container", id=container_id
    )

    docker_client = DockerClient()
    docker_client.client = mock_client

    containers = docker_client.list_containers()
    assert len(containers) == 2
    assert containers[0].id == "container1"
    assert containers[1].id == "container2"
    assert len(containers) == 2


@pytest.mark.parametrize(
    "volumes_input, mode, expected_volumes",
    [
        (
            "volume_name",
            "ro",
            {"volume_name": {"bind": "/mnt/volume_name", "mode": "ro"}},
        ),
        (
            ["volume1", "volume2"],
            "ro",
            {
                "volume1": {"bind": "/mnt/volume1", "mode": "ro"},
                "volume2": {"bind": "/mnt/volume2", "mode": "ro"},
            },
        ),
        (
            "volume_name",
            "rw",
            {"volume_name": {"bind": "/mnt/volume_name", "mode": "rw"}},
        ),
        (
            ["volume1", "volume2"],
            "rw",
            {
                "volume1": {"bind": "/mnt/volume1", "mode": "rw"},
                "volume2": {"bind": "/mnt/volume2", "mode": "rw"},
            },
        ),
        ([], "ro", {}),
    ],
)
def test_run_in_container(volumes_input, mode, expected_volumes):
    """
    Test the _run_in_container method of DockerClient for single
    multiple, and edge cases.
    """
    mock_client = MagicMock()
    mock_client.containers.run.return_value = b"output"

    docker_client = DockerClient()
    docker_client.client = mock_client

    output = docker_client._run_in_container("ls", volumes_input, mode=mode)

    docker_client.client.containers.run.assert_called_with(
        image="alpine",
        command="ls",
        volumes=expected_volumes,
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
            "find /mnt/test_volume/test_dir -exec stat "
            "-c '%F|%n|%s|%A|%U|%G|%Y' {} \\;",
        ],
        volumes={"test_volume": {"bind": "/mnt/test_volume", "mode": "ro"}},
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
            "find /mnt/test_volume -exec stat "
            "-c '%F|%n|%s|%A|%U|%G|%Y' {} \\;",
        ],
        volumes={"test_volume": {"bind": "/mnt/test_volume", "mode": "ro"}},
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
            "find /mnt/test_volume/test_dir -exec stat "
            "-c '%F|%n|%s|%A|%U|%G|%Y' {} \\;",
        ],
        volumes={"test_volume": {"bind": "/mnt/test_volume", "mode": "ro"}},
        remove=True,
        stdout=True,
        stderr=False,
    )

    assert output is None


def test_list_containers_not_found():
    """
    Test the list_containers method of DockerClient
    when a container is not found.
    """
    mock_client = MagicMock()
    mock_client.api.containers.return_value = [
        {"Id": "container1"},
        {"Id": "container2"},
    ]
    mock_client.containers.get.side_effect = [
        MagicMock(name="Container", id="container1"),
        docker.errors.NotFound("Container not found"),
    ]

    docker_client = DockerClient()
    docker_client.client = mock_client

    containers = docker_client.list_containers()

    assert len(containers) == 1
    assert containers[0].id == "container1"


@pytest.mark.parametrize(
    "volumes_input, human_readable, expected_output",
    [
        ("volume1", True, {"volume1": "10M"}),
        (["volume1", "volume2"], True, {"volume1": "10M", "volume2": "20M"}),
        (
            ["volume1", "volume2"],
            False,
            {"volume1": "10240", "volume2": "20480"},
        ),
    ],
)
def test_get_volumes_size(volumes_input, human_readable, expected_output):
    """
    Test the get_volumes_size method of DockerClient
    for single and multiple volumes.
    """
    mock_client = MagicMock()
    mock_client.containers.run.return_value = (
        b"10M\tdirectory-path\n20M\tdirectory-path"
        if human_readable
        else b"10240\tdirectory-path\n20480\tdirectory-path"
    )

    docker_client = DockerClient()
    docker_client.client = mock_client

    result = docker_client.get_volumes_size(volumes_input, human_readable)

    docker_client.client.containers.run.assert_called_with(
        image="alpine",
        command=[
            "sh",
            "-c",
            f"du -s{'h' if human_readable else ''} "
            + " ".join(
                [
                    f"/mnt/{vol}"
                    for vol in (
                        volumes_input
                        if isinstance(volumes_input, list)
                        else [volumes_input]
                    )
                ]
            ),
        ],
        volumes={
            vol: {"bind": f"/mnt/{vol}", "mode": "ro"}
            for vol in (
                volumes_input
                if isinstance(volumes_input, list)
                else [volumes_input]
            )
        },
        remove=True,
        stdout=True,
        stderr=False,
    )

    assert result == expected_output


def test_get_volumes_size_no_output():
    """
    Test the get_volumes_size method of DockerClient
    when no output is returned.
    """
    mock_client = MagicMock()
    mock_client.containers.run.return_value = b""

    docker_client = DockerClient()
    docker_client.client = mock_client

    result = docker_client.get_volumes_size(["volume1", "volume2"])

    assert result == {"volume1": "0", "volume2": "0"}


def test_get_volumes_size_index_error():
    """
    Test the get_volumes_size method of DockerClient when IndexError occurs.
    """
    mock_client = MagicMock()
    mock_client.containers.run.return_value = b"invalid_output"

    docker_client = DockerClient()
    docker_client.client = mock_client

    result = docker_client.get_volumes_size(["volume1", "volume2"])

    assert result == {"volume1": "0", "volume2": "0"}


def test_run_in_container_invalid_volumes_name():
    """
    Test the _run_in_container method of DockerClient when an invalid
    volumes_name is provided.
    """
    docker_client = DockerClient()

    with pytest.raises(
        ValueError, match="volumes_name must be a string or a list of strings"
    ):
        docker_client._run_in_container("ls", 123)


@pytest.mark.parametrize(
    "cached_volumes, requested_volumes, expected_result",
    [
        # Case where all requested volumes are cached
        (
            {
                "volume1": {"size": "10M", "timestamp": time.time()},
                "volume2": {"size": "20M", "timestamp": time.time()},
            },
            ["volume1", "volume2"],
            {"volume1": "10M", "volume2": "20M"},
        ),
        # Case where some volumes are cached, and one needs to be queried
        (
            {
                "volume1": {"size": "10M", "timestamp": time.time()},
                "volume2": {"size": "20M", "timestamp": time.time() - 30},
            },
            ["volume1", "volume2", "volume3"],
            {"volume1": "10M", "volume2": "20M", "volume3": "30M"},
        ),
    ],
)
def test_get_volumes_size_with_cache(
    cached_volumes, requested_volumes, expected_result
):
    """
    Test the get_volumes_size method of DockerClient
    when cache is used for some or all volumes.
    """
    mock_client = MagicMock()
    docker_client = DockerClient()
    docker_client.client = mock_client

    docker_client._volume_size_cache = cached_volumes
    docker_client._cache_timeout = 60

    mock_client.containers.run.return_value = b"30M\tdirectory-path"

    result = docker_client.get_volumes_size(requested_volumes)

    assert result == expected_result

    if "volume3" in requested_volumes:
        mock_client.containers.run.assert_called_once_with(
            image="alpine",
            command=[
                "sh",
                "-c",
                "du -sh /mnt/volume3",
            ],
            volumes={"volume3": {"bind": "/mnt/volume3", "mode": "ro"}},
            remove=True,
            stdout=True,
            stderr=False,
        )
    else:
        mock_client.containers.run.assert_not_called()
